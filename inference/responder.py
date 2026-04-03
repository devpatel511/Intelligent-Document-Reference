"""High-level responder used by backend chat endpoints."""

import logging
import re
from typing import Any, Dict, List, Optional

from inference.citation import format_citations
from inference.rag import RAGProcessor
from inference.retriever import Retriever

logger = logging.getLogger(__name__)

_SOURCE_MARKER_RE = re.compile(
    r"\s*\((?:source|citation)s?\s*:\s*[^)]+\)",
    flags=re.IGNORECASE,
)
_PATH_LINE_RE = re.compile(r"^\s*(?:/|[A-Za-z]:\\).*$", flags=re.MULTILINE)


def _strip_inline_source_markers(text: str) -> str:
    """Remove inline source markers; citations are returned separately."""
    cleaned = _SOURCE_MARKER_RE.sub("", text or "")
    cleaned = _PATH_LINE_RE.sub("", cleaned)
    # Collapse accidental extra spaces before punctuation.
    cleaned = re.sub(r"\s+([,.;:!?])", r"\1", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


class Responder:
    """Orchestrates retrieval and generation for a user query."""

    def __init__(self, db, embedding_client, inference_client, cache=None):
        self.db = db
        self.retriever = Retriever(
            db=db, embedding_client=embedding_client, cache=cache
        )
        self.rag = RAGProcessor(inference_client=inference_client)

    async def respond(
        self,
        query: str,
        *,
        top_k: int = 5,
        folder_id: Optional[int] = None,
        selected_files: Optional[List[str]] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        context_size: Optional[int] = None,
        system_prompt: Optional[str] = None,
        inference_backend: Optional[str] = None,
        chat_history_context: Optional[str] = None,
        runtime_prefs: Optional[dict] = None,
    ) -> Dict[str, Any]:
        """Run the full retrieve-then-generate pipeline.

        Args:
            query: User's question.
            top_k: Number of chunks to retrieve.
            folder_id: Optional folder filter.
            selected_files: Optional file paths to search within.
            model: Optional model override.
            temperature: Optional temperature override.
            context_size: Optional context size for local models.
            inference_backend: Optional inference backend override.
            chat_history_context: Optional chat history to include in prompt.

        Returns:
            Dict with answer, citations, and chunks.
        """
        file_ids: Optional[List[int]] = None
        if selected_files is not None:
            file_ids = self.db.get_file_ids_for_paths(selected_files)
            if not file_ids:
                file_ids = []

        logger.info("Retrieving top-%d chunks for query: %s", top_k, query[:80])
        chunks = await self.retriever.retrieve(
            query,
            top_k=top_k,
            folder_id=folder_id,
            file_ids=file_ids,
            selected_file_paths=selected_files,
        )

        if not chunks:
            return {
                "answer": "I couldn't find any relevant documents to answer your question.",
                "citations": [],
                "chunks": [],
            }

        logger.info("Retrieved %d chunks, generating response", len(chunks))
        generate_kwargs: Dict[str, Any] = {}
        if model:
            generate_kwargs["model"] = model
        if temperature is not None:
            generate_kwargs["temperature"] = temperature
        if system_prompt is not None:
            generate_kwargs["system_prompt"] = system_prompt

        if (inference_backend or "").lower() == "local":
            # Default context size; allow request override via context_size.
            requested_ctx = context_size or 4096
            # Cap requested context to the model's max context tokens when available
            model_max_ctx = None
            try:
                model_max_ctx = (
                    int(runtime_prefs.get("model_max_context_tokens"))
                    if runtime_prefs
                    else None
                )
            except Exception:
                model_max_ctx = None
            if model_max_ctx and model_max_ctx > 0:
                effective_ctx = min(requested_ctx, model_max_ctx)
            else:
                effective_ctx = requested_ctx

            # If this appears to be a Qwen3 model, tighten defaults to speed up
            # inference: smaller context, fewer chunks, and smaller output.
            try:
                effective_model = model or (
                    runtime_prefs.get("inference_model") if runtime_prefs else None
                )
                effective_model_l = (effective_model or "").lower()
                if "qwen" in effective_model_l and "3" in effective_model_l:
                    # target fast inference: smaller context and output budget
                    effective_ctx = min(effective_ctx, 2048)
                    generate_kwargs.setdefault("num_ctx", effective_ctx)
                    # Prefer a shorter output by default for Qwen3 to hit <20s
                    generate_kwargs.setdefault("num_predict", 256)
                    generate_kwargs.setdefault("max_chunk_chars", 1000)
                    generate_kwargs.setdefault("keep_alive", "10m")
                    generate_kwargs.setdefault(
                        "max_context_chars",
                        max(3000, min(effective_ctx * 2, 12000)),
                    )
                else:
                    generate_kwargs.setdefault("num_ctx", effective_ctx)
                    # Allow runtime preferences to control max output tokens for local models
                    if runtime_prefs and isinstance(
                        runtime_prefs.get("local_max_output_tokens"), int
                    ):
                        generate_kwargs.setdefault(
                            "num_predict",
                            int(runtime_prefs.get("local_max_output_tokens")),
                        )
                    else:
                        generate_kwargs.setdefault("num_predict", 384)
                    generate_kwargs.setdefault("keep_alive", "30m")
                    generate_kwargs.setdefault(
                        "max_context_chars",
                        max(6000, min(effective_ctx * 3, 24000)),
                    )
                    generate_kwargs.setdefault("max_chunk_chars", 1800)
            except Exception:
                # Fallback to sane defaults on any error
                generate_kwargs.setdefault("num_ctx", effective_ctx)
                generate_kwargs.setdefault("num_predict", 384)
                generate_kwargs.setdefault("keep_alive", "30m")
                generate_kwargs.setdefault(
                    "max_context_chars",
                    max(6000, min(effective_ctx * 3, 24000)),
                )
                generate_kwargs.setdefault("max_chunk_chars", 1800)

        # Generate raw output from the client (may contain inline source markers).
        raw_answer = await self.rag.generate_response(
            query, chunks, chat_history_context=chat_history_context, **generate_kwargs
        )
        # Strip inline markers for the displayed answer.
        answer = _strip_inline_source_markers(raw_answer)

        # If stripping removed all content, but the raw answer had something, fall back to raw.
        if not answer and raw_answer:
            logger.debug("Stripped answer empty; falling back to raw model output")
            answer = raw_answer.strip()

        # If still short/empty, optionally retry with increased tokens/adjusted temp.
        if (inference_backend or "").lower() == "local":
            tries = 0
            max_retries = 0
            min_chars = 0
            if runtime_prefs:
                max_retries = int(runtime_prefs.get("local_retry_attempts", 0))
                min_chars = int(runtime_prefs.get("local_min_answer_chars", 200))

            current_num_predict = int(generate_kwargs.get("num_predict", 384))
            current_temp = float(generate_kwargs.get("temperature", 0.7))

            while (not answer or len(answer) < min_chars) and tries < max_retries:
                tries += 1
                # Increase requested tokens by 2x each retry (capped reasonably)
                current_num_predict = min(current_num_predict * 2, 65536)
                # Slightly reduce temperature to make output more deterministic on retry
                current_temp = max(0.0, current_temp * 0.8)
                logger.info(
                    "Retrying local generation (try %d/%d): num_predict=%d, temperature=%.2f",
                    tries,
                    max_retries,
                    current_num_predict,
                    current_temp,
                )

                retry_kwargs = dict(generate_kwargs)
                retry_kwargs["num_predict"] = current_num_predict
                retry_kwargs["temperature"] = current_temp

                raw_answer = await self.rag.generate_response(
                    query, chunks, **retry_kwargs
                )
                stripped = _strip_inline_source_markers(raw_answer)
                if stripped:
                    answer = stripped
                    break
                if raw_answer:
                    answer = raw_answer.strip()
                    break

            # If still empty after retries, provide a deterministic fallback so frontend doesn't show blank.
            if not answer:
                logger.warning(
                    "Model returned empty output for query after retries: %s",
                    query[:120],
                )
                answer = (
                    "The local model did not produce any text for this input after several attempts. "
                    "Try a different model, increase local resources, or shorten the prompt/context."
                )
        citations = format_citations(chunks, max_items=3, query=query)

        return {
            "answer": answer,
            "citations": citations,
            "chunks": chunks,
        }


async def respond(query: str, ctx=None, **kwargs) -> Dict[str, Any]:
    """Convenience function that builds a Responder from AppContext and runs it."""
    if ctx is None:
        raise ValueError("AppContext is required")
    responder = Responder(
        db=ctx.db,
        embedding_client=ctx.embedding_client,
        inference_client=ctx.inference_client,
        cache=ctx.retrieval_cache if ctx else None,
    )
    return await responder.respond(query, **kwargs)
