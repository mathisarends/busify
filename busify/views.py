import asyncio
from typing import Generic, TypeVar
from dataclasses import dataclass, field


import time
from uuid import uuid4

ResultT = TypeVar("ResultT")


@dataclass(kw_only=True, frozen=True)
class BaseEvent(Generic[ResultT]):
    """
    Base event class for all events.
    Events can optionally have a result of type ResultT.
    """

    id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: float = field(default_factory=time.time)
    _result: ResultT | None = field(init=False, default=None, repr=False, compare=False)
    _completed: bool = field(init=False, default=False, repr=False, compare=False)

    _exception: Exception | None = field(
        init=False, default=None, repr=False, compare=False
    )

    @property
    def is_completed(self) -> bool:
        return self._completed

    @property
    def has_error(self) -> bool:
        return self._exception is not None
    
    def __await__(self):
        async def _wait():
            while not self._completed:
                await asyncio.sleep(0.01)
            return self.get_result(raise_if_exception=True)
        
        return _wait().__await__()

    def set_result(self, value: ResultT) -> None:
        """Sets the result, bypassing the frozen state."""
        if self._completed:
            raise RuntimeError("Event already completed")

        object.__setattr__(self, "_result", value)
        object.__setattr__(self, "_completed", True)

    def get_result(
        self, raise_if_none: bool = False, raise_if_exception: bool = True
    ) -> ResultT | None:
        """
        Retrieves the result.

        Args:
            raise_if_none: If True, raises ValueError if the event is not completed yet.
            raise_if_exception: If True, raises the stored exception if one exists.
        """
        if raise_if_exception and self._exception is not None:
            raise self._exception

        if raise_if_none and not self._completed:
            raise ValueError(f"Event {self.__class__.__name__} has not completed yet")

        return self._result

    def set_exception(self, exc: Exception) -> None:
        if self._completed:
            return

        object.__setattr__(self, "_exception", exc)
        object.__setattr__(self, "_completed", True)
