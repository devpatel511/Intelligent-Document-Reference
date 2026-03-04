"""Retrieval wrapper for top-k vector search."""

import asyncio
from typing import Any, Dict, List, Optional

from db.unified import UnifiedDatabase


class Retriever:
    def __init__(self, db: UnifiedDatabase, embedding_client: Any):
        self.db = db
        self.embedder = embedding_client

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        folder_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Embed the query and perform a vector similarity search.

        Args:
            query: Natural-language question from the user.
            top_k: How many chunks to return.
            folder_id: Optional file-level filter (maps to file_id in DB).

        Returns:
            List of chunk dicts with text_content, file_path, distance.
        """
        # embed_text is synchronous in all current clients
        query_vec = await asyncio.to_thread(self.embedder.embed_text, [query])

        results = await asyncio.to_thread(
            self.db.search_with_metadata,
            query_vec[0],
            limit=top_k,
            file_id=folder_id,
        )
        return results