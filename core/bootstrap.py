"""Bootstrap subsystem initializers and return AppContext (stub).

TODO: initialize DB, vectorstore, job queue, model clients via model_clients.registry.
"""
from config.settings import load_settings
from .context import AppContext
from model_clients.registry import ClientRegistry

def bootstrap() -> AppContext:
    settings = load_settings()
    ctx = AppContext(settings=settings)
    # TODO: initialize and assign real clients here
    ctx.embedding_client = ClientRegistry.get_client("embedding", settings.default_embedding_backend)
    ctx.inference_client = ClientRegistry.get_client("inference", settings.default_inference_backend)
    return ctx

