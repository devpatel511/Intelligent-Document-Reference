from typing import Literal
from .interface import VectorDBProtocol
from .sqlite_impl import SQLiteVectorDB
from .chroma_impl import ChromaVectorDB

def get_vector_db(db_type: Literal["sqlite", "chroma"], **kwargs) -> VectorDBProtocol:
    if db_type == "sqlite":
        return SQLiteVectorDB(**kwargs)
    elif db_type == "chroma":
        return ChromaVectorDB(**kwargs)
    else:
        raise ValueError(f"Unknown vector db type: {db_type}")
