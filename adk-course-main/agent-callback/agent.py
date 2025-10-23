"""
Simple Agent Callbacks Example for Students
This example shows how to use before and after callbacks to monitor agent interactions.
"""

from datetime import datetime
from typing import Optional
from google.adk.agents import Agent, LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.genai import types


def before_agent_callback(callback_context: CallbackContext) -> Optional[types.Content]:
    """
    Called BEFORE the agent processes the user's message.
    Great for: logging, authentication, input validation
    """
    print(f"🚀 Starting to process: '{callback_context.user_content}'")
    print(f"⏰ Time: {datetime.now().strftime('%H:%M:%S')}")

    # Store start time in session state
    callback_context.state["start_time"] = datetime.now()

    return None  # Continue normal processing


def after_agent_callback(callback_context: CallbackContext) -> Optional[types.Content]:
    """
    Called AFTER the agent generates a response.
    Great for: logging responses, analytics, post-processing
    """
    # Calculate how long it took
    if "start_time" in callback_context.state:
        duration = datetime.now() - callback_context.state["start_time"]
        print(f"⚡ Response generated in {duration.total_seconds():.1f} seconds")

    print(f"✅ Agent responded: '{callback_context.state.to_dict()}...'")

    return None  # Don't modify the response


root_agent = LlmAgent(
    name="math_tutor",
    model="gemini-2.0-flash",
    description="A friendly math tutor for students",
    instruction="""
    You are a helpful math tutor. 
    - Give clear, step-by-step explanations
    - Be encouraging and patient
    - Keep answers concise but complete
    """,
    before_agent_callback=before_agent_callback,
    after_agent_callback=after_agent_callback,
)
