"""
Simple Model Callbacks Example for Students
This shows how to intercept and modify what goes TO and FROM the AI model.
"""

from typing import Optional
from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.genai import types


def before_model_callback(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """
    Called BEFORE sending the request to the AI model.
    Perfect for: content filtering, request logging, blocking inappropriate content
    """
    # Get the user's message from the request
    user_message = ""
    if llm_request.contents:
        for content in llm_request.contents:
            if content.role == "user" and content.parts:
                user_message = content.parts[0].text
                break

    print(f"📤 Sending to model: '{user_message}'")

    # Block math questions (as an example filter)
    math_keywords = [
        "math",
        "calculate",
        "+",
        "-",
        "*",
        "/",
        "=",
        "plus",
        "minus",
        "times",
        "divided",
    ]

    if any(keyword in user_message.lower() for keyword in math_keywords):
        print("🚫 Blocking math-related content!")

        # Return a custom response instead of calling the model
        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[
                    types.Part(
                        text="Sorry, I'm not allowed to help with math problems right now. "
                        "Try asking about something else!"
                    )
                ],
            )
        )

    print("✅ Request approved - sending to model")
    return None  # Continue to model


def after_model_callback(
    callback_context: CallbackContext, llm_response: LlmResponse
) -> Optional[LlmResponse]:
    """
    Called AFTER getting response from the AI model.
    Perfect for: response filtering, adding disclaimers, logging responses
    """
    # Get the model's response text
    response_text = ""
    if llm_response.content and llm_response.content.parts:
        response_text = llm_response.content.parts[0].text

    print(f"📥 Model responded: '{response_text[:50]}...'")

    # Add a fun emoji to every response
    if response_text:
        modified_text = response_text + " 🤖"
        print("✨ Added robot emoji to response!")

        # Return the modified response
        return LlmResponse(
            content=types.Content(role="model", parts=[types.Part(text=modified_text)])
        )

    return None  # Use original response


# Create a simple chatbot with model callbacks
root_agent = LlmAgent(
    name="filtered_chatbot",
    model="gemini-2.0-flash",
    description="A chatbot that filters math questions and adds emojis",
    instruction="""
    You are a friendly chatbot. 
    - Be helpful and conversational
    - Keep responses short and friendly
    - Answer questions about various topics
    """,
    before_model_callback=before_model_callback,
    after_model_callback=after_model_callback,
)

# Example usage (uncomment to test):
# if __name__ == "__main__":
#     print("Filtered Chatbot Demo")
#     print("Try asking: 'What's the weather like?' or 'What's 2+2?'")
#
#     # Test normal question
#     response1 = chatbot.send_message("Hello, how are you?")
#     print(f"Response 1: {response1.text}\n")
#
#     # Test blocked content
#     response2 = chatbot.send_message("Can you help me calculate 15 + 25?")
#     print(f"Response 2: {response2.text}\n")
