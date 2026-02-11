import asyncio
from typing import Callable


class CancellationError(Exception):
    pass


class CancellationManager:
    def __init__(self):
        self._cancelled: dict[str, bool] = {}
        self._check_interval = 0.1

    def register(self, request_id: str) -> None:
        self._cancelled[request_id] = False

    def cancel(self, request_id: str) -> bool:
        if request_id in self._cancelled:
            self._cancelled[request_id] = True
            return True
        return False

    def is_cancelled(self, request_id: str) -> bool:
        return self._cancelled.get(request_id, False)

    def unregister(self, request_id: str) -> None:
        self._cancelled.pop(request_id, None)

    async def check_cancellation(self, request_id: str) -> None:
        if self.is_cancelled(request_id):
            raise CancellationError(f"Request {request_id} was cancelled")

    async def run_with_cancellation[T](
        self,
        request_id: str,
        coro: Callable[[], T],
    ) -> T:
        while True:
            await self.check_cancellation(request_id)
            try:
                return await asyncio.wait_for(
                    asyncio.create_task(asyncio.coroutine(lambda: coro)()),
                    timeout=self._check_interval,
                )
            except asyncio.TimeoutError:
                continue


cancellation_manager = CancellationManager()
