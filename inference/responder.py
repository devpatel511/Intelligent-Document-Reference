"""High-level responder used by backend chat endpoints."""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from inference.retriever import Retriever
from inference.rag import RAGProcessor
from inference.citation import format_citations

logger = logging.getLogger(__name__)


class Responder:
    """Orchestrates retrieval and generation for a user query."""

    def __init__(self, db, embedding_client, inference_client):
        self.retriever = Retriever(db=db, embedding_client=embedding_client)
        self.rag = RAGProcessor(inference_client=inference_client)

    async def respond(self, query: str, *, top_k: int = 5,
                      folder_id: Optional[int] = None) -> Dict[str, Any]:
        """Run the full retrieve-then-generate pipeline.

        Args:
            query: The user's natural-language question.
            top_k: Number of chunks to retrieve.
            folder_id: Optional file-level filter.

        Returns:
            Dict with keys: answer, citations, chunks.
        """
        logger.info("Retrieving top-%d chunks for query: %s", top_k, query[:80])
        chunks = await self.retriever.retrieve(query, top_k=top_k, folder_id=folder_id)

        if not chunks:
            return {
                "answer": "I couldn't find any relevant documents to answer your question.",
                "citations": [],
                "chunks": [],
            }

        logger.info("Retrieved %d chunks, generating response", len(chunks))
        answer = await self.rag.generate_response(query, chunks)
        citations = format_citations(chunks)

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
    )
    return await responder.respond(query, **kwargs)
