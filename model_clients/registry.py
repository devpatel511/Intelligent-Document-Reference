"""Client registry / factory.

Resolves embedding and inference clients based on the configured backend.
Backend values: "local" (Ollama), "api" (OpenAI), "gemini" (Google Gemini), "voyage" (Voyage AI).
"""

import logging
from typing import List

import httpx

from config.settings import load_settings
from model_clients.google_client import GoogleEmbeddingClient, GoogleInferenceClient
from model_clients.ollama_client import OllamaClient
from model_clients.openai_client import OpenAIEmbeddingClient, OpenAIInferenceClient
from model_clients.voyage_client import VoyageEmbeddingClient

logger = logging.getLogger(__name__)


class ClientRegistry:
    @staticmethod
    def get_client(
        kind: str,
        backend: str,
        *,
        model: str | None = None,
        embedding_dimension: int | None = None,
        url: str | None = None,
        api_key: str | None = None,
    ):
        """Return an embedding or inference client for the given backend.

        Args:
            kind: "embedding" or "inference".
            backend: "local", "api", "gemini", or "voyage".
        """
        settings = load_settings()

        if backend == "local":
            if kind == "embedding":
                resolved_model = model
                if not resolved_model:
                    candidates = ClientRegistry.list_models(
                        "embedding", "local", url=url
                    )
                    # Prefer names that look like embedding models, otherwise fall back
                    resolved_model = next(
                        (n for n in candidates if "embed" in n.lower()), None
                    )
                    resolved_model = resolved_model or (
                        candidates[0] if candidates else "nomic-embed-text"
                    )
                return OllamaClient(
                    url=url or settings.ollama_url,
                    embed_model=resolved_model,
                )
            if kind == "inference":
                resolved_model = model
                if not resolved_model:
                    candidates = ClientRegistry.list_models(
                        "inference", "local", url=url
                    )
                    resolved_model = candidates[0] if candidates else "llama3"
                return OllamaClient(
                    url=url or settings.ollama_url,
                    chat_model=resolved_model,
                )
            raise ValueError(f"Unknown client kind '{kind}' for local backend")

        if backend == "api":
            resolved_api_key = api_key or settings.openai_api_key
            if kind == "embedding":
                resolved_model = model
                if not resolved_model:
                    candidates = ClientRegistry.list_models(
                        "embedding", "api", api_key=resolved_api_key
                    )
                    # pick first embedding-like model
                    resolved_model = next(
                        (
                            n
                            for n in candidates
                            if "embed" in n.lower() or "embedding" in n.lower()
                        ),
                        None,
                    )
                    resolved_model = resolved_model or (
                        candidates[0] if candidates else "text-embedding-3-small"
                    )
                return OpenAIEmbeddingClient(
                    api_key=resolved_api_key or None,
                    model=resolved_model,
                    dimensions=embedding_dimension,
                )
            if kind == "inference":
                resolved_model = model
                if not resolved_model:
                    candidates = ClientRegistry.list_models(
                        "inference", "api", api_key=resolved_api_key
                    )
                    resolved_model = candidates[0] if candidates else "gpt-4o"
                return OpenAIInferenceClient(
                    api_key=resolved_api_key or None,
                    model=resolved_model,
                )
            raise ValueError(f"Unknown client kind '{kind}' for api backend")

        if backend == "gemini":
            resolved_api_key = api_key or settings.gemini_api_key
            if kind == "embedding":
                dim = (
                    embedding_dimension
                    if embedding_dimension and embedding_dimension > 0
                    else 3072
                )
                resolved_model = model
                if not resolved_model:
                    candidates = ClientRegistry.list_models(
                        "embedding", "gemini", api_key=resolved_api_key
                    )
                    resolved_model = next(
                        (
                            n
                            for n in candidates
                            if "embed" in n.lower() or "embedding" in n.lower()
                        ),
                        None,
                    )
                    resolved_model = resolved_model or (
                        candidates[0] if candidates else "models/gemini-embedding-001"
                    )
                return GoogleEmbeddingClient(
                    api_key=resolved_api_key or None,
                    model=resolved_model,
                    output_dimensionality=dim,
                )
            if kind == "inference":
                resolved_model = model
                if not resolved_model:
                    candidates = ClientRegistry.list_models(
                        "inference", "gemini", api_key=resolved_api_key
                    )
                    resolved_model = (
                        candidates[0] if candidates else "gemini-2.5-flash-lite"
                    )
                return GoogleInferenceClient(
                    api_key=resolved_api_key or None,
                    model=resolved_model,
                )
            raise ValueError(f"Unknown client kind '{kind}' for gemini backend")

        if backend == "voyage":
            if kind == "embedding":
                return VoyageEmbeddingClient(
                    api_key=api_key or settings.voyage_api_key or None,
                    model=model or "voyage-multimodal-3.5",
                )
            raise ValueError(f"Voyage backend only supports embedding, not {kind}")

        raise ValueError(
            f"Unknown backend '{backend}'. Use 'local', 'api', 'gemini', or 'voyage'."
        )

    @staticmethod
    def list_models(
        kind: str, backend: str, *, api_key: str | None = None, url: str | None = None
    ) -> List[str]:
        """Return a best-effort list of available model names for the given backend.

        This tries provider-specific endpoints and falls back to the defaults used by
        the registry when listing isn't supported.
        """
        settings = load_settings()
        names: List[str] = []

        try:
            if backend == "local":
                base = (url or settings.ollama_url or "http://localhost:11434").rstrip(
                    "/"
                )
                try:
                    # Newer Ollama exposes /api/tags with installed models
                    resp = httpx.get(f"{base}/api/tags", timeout=5.0)
                    resp.raise_for_status()
                    payload = resp.json()
                    models = (
                        payload.get("models", []) if isinstance(payload, dict) else []
                    )
                    for item in models:
                        if isinstance(item, dict):
                            nm = str(item.get("name", "")).strip()
                            if nm:
                                names.append(nm)
                    if names:
                        return names
                except Exception:
                    # Try /api/models as a fallback
                    try:
                        resp = httpx.get(f"{base}/api/models", timeout=5.0)
                        resp.raise_for_status()
                        payload = resp.json()
                        models = (
                            payload.get("models", [])
                            if isinstance(payload, dict)
                            else []
                        )
                        for item in models:
                            if isinstance(item, dict):
                                nm = str(item.get("name", "")).strip()
                                if nm:
                                    names.append(nm)
                        if names:
                            return names
                    except Exception:
                        pass

                # Fallback to configured/default inference model
                return [
                    url and settings and settings.ollama_url and "llama3" or "llama3"
                ]

            if backend == "api":
                resolved_api_key = api_key or settings.openai_api_key
                if not resolved_api_key:
                    return ["gpt-4o"]
                try:
                    # Prefer OpenAI SDK if installed
                    try:
                        from openai import OpenAI

                        client = OpenAI(api_key=resolved_api_key)
                        resp = getattr(client.models, "list")()
                        data = getattr(resp, "data", resp)
                        for item in data:
                            if hasattr(item, "id"):
                                names.append(str(item.id))
                            elif isinstance(item, dict) and item.get("id"):
                                names.append(str(item.get("id")))
                        if names:
                            return names
                    except Exception:
                        # Try the public REST endpoint as a last resort
                        hdr = {"Authorization": f"Bearer {resolved_api_key}"}
                        resp = httpx.get(
                            "https://api.openai.com/v1/models", headers=hdr, timeout=5.0
                        )
                        resp.raise_for_status()
                        payload = resp.json()
                        data = payload.get("data", [])
                        for item in data:
                            if isinstance(item, dict) and item.get("id"):
                                names.append(str(item.get("id")))
                        if names:
                            return names
                except Exception:
                    pass
                return ["gpt-4o"]

            if backend == "gemini":
                resolved_api_key = api_key or settings.gemini_api_key
                if not resolved_api_key:
                    return ["gemini-2.5-flash-lite"]
                try:
                    try:
                        from google import genai

                        client = genai.Client(api_key=resolved_api_key)
                        # SDKs differ; try common variants
                        if hasattr(client.models, "list"):
                            resp = client.models.list()
                            items = getattr(resp, "models", getattr(resp, "data", resp))
                            for m in items:
                                if hasattr(m, "name"):
                                    names.append(str(m.name))
                                elif isinstance(m, dict) and m.get("name"):
                                    names.append(str(m.get("name")))
                            if names:
                                return names
                    except Exception:
                        logger.debug(
                            "Gemini model list discovery failed or SDK not available; falling back to default inference model",
                            exc_info=True,
                        )
                        pass
                except Exception:
                    pass
                return ["gemini-2.5-flash-lite"]

            if backend == "voyage":
                # Voyage currently has no discover endpoint in this code; return default
                return ["voyage-multimodal-3.5"]
        except Exception:
            logger.exception("Error listing models for backend %s", backend)

        # Generic fallback depending on kind
        if kind == "inference":
            return ["llama3", "gpt-4o", "gemini-2.5-flash-lite"]
        return []
