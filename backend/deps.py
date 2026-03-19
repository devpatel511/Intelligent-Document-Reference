"""FastAPI dependency helpers.

Provides a singleton AppContext that is initialized once at import time
via ``bootstrap()`` and shared across all request handlers.
"""

from backend.chat_memory import ChatHistory
from core.bootstrap import bootstrap
from core.context import AppContext
from inference.retrieval_cache import RetrievalCache

_ctx: AppContext = bootstrap()


def get_context() -> AppContext:
    """Return the application-wide AppContext singleton.

    Returns:
        The bootstrapped AppContext instance.
    """
    return _ctx


def get_chat_history() -> ChatHistory:
    """Return the chat history instance from AppContext.

    Returns:
        The ChatHistory instance.
    """
    return _ctx.chat_history


def get_retrieval_cache() -> RetrievalCache:
    """Return the retrieval cache instance from AppContext.

    Returns:
        The RetrievalCache instance.
    """
    return _ctx.retrieval_cache
