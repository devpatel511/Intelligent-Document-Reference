"""Client registry / factory.

TODO: wire correct auth and model selection from config/models.yaml
"""
from config.settings import load_settings
from .openai_client import OpenAIEmbeddingClient, OpenAIInferenceClient
from .google_client import GoogleEmbeddingClient
from .ollama_client import OllamaClient
from .voyage_client import VoyageEmbeddingClient

class ClientRegistry:
    @staticmethod
    def get_client(kind: str, backend: str):
        settings = load_settings()
        if backend == "local":
            return OllamaClient(settings.ollama_url)
        if backend == "api":
            if kind == "embedding":
                return GoogleEmbeddingClient(api_key=settings.ollama_url)  # TODO: replace with actual key
            if kind == "inference":
                return OpenAIInferenceClient(api_key=settings.ollama_url)  # TODO: replace
        if backend == "voyage":
            if kind == "embedding":
                return VoyageEmbeddingClient(api_key=getattr(settings, 'voyage_api_key', None))
            raise ValueError(f"Voyage backend only supports embedding, not {kind}")
        raise ValueError("Unknown client requested")

