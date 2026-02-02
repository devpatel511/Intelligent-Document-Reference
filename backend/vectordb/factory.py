from typing import Literal
from backend.vectordb.interface import VectorDBProtocol
from backend.vectordb.sqlite_impl import SQLiteVectorDB
from backend.vectordb.chroma_impl import ChromaVectorDB


def get_vector_db(db_type: Literal["sqlite", "chroma"], **kwargs) -> VectorDBProtocol:
    if db_type == "sqlite":
        return SQLiteVectorDB(**kwargs)
    elif db_type == "chroma":
        return ChromaVectorDB(**kwargs)
    else:
        raise ValueError(f"Unknown vector db type: {db_type}")
