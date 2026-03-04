"""Google Gemini client for embeddings and inference via AI Studio."""

import logging
import os
from typing import List, Optional

from dotenv import load_dotenv

from model_clients.base import EmbeddingClient, InferenceClient

load_dotenv()
logger = logging.getLogger(__name__)

try:
    from google import genai
except ImportError:
    genai = None


class GoogleEmbeddingClient(EmbeddingClient):
    """Embedding client using Google's text-embedding model via genai SDK."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "models/gemini-embedding-001",
    ):
        if genai is None:
            raise ImportError(
                "google-genai package is required. Install with: pip install google-genai"
            )
        self.api_key = (
            api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        )
        if not self.api_key:
            raise ValueError(
                "Google API key is required. Set GEMINI_API_KEY in .env or pass api_key."
            )
        self.client = genai.Client(api_key=self.api_key)
        self.model = model

    def embed_text(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of texts using the Gemini embedding model.

        Args:
            texts: Strings to embed.

        Returns:
            List of float vectors, one per input text.
        """
        if not texts:
            return []

        result = self.client.models.embed_content(
            model=self.model,
            contents=texts,
        )
        return [e.values for e in result.embeddings]


class GoogleInferenceClient(InferenceClient):
    """Inference client using Google Gemini generative models."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-2.5-flash-lite",
    ):
        if genai is None:
            raise ImportError(
                "google-genai package is required. Install with: pip install google-genai"
            )
        self.api_key = (
            api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        )
        if not self.api_key:
            raise ValueError(
                "Google API key is required. Set GEMINI_API_KEY in .env or pass api_key."
            )
        self.client = genai.Client(api_key=self.api_key)
        self.model = model

    def generate(self, prompt: str, **kwargs) -> str:
        """Generate a text response from the Gemini model.

        Args:
            prompt: The full prompt string.
            **kwargs: Extra params (temperature, etc.).

        Returns:
            The generated text.
        """
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
        )
        return response.text
