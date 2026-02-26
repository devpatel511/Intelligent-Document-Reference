"""Embedding adapter: batch embed texts using configurable backends."""

from typing import Any, Callable, List, Optional, Protocol


class EmbeddingClient(Protocol):
    """Protocol for embedding clients."""

    def embed_text(self, texts: List[str]) -> List[List[float]]:
        ...


def _get_voyage_client() -> Optional[EmbeddingClient]:
    """Lazy import Voyage client if available."""
    try:
        from model_clients.voyage_client import VoyageEmbeddingClient
        import os
        key = os.getenv("VOYAGE_API_KEY")
        if key:
            return VoyageEmbeddingClient(api_key=key)
    except Exception:
        pass
    return None


def _get_ollama_client() -> Optional[EmbeddingClient]:
    """Lazy import Ollama client if available."""
    try:
        from model_clients.ollama_client import OllamaClient
        from config.settings import load_settings
        s = load_settings()
        return OllamaClient(url=s.ollama_url)
    except Exception:
        pass
    return None


def embed_texts_batched(
    texts: List[str],
    *,
    client: Optional[EmbeddingClient] = None,
    batch_size: int = 32,
    dimension: Optional[int] = None,
) -> List[List[float]]:
    """Embed texts in batches. Uses provided client or auto-detects.

    Args:
        texts: Texts to embed.
        client: Optional embedding client. If None, tries Voyage then Ollama.
        batch_size: Max texts per API call.
        dimension: Expected dimension (for validation). Not enforced if None.

    Returns:
        List of embedding vectors.

    Raises:
        RuntimeError: If no embedding client available and texts non-empty.
    """
    if not texts:
        return []

    if client is None:
        client = _get_voyage_client() or _get_ollama_client()
    if client is None:
        raise RuntimeError(
            "No embedding client available. Set VOYAGE_API_KEY or configure Ollama. "
            "Alternatively, pass a custom client."
        )

    result: List[List[float]] = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        emb = client.embed_text(batch)
        result.extend(emb)
    return result


def get_local_embedder() -> Optional[Callable[[List[str]], List[List[float]]]]:
    """Return a local embedder if sentence-transformers is available.

    Use for fully offline operation. Returns None if not installed.
    """
    try:
        from sentence_transformers import SentenceTransformer
        _model = None

        def _embed(texts: List[str]) -> List[List[float]]:
            nonlocal _model
            if _model is None:
                _model = SentenceTransformer("all-MiniLM-L6-v2")  # 384 dims
            return _model.encode(texts, convert_to_numpy=True).tolist()

        return _embed
    except ImportError:
        return None
