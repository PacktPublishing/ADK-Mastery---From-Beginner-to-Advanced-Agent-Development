import asyncio
from google.genai import types
import uuid
from dotenv import load_dotenv
from google.adk.sessions import InMemorySessionService
from google.adk.agents import Agent
from google.adk.runners import Runner
from pydantic import BaseModel, Field
from typing import Optional


load_dotenv()


# Defining our customer schema using pydantic
class CustomerStateOutput(BaseModel):
    customer_name: str = Field(description="Full name of the customer.")
    favorite_category: str = Field(
        description="Customer's preferred product category for shopping."
    )
    recent_order: str = Field(
        description="Details of the customer's most recent order including product, order number, and status."
    )
    loyalty_points: int = Field(
        description="Current number of loyalty/reward points the customer has earned.",
        ge=0,
    )


async def main():

    # Create session service to store customer data
    session_service = InMemorySessionService()

    # Simple customer profile
    customer_data = {
        "customer_name": "Sarah Johnson",
        "favorite_category": "Electronics",
        "recent_order": "iPhone 15 Pro - Order #12345 - Shipped",
        "loyalty_points": "500",
    }

    # Create the customer support agent
    support_agent = Agent(
        name="CustomerSupport",
        model="gemini-2.0-flash",
        output_schema=CustomerStateOutput,
        output_key="state",
        instruction="You are a friendly customer support agent for TechStore. Customer: {customer_name}. Their favorite category is {favorite_category}. Recent order: {recent_order}. Loyalty points: {loyalty_points}.",
    )

    # Create session
    APP_NAME = "TechStore"
    CUSTOMER_ID = "sarah_j"
    SESSION_ID = str(uuid.uuid4())

    await session_service.create_session(
        app_name=APP_NAME,
        user_id=CUSTOMER_ID,
        session_id=SESSION_ID,
        state=customer_data,
    )

    print(f"🛒 Customer: {customer_data['customer_name']}")
    print(f"📱 Favorite: {customer_data['favorite_category']}")
    print(f"📦 Recent Order: {customer_data['recent_order']}")
    print(f"⭐ Points: {customer_data['loyalty_points']}")

    # Create runner
    runner = Runner(
        agent=support_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

    # Customer asks a question
    customer_message = types.Content(
        role="user",
        parts=[types.Part(text="Hi! Can you check my recent order status?")],
    )

    print(f"customer_message: ==> {customer_message}")

    print(f"\n💬 Customer: Hi! Can you check my recent order status?")
    print("🤖 Support Agent: ", end="")

    # Get response from agent
    async for event in runner.run_async(
        user_id=CUSTOMER_ID,
        session_id=SESSION_ID,
        new_message=customer_message,
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                print(event.content.parts[0].text)

    # Show final session state
    session = await session_service.get_session(
        app_name=APP_NAME, user_id=CUSTOMER_ID, session_id=SESSION_ID
    )

    # Checks if structured output exists in session state under the output_key
    if "state" in session.state:
        structured_data = session.state["state"]
        print(structured_data)
        print("✅ Updating session state:")

        for key, value in structured_data.items():
            session.state[key] = value
            print(f"  - {key} updated to: {value}")

        del session.state["state"]
    else:
        print("No structured output found in session state.")

    print(f"\n📊 Session Data:")
    for key, value in session.state.items():
        print(f"   {key}: {value}")


if __name__ == "__main__":
    asyncio.run(main())
