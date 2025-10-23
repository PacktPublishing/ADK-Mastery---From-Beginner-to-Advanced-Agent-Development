# Our Imports
import asyncio
import time
import uuid
from dotenv import load_dotenv

from google.adk.sessions import DatabaseSessionService
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.genai import types
from google.adk.events.event import Event

# We are going to create our own recipe assistant!

load_dotenv()

DB_URL = "sqlite:///./recipe_data.db"  # persistent storage file
APP_NAME = "Personal Recipe Assistant"
USER_ID = "alice"

# All of the tools our agent will have access to


# Adding a recipe
def add_recipe(
    name: str,
    ingredients: str,
    instructions: str,
    cook_time: str = "30 minutes",
    tool_context=None,
) -> dict:
    """Add a new recipe to your collection"""
    recipe = {
        "name": name,
        "ingredients": ingredients,
        "instructions": instructions,
        "cook_time": cook_time,
        "date_added": time.strftime("%Y-%m-%d"),
    }

    if tool_context and hasattr(tool_context, "state"):
        # Use tool_context.state if available (proper ADK way)
        recipes = tool_context.state.get("recipes", [])
        recipes.append(recipe)
        tool_context.state["recipes"] = recipes
        print(f"[Recipes] Added recipe: {name}")
        print_recipe_summary(recipes)
        return {
            "action": "add_recipe",
            "recipe": name,
            "message": f"Added recipe: {name}",
        }
    else:
        # Fallback: manually update session state and persist to database
        session = service.get_session(
            app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
        )
        recipes = session.state.get("recipes", [])
        recipes.append(recipe)

        # Create an event with state delta to persist changes
        from google.adk.sessions import types as session_types

        event = Event(
            id=str(uuid.uuid4()),
            author="user",
            content=types.Content(
                role="user", parts=[types.Part(text=f"Add recipe: {name}")]
            ),
            actions=session_types.Actions(state_delta={"recipes": recipes}),
            timestamp=time.time(),
            turn_complete=True,
        )

        # Append the event to persist state changes
        service.append_event(session=session, event=event)

        print(f"[Recipes] Added recipe: {name}")
        print_recipe_summary(recipes)
        return {
            "action": "add_recipe",
            "recipe": name,
            "message": f"Added recipe: {name}",
        }


# Viewing all recipes
def view_recipes(tool_context=None) -> dict:
    """View all saved recipes"""
    if tool_context and hasattr(tool_context, "state"):
        recipes = tool_context.state.get("recipes", [])
        print_all_recipes(recipes)
        return {"action": "view_recipes", "message": "Here are all your saved recipes"}
    else:
        # Fallback: manually get session state
        session = service.get_session(
            app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
        )
        recipes = session.state.get("recipes", [])
        print_all_recipes(recipes)
        return {"action": "view_recipes", "message": "Here are all your saved recipes"}


# Getting a specific recipe
def get_recipe(name: str, tool_context=None) -> dict:
    """Get details of a specific recipe by name"""
    if tool_context and hasattr(tool_context, "state"):
        recipes = tool_context.state.get("recipes", [])
    else:
        session = service.get_session(
            app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
        )
        recipes = session.state.get("recipes", [])

    # Find recipe (case insensitive)
    for recipe in recipes:
        if recipe["name"].lower() == name.lower():
            print_recipe_details(recipe)
            return {
                "action": "get_recipe",
                "recipe": name,
                "message": f"Found recipe: {name}",
            }

    print(f"[Recipes] Recipe '{name}' not found")
    return {
        "action": "get_recipe",
        "recipe": name,
        "message": f"Recipe '{name}' not found",
    }


# Deleting a recipe
def delete_recipe(name: str, tool_context=None) -> dict:
    """Delete a recipe by name"""
    if tool_context and hasattr(tool_context, "state"):
        recipes = tool_context.state.get("recipes", [])

        # Find and remove recipe
        for i, recipe in enumerate(recipes):
            if recipe["name"].lower() == name.lower():
                removed = recipes.pop(i)
                tool_context.state["recipes"] = recipes

                print(f"[Recipes] Deleted recipe: {name}")
                print_recipe_summary(recipes)
                return {
                    "action": "delete_recipe",
                    "recipe": name,
                    "message": f"Deleted recipe: {name}",
                }

        print(f"[Recipes] Recipe '{name}' not found")
        return {
            "action": "delete_recipe",
            "recipe": name,
            "message": f"Recipe '{name}' not found",
        }
    else:
        # Fallback: manually update session state and persist to database
        session = service.get_session(
            app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
        )
        recipes = session.state.get("recipes", [])

        # Find and remove recipe
        for i, recipe in enumerate(recipes):
            if recipe["name"].lower() == name.lower():
                removed = recipes.pop(i)

                # Create an event with state delta to persist changes
                from google.adk.sessions import types as session_types

                event = Event(
                    id=str(uuid.uuid4()),
                    author="user",
                    content=types.Content(
                        role="user", parts=[types.Part(text=f"Delete recipe: {name}")]
                    ),
                    actions=session_types.Actions(state_delta={"recipes": recipes}),
                    timestamp=time.time(),
                    turn_complete=True,
                )

                # Append the event to persist state changes
                service.append_event(session=session, event=event)

                print(f"[Recipes] Deleted recipe: {name}")
                print_recipe_summary(recipes)
                return {
                    "action": "delete_recipe",
                    "recipe": name,
                    "message": f"Deleted recipe: {name}",
                }

        print(f"[Recipes] Recipe '{name}' not found")
        return {
            "action": "delete_recipe",
            "recipe": name,
            "message": f"Recipe '{name}' not found",
        }


