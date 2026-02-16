import logging
import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

from busify.views import BaseEvent

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseEvent)
EventHandler = Callable[[T], Awaitable[None]]


class EventBus:
    def __init__(self):
        self._handlers: dict[type[BaseEvent], list[EventHandler]] = {}
        self._wildcard_handlers: list[Callable[[BaseEvent], Awaitable[None]]] = []

    def subscribe(self, event_type: type[T], handler: EventHandler[T]) -> None:
        self._handlers.setdefault(event_type, []).append(handler)
        logger.debug(f"Subscribed to {event_type.__name__}")

    def unsubscribe(self, event_type: type[T], handler: EventHandler[T]) -> None:
        if event_type in self._handlers:
            if handler in self._handlers[event_type]:
                self._handlers[event_type].remove(handler)

    def unsubscribe_all(self, event_type: type[T] | None = None) -> None:
        if event_type is None:
            self._handlers.clear()
            self._wildcard_handlers.clear()
        elif event_type in self._handlers:
            del self._handlers[event_type]

    async def dispatch(self, event: T) -> T:
        event_type = type(event)
        handlers = self._handlers.get(event_type, []) + self._wildcard_handlers

        if not handlers:
            return event

        tasks = [handler(event) for handler in handlers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                logger.error(
                    f"Handler failed for {event_type.__name__}: {result}",
                    exc_info=result,
                )
                event.set_exception(result)

        return event

    async def wait_for_event(
        self,
        event_type: type[T],
        timeout: float | None = None,
        predicate: Callable[[T], bool] | None = None,
    ) -> T:
        future: asyncio.Future[T] = asyncio.Future()
        logger.debug(f"Waiting for {event_type.__name__} (timeout={timeout}s)")

        async def handler(event: T) -> None:
            if predicate is None or predicate(event):
                if not future.done():
                    future.set_result(event)

        self.subscribe(event_type, handler)

        try:
            if timeout:
                result = await asyncio.wait_for(future, timeout=timeout)
            else:
                result = await future

            logger.debug(f"Received {event_type.__name__}")
            return result
        except asyncio.TimeoutError:
            logger.warning(
                f"Timeout waiting for {event_type.__name__} after {timeout}s"
            )
            raise
        finally:
            self.unsubscribe(event_type, handler)