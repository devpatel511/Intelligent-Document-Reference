import chromadb
from typing import List, Dict, Any
from .interface import VectorDBProtocol
import shutil
import os

class ChromaVectorDB(VectorDBProtocol):
    def __init__(self, persist_path: str = "./chroma_db", collection_name: str = "docs"):
        self.persist_path = persist_path
        self.collection_name = collection_name
        self.client = None
        self.collection = None

    def initialize(self):
        # Initialize persistent client
        self.client = chromadb.PersistentClient(path=self.persist_path)
        self.collection = self.client.get_or_create_collection(name=self.collection_name)

    def add_chunks(self, 
                   embeddings: List[List[float]], 
                   metadata: List[Dict[str, Any]], 
                   ids: List[str]) -> bool:
        if not self.collection:
            self.initialize()
            
        try:
            self.collection.add(
                embeddings=embeddings,
                metadatas=metadata,
                ids=ids
            )
            return True
        except Exception as e:
            print(f"Chroma Error: {e}")
            return False

    def search(self, 
               query_vector: List[float], 
               limit: int = 5) -> List[Dict[str, Any]]:
        if not self.collection:
            self.initialize()
            
        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=limit
        )
        
        # Unpack Chroma structure
        # results is a dict of lists: {'ids': [['id1', ...]], 'distances': [[0.1, ...]], 'metadatas': [[...]]}
        parsed_results = []
        if results['ids']:
            ids = results['ids'][0]
            distances = results['distances'][0] if 'distances' in results else [0]*len(ids)
            metas = results['metadatas'][0] if 'metadatas' in results else [{}]*len(ids)
            
            for i, uid in enumerate(ids):
                # Chroma returns distance, we might want similarity or raw distance
                # Just passing generic score
                score = 1.0 - distances[i] # approx
                parsed_results.append({
                    "id": uid,
                    "score": score,
                    "metadata": metas[i]
                })
                
        return parsed_results

    def delete(self, ids: List[str]) -> bool:
        if not self.collection:
            self.initialize()
        try:
            self.collection.delete(ids=ids)
            return True
        except:
            return False

    def close(self):
        # Chroma client doesn't really have a close(), checks persist automatically
        pass
