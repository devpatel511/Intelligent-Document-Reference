"""Google embeddings client stub."""

from model_clients.base import EmbeddingClient


class GoogleEmbeddingClient(EmbeddingClient):
    def __init__(self, api_key: str):
        self.api_key = api_key

    def embed_text(self, texts):
        raise NotImplementedError
