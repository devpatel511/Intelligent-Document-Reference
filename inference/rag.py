"""RAG prompt builder and orchestration (stub)."""
from typing import Any, Dict, List


class RAGProcessor:
    def __init__(self, inference_client: Any):
        self.client = inference_client

    def build_prompt(self, query: str, chunks: List[Dict[str, Any]]) -> str:
        # Structured formatting ensures the LLM can distinguish between 
        # different sources for citations 
        context_str = ""
        for c in chunks:
            context_str += f"\n[SOURCE: {c['file_path']}]\nCONTENT: {c['text_content']}\n"
            
        return f"""You are a professional assistant. Use the context below to answer accurately.
        Every claim MUST cite its source path in brackets, e.g., (Source: /docs/notes.pdf).
        
        CONTEXT:
        {context_str}
        
        USER QUESTION: {query}
        ANSWER:"""

    async def generate_response(self, query: str, 
                                chunks: List[Dict[str, Any]]) -> str:
        prompt = self.build_prompt(query, chunks)
        # Final inference step to synthesize the answer with citations
        return await self.client.generate(prompt)