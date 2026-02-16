import pytest
from dataclasses import dataclass
from busify import BaseEvent


@dataclass(kw_only=True, frozen=True)
class TestEvent(BaseEvent[str]):
    data: str


@dataclass(kw_only=True, frozen=True)
class NoResultEvent(BaseEvent[None]):
    value: int


def test_event_creation():
    event = TestEvent(data="test")
    assert event.data == "test"
    assert event.id is not None
    assert event.timestamp > 0
    assert not event.is_completed
    assert not event.has_error


def test_set_and_get_result():
    event = TestEvent(data="test")
    event.set_result("result")
    
    assert event.is_completed
    assert event.get_result() == "result"


def test_set_result_twice_raises():
    event = TestEvent(data="test")
    event.set_result("first")
    
    with pytest.raises(RuntimeError, match="already completed"):
        event.set_result("second")


def test_get_result_with_raise_if_none():
    event = TestEvent(data="test")
    
    with pytest.raises(ValueError, match="has not completed yet"):
        event.get_result(raise_if_none=True)


def test_set_and_get_exception():
    event = TestEvent(data="test")
    exc = ValueError("test error")
    event.set_exception(exc)
    
    assert event.is_completed
    assert event.has_error
    
    with pytest.raises(ValueError, match="test error"):
        event.get_result(raise_if_exception=True)


def test_get_exception_without_raise():
    event = TestEvent(data="test")
    event.set_exception(ValueError("test"))
    
    result = event.get_result(raise_if_exception=False)
    assert result is None