# Search recipes by ingredient
def search_recipes(ingredient: str, tool_context=None) -> dict:
    """Search for recipes containing a specific ingredient"""
    if tool_context and hasattr(tool_context, "state"):
        recipes = tool_context.state.get("recipes", [])
    else:
        session = service.get_session(
            app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
        )
        recipes = session.state.get("recipes", [])

    # Find recipes containing the ingredient
    matching_recipes = []
    for recipe in recipes:
        if ingredient.lower() in recipe["ingredients"].lower():
            matching_recipes.append(recipe)

    if matching_recipes:
        print(f"[Search] Found {len(matching_recipes)} recipe(s) with '{ingredient}':")
        for recipe in matching_recipes:
            print(f"  • {recipe['name']} ({recipe['cook_time']})")
    else:
        print(f"[Search] No recipes found with ingredient '{ingredient}'")

    return {
        "action": "search_recipes",
        "ingredient": ingredient,
        "found": len(matching_recipes),
    }


# Defining our agent here!
recipe_agent = Agent(
    name="recipe_agent",
    model="gemini-2.0-flash",
    description="Personal recipe collection assistant",
    instruction="""
You help users manage their personal recipe collection. You can add, view, search, and delete recipes.

When the user wants to:
  • Add a recipe      → call add_recipe(name, ingredients, instructions, cook_time)
  • View all recipes  → call view_recipes()
  • Get specific recipe → call get_recipe(name)
  • Delete a recipe   → call delete_recipe(name)
  • Search by ingredient → call search_recipes(ingredient)

Always be friendly and helpful. Suggest recipe ideas if asked. Confirm actions taken.

Current state:
- chef_name: {chef_name}
- total_recipes: {total_recipes}
- recipes: {recipes}

Example commands you understand:
- "Add my pasta recipe"
- "Show me the chocolate cake recipe"
- "What recipes use chicken?"
- "Delete the old soup recipe"
""",
    tools=[add_recipe, view_recipes, get_recipe, delete_recipe, search_recipes],
)

# Creating our session state
service = DatabaseSessionService(db_url=DB_URL)
initial_state = {"chef_name": "Alice", "total_recipes": 0, "recipes": []}

# We'll initialize the session inside an async function
SESSION_ID = None
runner = None


async def initialize_session():
    """Initialize session and runner - must be called from async context"""
    global SESSION_ID, runner

    # Seeing if we have a pre-existing session (ASYNC!)
    resp = await service.list_sessions(app_name=APP_NAME, user_id=USER_ID)
    if resp.sessions:
        SESSION_ID = resp.sessions[0].id
        print("Continuing session:", SESSION_ID)
    else:
        # Create session (ALSO ASYNC!)
        session = await service.create_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            state=initial_state,
        )
        SESSION_ID = session.id
        print("Created new session:", SESSION_ID)

    # Creating our runner
    runner = Runner(agent=recipe_agent, app_name=APP_NAME, session_service=service)


# Helper functions for printing recipes - FOR DEBUGGING PURPOSES
def print_recipe_summary(recipes):
    if not recipes:
        print("[Recipes] No recipes saved yet")
    else:
        print(f"[Recipes] Total: {len(recipes)} recipe(s)")
        for recipe in recipes:
            print(
                f"  • {recipe['name']} ({recipe['cook_time']}) - added {recipe['date_added']}"
            )


def print_all_recipes(recipes):
    if not recipes:
        print("[Recipes] No recipes saved yet")
    else:
        print(f"\n[Recipe Collection] {len(recipes)} recipe(s):")
        for i, recipe in enumerate(recipes, 1):
            print(f"\n{i}. {recipe['name']}")
            print(f"   Cook time: {recipe['cook_time']}")
            print(f"   Added: {recipe['date_added']}")


def print_recipe_details(recipe):
    print(f"\n[Recipe Details] {recipe['name']}")
    print(f"Cook time: {recipe['cook_time']}")
    print(f"Added: {recipe['date_added']}")
    print(f"\nIngredients:\n{recipe['ingredients']}")
    print(f"\nInstructions:\n{recipe['instructions']}")


# Function to call the agent
async def ask_agent(text: str):
    msg = types.Content(role="user", parts=[types.Part(text=text)])

    async for ev in runner.run_async(
        user_id=USER_ID, session_id=SESSION_ID, new_message=msg
    ):
        # Only print the assistant's text part
        if ev.is_final_response() and ev.content and ev.content.parts:
            for part in ev.content.parts:
                if hasattr(part, "text") and part.text:
                    print("\n👩‍🍳 Recipe Assistant:", part.text)


# Our loop to chat with our agent
async def main():
    # Initialize session first!
    await initialize_session()

    print("\n🍳 Personal Recipe Assistant ready! (type 'quit' to exit)")
    print(
        "Try: 'add pasta recipe', 'view recipes', 'search chicken', 'get pasta recipe'\n"
    )

    while True:
        q = input("You: ")
        if q.lower() in ("quit", "exit"):
            print("Recipe collection saved. Happy cooking! 👋")
            break
        await ask_agent(q)


if __name__ == "__main__":
    asyncio.run(main())
