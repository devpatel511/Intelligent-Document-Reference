from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class VectorDBProtocol(ABC):
    """
    Abstract Interface for Vector Database implementations.
    This allows us to swap between sqlite-vec, ChromaDB, or others without
    changing the core application logic.
    """

    @abstractmethod
    def initialize(self):
        """Perform any setup, table creation, or connection establishment."""
        pass

    @abstractmethod
    def add_chunks(self, 
                   embeddings: List[List[float]], 
                   metadata: List[Dict[str, Any]], 
                   ids: List[str]) -> bool:
        """
        Add vectors to the index.
        
        Args:
            embeddings: List of float vectors.
            metadata: List of dicts containing link back to relational DB (e.g. {'chunk_id': 1}).
            ids: List of unique string identifiers for the vectors.
        """
        pass

    @abstractmethod
    def search(self, 
               query_vector: List[float], 
               limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for nearest neighbors.

        Returns:
            List of results, where each result contains:
            {'id': str, 'score': float, 'metadata': dict}
        """
        pass

    @abstractmethod
    def delete(self, ids: List[str]) -> bool:
        """Delete vectors by ID."""
        pass

    @abstractmethod
    def close(self):
        """Cleanup resources."""
        pass
