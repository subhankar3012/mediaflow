import asyncio
from abc import ABC, abstractmethod
from typing import Optional

class BaseJobQueue(ABC):
    """Abstract interface for job queuing."""

    @abstractmethod
    async def enqueue(self, job_id: str) -> None:
        pass

    @abstractmethod
    async def dequeue(self) -> str:
        pass

    @abstractmethod
    def qsize(self) -> int:
        pass

class AsyncIOJobQueue(BaseJobQueue):
    """
    In-memory async job queue for local and MVP deployments.
    Decoupled to allow a Redis/Celery/ARQ queue to be plugged in later.
    """

    def __init__(self, maxsize: int = 100):
        self._queue: asyncio.Queue[str] = asyncio.Queue(maxsize=maxsize)

    async def enqueue(self, job_id: str) -> None:
        await self._queue.put(job_id)

    async def dequeue(self) -> str:
        return await self._queue.get()

    def task_done(self) -> None:
        self._queue.task_done()

    def qsize(self) -> int:
        return self._queue.qsize()

job_queue = AsyncIOJobQueue()
