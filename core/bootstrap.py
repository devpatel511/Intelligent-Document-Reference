"""Bootstrap subsystem initializers and return AppContext."""

from config.settings import load_settings
from db.unified import UnifiedDatabase
from jobs.queue import JobQueue
from jobs.scheduler import Scheduler
from model_clients.registry import ClientRegistry
from watcher.core.database import FileRegistry
from watcher.service import FileTrackingService

from .context import AppContext


def bootstrap() -> AppContext:
    """Build and return a fully wired AppContext."""
    settings = load_settings()
    ctx = AppContext(settings=settings)

    ctx.embedding_client = ClientRegistry.get_client(
        "embedding", settings.default_embedding_backend
    )
    ctx.inference_client = ClientRegistry.get_client(
        "inference", settings.default_inference_backend
    )

    ctx.db = UnifiedDatabase(db_path=settings.unified_db_path)

    job_queue = JobQueue(db_path=settings.unified_db_path)
    ctx.job_queue = job_queue

    ctx.scheduler = Scheduler(job_queue)
    registry = FileRegistry(db_path=settings.watcher_db_path)
    ctx.watcher = FileTrackingService(registry=registry, scheduler=ctx.scheduler)

    return ctx
