"""OpenAI client stub."""
from .base import EmbeddingClient, InferenceClient

class OpenAIEmbeddingClient(EmbeddingClient):
    def __init__(self, api_key: str):
        self.api_key = api_key

    def embed_text(self, texts):
        raise NotImplementedError

class OpenAIInferenceClient(InferenceClient):
    def __init__(self, api_key: str):
        self.api_key = api_key

    def generate(self, prompt: str, **kwargs):
        raise NotImplementedError

