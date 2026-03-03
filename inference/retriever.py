"""Retrieval wrapper (stub) for top-k vector search."""


class Retriever:
    def __init__(self, db, embedding_client):
        self.db = db
        self.embedding_client = embedding_client

    async def retrieve(self, query: str, top_k: int = 5, folder_id: int = None):
        # 1. Embed Query 
        query_vec = await self.embedding_client.embed_text([query])
        
        # 2. Similarity Search 
        chunks = self.db.search_with_metadata(query_vec[0], limit=top_k, file_id=folder_id)
        return chunks