"""Ollama (local) client stub supporting embeddings and inference."""

from model_clients.base import EmbeddingClient, InferenceClient


class OllamaClient(EmbeddingClient, InferenceClient):
    def __init__(self, url: str):
        self.url = url

    def embed_text(self, texts):
        raise NotImplementedError

    def generate(self, prompt: str, **kwargs):
        raise NotImplementedError
