import asyncio
from dataclasses import dataclass

from busify import EventBus, BaseEvent


WELCOME_EMAIL_DELAY = 0.5
PROFILE_CREATION_DELAY = 0.3
PAYMENT_PROCESSING_DELAY = 0.4
DELAYED_EVENT_DELAY = 1.0
EVENT_TIMEOUT = 5.0


@dataclass(kw_only=True, frozen=True)
class UserRegistered(BaseEvent[str]):
    username: str
    email: str


@dataclass(kw_only=True, frozen=True)
class OrderPlaced(BaseEvent[dict]):
    order_id: str
    amount: float


async def send_welcome_email(event: UserRegistered) -> None:
    print(f"📧 Sending welcome email to {event.email}")
    await asyncio.sleep(WELCOME_EMAIL_DELAY)
    print(f"✅ Welcome email sent to {event.username}")
    event.set_result(f"Email sent to {event.email}")


async def create_user_profile(event: UserRegistered) -> None:
    print(f"👤 Creating profile for {event.username}")
    await asyncio.sleep(PROFILE_CREATION_DELAY)  
    print(f"✅ Profile created for {event.username}")


async def process_payment(event: OrderPlaced) -> None:
    print(f"💳 Processing payment of ${event.amount:.2f} for order {event.order_id}")
    await asyncio.sleep(PAYMENT_PROCESSING_DELAY)
    print(f"✅ Payment processed for order {event.order_id}")
    
    event.set_result({
        "order_id": event.order_id,
        "status": "paid",
        "amount": event.amount
    })


def print_section(title: str) -> None:
    print(f"\n📌 {title}")
    print("-" * 60)


def print_result(result: str | dict) -> None:
    print(f"📊 Event result: {result}\n")


async def demonstrate_user_registration(bus: EventBus) -> None:
    print_section("Example 1: User Registration")
    event = UserRegistered(username="alice", email="alice@example.com")
    await bus.dispatch(event)
    print_result(event.get_result())


async def demonstrate_order_placement(bus: EventBus) -> None:
    print_section("Example 2: Order Placement")
    event = OrderPlaced(order_id="ORD-12345", amount=99.99)
    await bus.dispatch(event)
    print_result(event.get_result())


async def demonstrate_wait_for_event(bus: EventBus) -> None:
    print_section("Example 3: Wait for Event")
    
    async def dispatch_delayed_event():
        await asyncio.sleep(DELAYED_EVENT_DELAY)
        event = UserRegistered(username="bob", email="bob@example.com")
        print("🔔 Background task dispatching event...")
        await bus.dispatch(event)
    
    asyncio.create_task(dispatch_delayed_event())
    
    print("⏳ Waiting for UserRegistered event...")
    received_event = await bus.wait_for_event(
        UserRegistered,
        timeout=EVENT_TIMEOUT,
        predicate=lambda e: e.username == "bob"
    )
    print(f"📨 Received event for user: {received_event.username}\n")


async def demonstrate_awaitable_event(bus: EventBus) -> None:
    print_section("Example 4: Awaiting Event Result")
    event = OrderPlaced(order_id="ORD-67890", amount=149.99)
    
    dispatch_task = asyncio.create_task(bus.dispatch(event))
    result = await event
    print_result(result)
    await dispatch_task


def setup_event_bus() -> EventBus:
    bus = EventBus()
    bus.subscribe(UserRegistered, send_welcome_email)
    bus.subscribe(UserRegistered, create_user_profile)
    bus.subscribe(OrderPlaced, process_payment)
    return bus


async def main() -> None:
    print("=" * 60)
    print("🚀 Busify Event Bus Example")
    print("=" * 60)
    
    bus = setup_event_bus()
    
    await demonstrate_user_registration(bus)
    await demonstrate_order_placement(bus)
    await demonstrate_wait_for_event(bus)
    await demonstrate_awaitable_event(bus)
    
    print("=" * 60)
    print("✨ All examples completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())