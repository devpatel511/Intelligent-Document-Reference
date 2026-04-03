"""Bootstrap subsystem initializers and return AppContext."""

from backend.chat_memory import ChatHistory
from config.settings import load_settings
from core.context import AppContext
from core.runtime_config import apply_runtime_clients
from db import UnifiedDatabase
from db.settings_store import SettingsStore
from inference.retrieval_cache import RetrievalCache
from jobs import JobQueue, Scheduler
from watcher import FileRegistry, FileTrackingService


def bootstrap() -> AppContext:
    """Build and return a fully wired AppContext."""
    settings = load_settings()
    ctx = AppContext(settings=settings)

    ctx.settings_store = SettingsStore(db_path=settings.unified_db_path)
    apply_runtime_clients(ctx)

    vector_dimension = int(
        (ctx.runtime_preferences or {}).get(
            "embedding_dimension", settings.embedding_dimension
        )
    )
    ctx.db = UnifiedDatabase(
        db_path=settings.unified_db_path,
        vector_dimension=vector_dimension,
    )

    # Initialize retrieval cache and chat history
    ctx.retrieval_cache = RetrievalCache(
        db=ctx.db, max_size=100, similarity_threshold=0.1
    )
    ctx.chat_history = ChatHistory(window_size=5)

    job_queue = JobQueue(db_path=settings.unified_db_path)
    ctx.job_queue = job_queue

    ctx.scheduler = Scheduler(job_queue)
    registry = FileRegistry(db_path=settings.watcher_db_path)
    ctx.watcher = FileTrackingService(registry=registry, scheduler=ctx.scheduler)

    return ctx
