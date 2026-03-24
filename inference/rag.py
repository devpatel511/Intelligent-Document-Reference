"""RAG prompt builder and orchestration."""

import asyncio
from typing import Any, Dict, List


class RAGProcessor:
    def __init__(self, inference_client: Any):
        self.client = inference_client

    def build_prompt(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        *,
        system_prompt: str | None = None,
        max_context_chars: int | None = None,
        max_chunk_chars: int | None = None,
        chat_history_context: str | None = None,
    ) -> str:
        """Build a retrieval-augmented prompt with source attributions and chat history.

        Args:
            query: User's question.
            chunks: Retrieved chunks.
            max_context_chars: Maximum total context length.
            max_chunk_chars: Maximum per-chunk length.
            chat_history_context: Optional previous conversation context.

        Returns:
            Formatted prompt string.
        """
        # Use custom system prompt if provided, otherwise use default
        system_instruction = system_prompt or (
            "You are a professional assistant. Use the context below to answer "
            "accurately and concisely.\n"
            "Return markdown only (headings, bullet lists, tables where helpful).\n"
            "Do not append source markers in the answer text.\n"
            "Do not include absolute or relative source file paths in the answer body.\n"
        )

        context_str = ""
        for c in chunks:
            chunk_text = c["text_content"]
            if max_chunk_chars is not None and max_chunk_chars > 0:
                chunk_text = chunk_text[:max_chunk_chars]

            loc_parts = [c["file_path"]]
            if c.get("page_number"):
                loc_parts.append(f"Page {c['page_number']}")
            if c.get("section"):
                loc_parts.append(c["section"])
            source_label = " | ".join(loc_parts)

            segment = f"\n[SOURCE: {source_label}]\nCONTENT: {chunk_text}\n"
            if max_context_chars is not None and max_context_chars > 0:
                remaining = max_context_chars - len(context_str)
                if remaining <= 0:
                    break
                if len(segment) > remaining:
                    context_str += segment[:remaining]
                    break
            context_str += segment

        return (
            f"{system_instruction}\n"
            f"CONTEXT:\n{context_str}\n\n"
            f"USER QUESTION: {query}\nANSWER:"
        )

        if chat_history_context:
            prompt += f"CONVERSATION HISTORY:\n{chat_history_context}\n\n"

        prompt += f"CONTEXT:\n{context_str}\n\n" f"USER QUESTION: {query}\nANSWER:"

        return prompt

    async def generate_response(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        chat_history_context: str | None = None,
        **generate_kwargs,
    ) -> str:
        """Generate an LLM response from retrieved chunks.

        Args:
            query: User's question.
            chunks: Retrieved chunks.
            chat_history_context: Optional previous conversation context.
            **generate_kwargs: Additional kwargs for the client.generate call.

        Returns:
            Generated response text.
        """
        system_prompt = generate_kwargs.pop("system_prompt", None)
        max_context_chars = generate_kwargs.pop("max_context_chars", None)
        max_chunk_chars = generate_kwargs.pop("max_chunk_chars", None)
        prompt = self.build_prompt(
            query,
            chunks,
            system_prompt=system_prompt,
            max_context_chars=max_context_chars,
            max_chunk_chars=max_chunk_chars,
            chat_history_context=chat_history_context,
        )
        return await asyncio.to_thread(self.client.generate, prompt, **generate_kwargs)
