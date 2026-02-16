"""Async worker that polls the job queue and dispatches to a processor."""

import asyncio
import logging
from typing import Callable, Optional

from core.context import AppContext
from jobs import JobQueue, transition_state

logger = logging.getLogger(__name__)

ProcessorFn = Callable[..., None]


class Worker:
    """Async loop that dequeues jobs and runs a processor function."""

    def __init__(
        self,
        queue: JobQueue,
        processor: ProcessorFn,
        ctx: Optional[AppContext] = None,
        poll_interval: float = 2.0,
    ) -> None:
        self._queue = queue
        self._processor = processor
        self._ctx = ctx
        self._poll_interval = poll_interval
        self._task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self) -> None:
        """Launch the worker loop as a background asyncio task."""
        if self._task is not None:
            logger.warning("Worker already running — ignoring start()")
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())
        logger.info("Job worker started (poll_interval=%.1fs)", self._poll_interval)

    async def stop(self) -> None:
        """Cancel the worker task and wait for it to finish."""
        self._running = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("Job worker stopped")

    async def _loop(self) -> None:
        """Poll the queue and process jobs until stopped."""
        while self._running:
            try:
                job = await asyncio.to_thread(self._queue.dequeue)
                if job is None:
                    await asyncio.sleep(self._poll_interval)
                    continue

                logger.info(
                    "Processing job %d: %s (attempt %d/%d)",
                    job.id,
                    job.file_path,
                    job.attempts,
                    job.max_attempts,
                )

                try:
                    await asyncio.to_thread(self._processor, job.file_path, self._ctx)
                    await asyncio.to_thread(
                        transition_state, self._queue, job.id, "completed"
                    )
                    logger.info("Job %d completed", job.id)
                except Exception as exc:
                    error_msg = f"{type(exc).__name__}: {exc}"
                    updated = await asyncio.to_thread(
                        transition_state,
                        self._queue,
                        job.id,
                        "failed",
                        error_msg,
                    )
                    if updated.status == "queued":
                        logger.warning(
                            "Job %d failed (will retry): %s", job.id, error_msg
                        )
                    else:
                        logger.error("Job %d permanently failed: %s", job.id, error_msg)

            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Unexpected error in worker loop")
                await asyncio.sleep(self._poll_interval)
