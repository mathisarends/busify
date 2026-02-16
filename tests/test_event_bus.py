import pytest
import asyncio
from dataclasses import dataclass
from busify import EventBus, BaseEvent


@dataclass(kw_only=True, frozen=True)
class UserCreatedEvent(BaseEvent[None]):
    user_id: str
    email: str


@dataclass(kw_only=True, frozen=True)
class OrderPlacedEvent(BaseEvent[dict]):
    order_id: str
    amount: float


@pytest.fixture
def bus():
    return EventBus()


@pytest.mark.asyncio
async def test_subscribe_and_dispatch(bus):
    received_events = []
    
    async def handler(event: UserCreatedEvent):
        received_events.append(event)
    
    bus.subscribe(UserCreatedEvent, handler)
    event = UserCreatedEvent(user_id="123", email="test@example.com")
    await bus.dispatch(event)
    
    assert len(received_events) == 1
    assert received_events[0].user_id == "123"


@pytest.mark.asyncio
async def test_multiple_handlers(bus):
    call_order = []
    
    async def handler1(event: UserCreatedEvent):
        call_order.append(1)
    
    async def handler2(event: UserCreatedEvent):
        call_order.append(2)
    
    bus.subscribe(UserCreatedEvent, handler1)
    bus.subscribe(UserCreatedEvent, handler2)
    
    event = UserCreatedEvent(user_id="123", email="test@example.com")
    await bus.dispatch(event)
    
    assert len(call_order) == 2
    assert set(call_order) == {1, 2}


@pytest.mark.asyncio
async def test_unsubscribe(bus):
    received = []
    
    async def handler(event: UserCreatedEvent):
        received.append(event)
    
    bus.subscribe(UserCreatedEvent, handler)
    bus.unsubscribe(UserCreatedEvent, handler)
    
    event = UserCreatedEvent(user_id="123", email="test@example.com")
    await bus.dispatch(event)
    
    assert len(received) == 0


@pytest.mark.asyncio
async def test_unsubscribe_all_for_event_type(bus):
    received = []
    
    async def handler1(event: UserCreatedEvent):
        received.append(1)
    
    async def handler2(event: UserCreatedEvent):
        received.append(2)
    
    bus.subscribe(UserCreatedEvent, handler1)
    bus.subscribe(UserCreatedEvent, handler2)
    bus.unsubscribe_all(UserCreatedEvent)
    
    event = UserCreatedEvent(user_id="123", email="test@example.com")
    await bus.dispatch(event)
    
    assert len(received) == 0


@pytest.mark.asyncio
async def test_unsubscribe_all(bus):
    received = []
    
    async def handler1(event: UserCreatedEvent):
        received.append(1)
    
    async def handler2(event: OrderPlacedEvent):
        received.append(2)
    
    bus.subscribe(UserCreatedEvent, handler1)
    bus.subscribe(OrderPlacedEvent, handler2)
    bus.unsubscribe_all()
    
    await bus.dispatch(UserCreatedEvent(user_id="123", email="test@example.com"))
    await bus.dispatch(OrderPlacedEvent(order_id="456", amount=99.99))
    
    assert len(received) == 0


@pytest.mark.asyncio
async def test_handler_exception_is_caught(bus):
    async def failing_handler(event: UserCreatedEvent):
        raise ValueError("Handler failed")
    
    bus.subscribe(UserCreatedEvent, failing_handler)
    event = UserCreatedEvent(user_id="123", email="test@example.com")
    await bus.dispatch(event)
    
    assert event.has_error


@pytest.mark.asyncio
async def test_handler_exception_doesnt_stop_others(bus):
    received = []
    
    async def failing_handler(event: UserCreatedEvent):
        raise ValueError("Fail")
    
    async def working_handler(event: UserCreatedEvent):
        received.append(event)
    
    bus.subscribe(UserCreatedEvent, failing_handler)
    bus.subscribe(UserCreatedEvent, working_handler)
    
    event = UserCreatedEvent(user_id="123", email="test@example.com")
    await bus.dispatch(event)
    
    assert len(received) == 1


@pytest.mark.asyncio
async def test_wait_for_event(bus):
    async def emit_event():
        await asyncio.sleep(0.1)
        await bus.dispatch(UserCreatedEvent(user_id="123", email="test@example.com"))
    
    asyncio.create_task(emit_event())
    
    event = await bus.wait_for_event(UserCreatedEvent, timeout=1.0)
    assert event.user_id == "123"


@pytest.mark.asyncio
async def test_wait_for_event_with_predicate(bus):
    async def emit_events():
        await asyncio.sleep(0.1)
        await bus.dispatch(UserCreatedEvent(user_id="wrong", email="wrong@example.com"))
        await asyncio.sleep(0.1)
        await bus.dispatch(UserCreatedEvent(user_id="correct", email="correct@example.com"))
    
    asyncio.create_task(emit_events())
    
    event = await bus.wait_for_event(
        UserCreatedEvent,
        predicate=lambda e: e.user_id == "correct",
        timeout=2.0
    )
    assert event.user_id == "correct"


@pytest.mark.asyncio
async def test_wait_for_event_timeout(bus):
    with pytest.raises(asyncio.TimeoutError):
        await bus.wait_for_event(UserCreatedEvent, timeout=0.1)


@pytest.mark.asyncio
async def test_event_with_result(bus):
    async def handler(event: OrderPlacedEvent):
        event.set_result({"status": "processed", "order_id": event.order_id})
    
    bus.subscribe(OrderPlacedEvent, handler)
    
    event = OrderPlacedEvent(order_id="456", amount=99.99)
    await bus.dispatch(event)
    
    result = event.get_result()
    assert result["status"] == "processed"
    assert result["order_id"] == "456"