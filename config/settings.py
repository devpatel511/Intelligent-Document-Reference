"""Runtime-configurable settings (stub).

TODO: load YAML / environment variables and expose a Settings object.
"""
from dataclasses import dataclass
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

@dataclass
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./data/metadata.db")
    vector_db_path: str = os.getenv("VECTOR_DB_PATH", "./data/vectorstore")
    ollama_url: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
    default_embedding_backend: str = "api"
    default_inference_backend: str = "api"
    embedding_dimension: int = int(os.getenv("EMBEDDING_DIMENSION", "1024"))

def load_settings() -> Settings:
    return Settings()

