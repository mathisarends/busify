# busify

Type-safe async event bus for Python.

## Installation

```bash
pip install busify
```

## Quick Start

```python
import asyncio
from dataclasses import dataclass
from busify import EventBus, BaseEvent

@dataclass(kw_only=True, frozen=True)
class UserCreatedEvent(BaseEvent[None]):
    user_id: str
    email: str

bus = EventBus()

async def send_welcome_email(event: UserCreatedEvent):
    print(f"Sending welcome email to {event.email}")

bus.subscribe(UserCreatedEvent, send_welcome_email)

async def main():
    event = UserCreatedEvent(user_id="123", email="user@example.com")
    await bus.dispatch(event)

asyncio.run(main())
```

## Core Concepts

### Events

Events are immutable dataclasses that can optionally carry results:

```python
@dataclass(frozen=True)
class ScreenshotResult:
    data: bytes

@dataclass(kw_only=True, frozen=True)
class CaptureScreenshotEvent(BaseEvent[ScreenshotResult]):
    quality: int = 90
```

### Handlers

Handlers are async functions that process events:

```python
async def capture_handler(event: CaptureScreenshotEvent):
    data = await take_screenshot(quality=event.quality)
    event.set_result(ScreenshotResult(data=data))

bus.subscribe(CaptureScreenshotEvent, capture_handler)
```

### Dispatching

Dispatch events and retrieve results:

```python
event = CaptureScreenshotEvent(quality=95)
await bus.dispatch(event)
result = event.get_result()
```

## API Reference

### EventBus

#### `subscribe(event_type, handler)`

Subscribe a handler to an event type.

#### `unsubscribe(event_type, handler)`

Remove a specific handler.

#### `unsubscribe_all(event_type=None)`

Remove all handlers for an event type, or all handlers if `event_type` is None.

#### `dispatch(event)`

Dispatch an event to all subscribed handlers. Returns the event.

#### `wait_for_event(event_type, timeout=None, predicate=None)`

Wait for a specific event with optional timeout and predicate.

```python
event = await bus.wait_for_event(
    UserCreatedEvent,
    timeout=5.0,
    predicate=lambda e: e.email.endswith("@example.com")
)
```

### BaseEvent

#### Properties

- `id` - Unique event identifier
- `timestamp` - Event creation timestamp
- `is_completed` - Whether the event has completed
- `has_error` - Whether the event completed with an error

#### Methods

- `set_result(value)` - Set the event result
- `get_result(raise_if_none=False, raise_if_exception=True)` - Retrieve the result
- `set_exception(exc)` - Mark the event as failed

## Error Handling

Failed handlers don't crash the dispatch:

```python
async def failing_handler(event: UserCreatedEvent):
    raise ValueError("Something went wrong")

async def working_handler(event: UserCreatedEvent):
    print("This still runs")

bus.subscribe(UserCreatedEvent, failing_handler)
bus.subscribe(UserCreatedEvent, working_handler)

event = UserCreatedEvent(user_id="123", email="user@example.com")
await bus.dispatch(event)

if event.has_error:
    event.get_result(raise_if_exception=True)  # Raises the exception
```

## Requirements

Python 3.12+

## License

MIT
