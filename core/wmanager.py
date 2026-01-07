from __future__ import annotations
import logging
import asyncio
import itertools
from typing import Any, Awaitable, Callable, Coroutine, Dict, NamedTuple

AsyncFunc = Callable[..., Coroutine[Any, Any, Any]]


class TaskHandle(NamedTuple):
    id: int
    task: asyncio.Task
    meta: dict[str, Any]


class TaskManager:
    def __init__(self, max_parallel: int = 100) -> None:
        self._queue: asyncio.Queue[TaskHandle] = asyncio.Queue()
        self._slot_sem = asyncio.Semaphore(max_parallel)
        self._running: Dict[int, TaskHandle] = {}
        self._id_gen = itertools.count(1)
        self._workers = [
            asyncio.create_task(self._worker(), name=f"tm‑worker‑{i}")
            for i in range(max_parallel)
        ]

    async def enqueue(self, func: AsyncFunc, *args: Any, **kwargs: Any) -> int:
        job_id = next(self._id_gen)
        coro = func(*args, job_id, **kwargs)
        task = asyncio.create_task(coro, name=f"tm‑job‑{job_id}")
        handle = TaskHandle(job_id, task, {"name": func.__name__})
        self._running[job_id] = handle
        await self._queue.put(handle)
        logging.info(f'{job_id}:Task added')
        return job_id

    def cancel(self, job_id: int) -> bool:
        handle = self._running.pop(job_id, None)
        if not handle:
            return False
        handle.task.cancel("Cancelled by user")
        logging.info(f'{job_id}:Task Cancelled')
        return True

    def status(self, job_id: int) -> str:
        handle = self._running.get(job_id)
        if not handle:
            return "unknown"

        t = handle.task
        if t.cancelled():
            return "cancelled"
        if t.done():
            return "error" if t.exception() else "done"
        return "queued" if handle in self._queue._queue else "running"

    async def wait_all_done(self) -> None:
        await self._queue.join()
        await asyncio.gather(*self._workers, return_exceptions=True)


    async def _worker(self) -> None:
        while True:
            handle = await self._queue.get()
            async with self._slot_sem:
                try:
                    logging.info(f'{handle.id} is preparing')
                    await handle.task
                    logging.info(f'{handle.id} is done')
                except asyncio.CancelledError:
                    pass 
                finally:
                    self._running.pop(handle.id, None)
                    self._queue.task_done()
