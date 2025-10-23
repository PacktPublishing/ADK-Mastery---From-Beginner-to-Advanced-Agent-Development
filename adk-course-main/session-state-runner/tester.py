#!/usr/bin/env python3
"""
Simple Study Buddy - Interactive CLI Application
A streamlined AI-powered study assistant using Google ADK

Features:
- Single AI agent with multiple tools
- Persistent state management with ADK sessions
- Interactive command-line interface
- Course and assignment tracking
- Study session logging
- Natural language interaction

Installation:
pip install google-adk python-dotenv

Usage:
python simple_study_buddy.py
or
uv run simple_study_buddy.py
"""

import asyncio
import uuid
import time
import json
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv

# Google ADK imports
from google.adk.sessions import DatabaseSessionService
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.genai import types
from google.adk.events.event import Event

load_dotenv()

# Configuration
DB_URL = "sqlite:///./simple_study_buddy.db"
APP_NAME = "SimpleStudyBuddy"
USER_ID = "student"

# Global variables for session management
service = None
runner = None
session_id = None

# ============================================================================
# TOOL FUNCTIONS
# ============================================================================


def add_course(name: str, instructor: str, tool_context=None) -> dict:
    """Add a new course"""
    if tool_context and hasattr(tool_context, "state"):
        course = {
            "id": str(uuid.uuid4())[:8],
            "name": name,
            "instructor": instructor,
            "added_date": datetime.now().strftime("%Y-%m-%d"),
        }

        courses = tool_context.state.get("courses", [])
        courses.append(course)
        tool_context.state["courses"] = courses

        print(f"✅ Added course: {name} with {instructor}")
        print_courses(courses)
        return {"action": "add_course", "message": f"Added course: {name}"}

    return {"action": "add_course", "error": "Could not add course"}


def view_courses(tool_context=None) -> dict:
    """View all courses"""
    if tool_context and hasattr(tool_context, "state"):
        courses = tool_context.state.get("courses", [])
        print_courses(courses)
        return {"action": "view_courses", "count": len(courses)}

    return {"action": "view_courses", "error": "Could not access courses"}


def add_assignment(
    course_name: str, title: str, due_date: str, tool_context=None
) -> dict:
    """Add a new assignment"""
    if tool_context and hasattr(tool_context, "state"):
        assignment = {
            "id": str(uuid.uuid4())[:8],
            "course_name": course_name,
            "title": title,
            "due_date": due_date,
            "status": "Pending",
            "added_date": datetime.now().strftime("%Y-%m-%d"),
        }

        assignments = tool_context.state.get("assignments", [])
        assignments.append(assignment)
        tool_context.state["assignments"] = assignments

        print(f"✅ Added assignment: {title} for {course_name} (Due: {due_date})")
        print_assignments(assignments)
        return {"action": "add_assignment", "message": f"Added assignment: {title}"}

    return {"action": "add_assignment", "error": "Could not add assignment"}


def view_assignments(status_filter: str = "all", tool_context=None) -> dict:
    """View all assignments"""
    if tool_context and hasattr(tool_context, "state"):
        assignments = tool_context.state.get("assignments", [])

        if status_filter.lower() != "all":
            assignments = [
                a for a in assignments if a["status"].lower() == status_filter.lower()
            ]

        print_assignments(assignments, status_filter)
        return {"action": "view_assignments", "count": len(assignments)}

    return {"action": "view_assignments", "error": "Could not access assignments"}


def complete_assignment(title: str, tool_context=None) -> dict:
    """Mark an assignment as completed"""
    if tool_context and hasattr(tool_context, "state"):
        assignments = tool_context.state.get("assignments", [])

        for assignment in assignments:
            if assignment["title"].lower() == title.lower():
                assignment["status"] = "Completed"
                assignment["completed_date"] = datetime.now().strftime("%Y-%m-%d")

                print(f"✅ Completed assignment: {title}")
                print_assignments(assignments)
                return {
                    "action": "complete_assignment",
                    "message": f"Completed: {title}",
                }

        print(f"❌ Assignment '{title}' not found")
        return {
            "action": "complete_assignment",
            "error": f"Assignment '{title}' not found",
        }

    return {"action": "complete_assignment", "error": "Could not complete assignment"}


def log_study_session(
    subject: str, duration_minutes: int, notes: str = "", tool_context=None
) -> dict:
    """Log a study session"""
    if tool_context and hasattr(tool_context, "state"):
        session = {
            "id": str(uuid.uuid4())[:8],
            "subject": subject,
            "duration_minutes": duration_minutes,
            "notes": notes,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": datetime.now().strftime("%H:%M"),
        }

        sessions = tool_context.state.get("study_sessions", [])
        sessions.append(session)
        tool_context.state["study_sessions"] = sessions

        # Update total study time
        total_minutes = tool_context.state.get("total_study_minutes", 0)
        tool_context.state["total_study_minutes"] = total_minutes + duration_minutes

        print(f"✅ Logged {duration_minutes} minute study session on {subject}")
        if notes:
            print(f"   Notes: {notes}")
        print_study_stats(tool_context.state)
        return {
            "action": "log_study_session",
            "message": f"Logged study session: {subject}",
        }

    return {"action": "log_study_session", "error": "Could not log session"}


def view_study_stats(tool_context=None) -> dict:
    """View study statistics"""
    if tool_context and hasattr(tool_context, "state"):
        print_study_stats(tool_context.state)
        return {"action": "view_study_stats", "message": "Study stats displayed"}

    return {"action": "view_study_stats", "error": "Could not access stats"}


# ============================================================================
# HELPER FUNCTIONS FOR DISPLAY
# ============================================================================


def print_courses(courses):
    """Display courses in a formatted way"""
    if not courses:
        print("📚 No courses enrolled yet")
    else:
        print(f"\n📚 Your Courses ({len(courses)}):")
        print("-" * 40)
        for i, course in enumerate(courses, 1):
            print(f"  {i}. {course['name']}")
            print(f"     Instructor: {course['instructor']}")
            print(f"     Added: {course['added_date']}")
        print("-" * 40)


def print_assignments(assignments, status_filter="all"):
    """Display assignments in a formatted way"""
    if not assignments:
        print(f"📋 No assignments found (filter: {status_filter})")
    else:
        print(f"\n📋 Your Assignments - {status_filter.title()} ({len(assignments)}):")
        print("-" * 50)
        for i, assignment in enumerate(assignments, 1):
            status_icon = "✅" if assignment["status"] == "Completed" else "⏳"
            print(f"  {status_icon} {i}. {assignment['title']}")
            print(f"     Course: {assignment['course_name']}")
            print(
                f"     Due: {assignment['due_date']} | Status: {assignment['status']}"
            )
            if assignment.get("completed_date"):
                print(f"     Completed: {assignment['completed_date']}")
        print("-" * 50)


def print_study_stats(state):
    """Display study statistics"""
    sessions = state.get("study_sessions", [])
    total_minutes = state.get("total_study_minutes", 0)
    total_hours = total_minutes / 60

    print(f"\n📊 Study Statistics:")
    print("-" * 30)
    print(f"  Total Sessions: {len(sessions)}")
    print(f"  Total Hours: {total_hours:.1f}h")
    if sessions:
        avg_session = total_minutes / len(sessions)
        print(f"  Avg Session: {avg_session:.0f} minutes")

        print(f"\n  Recent Sessions:")
        for session in sessions[-5:]:  # Show last 5 sessions
            print(
                f"    • {session['subject']} - {session['duration_minutes']}min ({session['date']})"
            )
    print("-" * 30)


def print_header():
    """Print application header"""
    print("=" * 60)
    print("🎓 SIMPLE STUDY BUDDY - Your AI Academic Assistant")
    print("=" * 60)
    print("Powered by Google ADK | Type 'help' for commands")
    print()


def print_help():
    """Print help information"""
    print("\n📖 Available Commands:")
    print("-" * 40)
    print("COURSE MANAGEMENT:")
    print("  • 'add course Math with Dr. Smith'")
    print("  • 'show my courses' or 'view courses'")
    print()
    print("ASSIGNMENT TRACKING:")
    print("  • 'add assignment homework for Math due 2024-12-20'")
    print("  • 'view assignments' or 'show assignments'")
    print("  • 'complete homework'")
    print()
    print("STUDY LOGGING:")
    print("  • 'log 30 minute study session on calculus'")
    print("  • 'show study stats' or 'view stats'")
    print()
    print("GENERAL:")
    print("  • 'help' - Show this help")
    print("  • 'status' - Show current status")
    print("  • 'clear' - Clear screen")
    print("  • 'quit' or 'exit' - Exit application")
    print("-" * 40)


def print_status(state):
    """Print current status"""
    courses = state.get("courses", [])
    assignments = state.get("assignments", [])
    sessions = state.get("study_sessions", [])
    total_minutes = state.get("total_study_minutes", 0)

    pending_assignments = len([a for a in assignments if a["status"] == "Pending"])

    print(f"\n📊 Current Status:")
    print("-" * 30)
    print(f"  Student: {state.get('student_name', 'Not set')}")
    print(f"  Learning Style: {state.get('learning_style', 'Not set')}")
    print(f"  Enrolled Courses: {len(courses)}")
    print(f"  Pending Assignments: {pending_assignments}")
    print(f"  Study Sessions: {len(sessions)}")
    print(f"  Total Study Time: {total_minutes/60:.1f} hours")
    print("-" * 30)


# ============================================================================
# AI AGENT DEFINITION
# ============================================================================

study_agent = Agent(
    name="StudyBuddy",
    model="gemini-2.0-flash",
    description="Personal study assistant",
    instruction="""You are a friendly study assistant helping {student_name} manage their academic life.

Current Status:
- Student: {student_name}
- Learning Style: {learning_style}
- Total Study Time: {total_study_minutes} minutes

You can help with:
• Course management: add_course(name, instructor), view_courses()
• Assignment tracking: add_assignment(course_name, title, due_date), view_assignments(), complete_assignment(title)
• Study logging: log_study_session(subject, duration_minutes, notes), view_study_stats()

When users ask to:
- "Add course Math with Dr. Smith" → call add_course("Math", "Dr. Smith")
- "Show my courses" → call view_courses()
- "Add assignment homework for Math due tomorrow" → call add_assignment("Math", "homework", "2024-12-15")
- "View assignments" → call view_assignments()
- "Complete homework" → call complete_assignment("homework")
- "Log 30 minute study session on calculus" → call log_study_session("calculus", 30)
- "Show study stats" → call view_study_stats()

Always be encouraging and help them stay organized! Provide brief, helpful responses.
""",
    tools=[
        add_course,
        view_courses,
        add_assignment,
        view_assignments,
        complete_assignment,
        log_study_session,
        view_study_stats,
    ],
)

# ============================================================================
# SESSION MANAGEMENT
# ============================================================================


async def initialize_session(
    student_name: str = "Student", learning_style: str = "visual"
):
    """Initialize ADK session"""
    global service, runner, session_id

    try:
        print("🔄 Initializing Study Buddy...")

        # Create database service
        service = DatabaseSessionService(db_url=DB_URL)

        # Check for existing session
        resp = await service.list_sessions(app_name=APP_NAME, user_id=USER_ID)

        if resp.sessions:
            session_id = resp.sessions[0].id
            print(f"✅ Resuming existing session: {session_id[:8]}...")
        else:
            # Create new session
            initial_state = {
                "student_name": student_name,
                "learning_style": learning_style,
                "courses": [],
                "assignments": [],
                "study_sessions": [],
                "total_study_minutes": 0,
            }

            session = await service.create_session(
                app_name=APP_NAME, user_id=USER_ID, state=initial_state
            )
            session_id = session.id
            print(f"✅ Created new session: {session_id[:8]}...")

        # Create runner
        runner = Runner(agent=study_agent, app_name=APP_NAME, session_service=service)

        print("✅ Study Buddy initialized successfully!")
        return True

    except Exception as e:
        print(f"❌ Error initializing Study Buddy: {str(e)}")
        return False


async def chat_with_agent(message: str) -> str:
    """Send message to agent and get response"""
    try:
        msg = types.Content(role="user", parts=[types.Part(text=message)])

        response_parts = []
        async for event in runner.run_async(
            user_id=USER_ID, session_id=session_id, new_message=msg
        ):
            if event.is_final_response() and event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        response_parts.append(part.text)

        return (
            " ".join(response_parts)
            if response_parts
            else "I'm having trouble understanding. Can you rephrase?"
        )

    except Exception as e:
        return f"Error: {str(e)}"


async def get_current_state():
    """Get current session state"""
    try:
        session = await service.get_session(
            app_name=APP_NAME, user_id=USER_ID, session_id=session_id
        )
        return session.state
    except Exception as e:
        print(f"Error getting state: {e}")
        return {}


# ============================================================================
# CLI INTERFACE
# ============================================================================


def setup_student():
    """Initial student setup"""
    print("\n🎓 Welcome to Study Buddy!")
    print("Let's set up your profile...")

    student_name = input("Enter your name (or press Enter for 'Student'): ").strip()
    if not student_name:
        student_name = "Student"

    print("\nChoose your learning style:")
    print("1. Visual (charts, diagrams, images)")
    print("2. Auditory (discussions, lectures)")
    print("3. Kinesthetic (hands-on, practice)")
    print("4. Reading/Writing (notes, text)")

    while True:
        choice = input("Enter choice (1-4): ").strip()
        styles = {"1": "visual", "2": "auditory", "3": "kinesthetic", "4": "reading"}
        if choice in styles:
            learning_style = styles[choice]
            break
        print("Invalid choice. Please enter 1, 2, 3, or 4.")

    return student_name, learning_style


def handle_special_commands(user_input: str, state: dict) -> bool:
    """Handle special CLI commands that don't need AI"""
    command = user_input.lower().strip()

    if command in ["help", "?"]:
        print_help()
        return True

    elif command in ["status", "info"]:
        print_status(state)
        return True

    elif command in ["clear", "cls"]:
        import os

        os.system("cls" if os.name == "nt" else "clear")
        print_header()
        return True

    elif command in ["quit", "exit", "q"]:
        print("\n👋 Thanks for using Study Buddy! Keep studying hard!")
        return True

    return False


async def main_loop():
    """Main interactive loop"""
    print_header()

    # Setup student profile
    student_name, learning_style = setup_student()

    # Initialize ADK
    success = await initialize_session(student_name, learning_style)
    if not success:
        print("❌ Failed to initialize. Exiting...")
        return

    # Get initial state
    state = await get_current_state()
    print_status(state)

    print(f"\n💬 Hi {student_name}! I'm ready to help you manage your studies.")
    print("Type 'help' for commands or just tell me what you need!")

    # Main chat loop
    while True:
        try:
            print("\n" + "-" * 60)
            user_input = input("You: ").strip()

            if not user_input:
                continue

            # Get fresh state for special commands
            state = await get_current_state()

            # Handle special commands
            if handle_special_commands(user_input, state):
                if user_input.lower() in ["quit", "exit", "q"]:
                    break
                continue

            # Send to AI agent
            print("🤖 Study Buddy: ", end="", flush=True)
            response = await chat_with_agent(user_input)
            print(response)

        except KeyboardInterrupt:
            print("\n\n👋 Caught Ctrl+C. Thanks for using Study Buddy!")
            break
        except Exception as e:
            print(f"\n❌ An error occurred: {e}")
            print("Type 'help' if you need assistance.")


# ============================================================================
# MAIN FUNCTION
# ============================================================================


def main():
    """Main function"""
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Fatal error: {e}")


if __name__ == "__main__":
    main()

# ============================================================================
# EXAMPLE USAGE
# ============================================================================
"""
EXAMPLE COMMANDS TO TRY:

Setup:
- Run: python simple_study_buddy.py
- Follow setup prompts for name and learning style

Course Management:
- "Add course Calculus I with Dr. Smith"
- "Add course Physics with Dr. Johnson" 
- "Show my courses"

Assignment Tracking:
- "Add assignment Problem Set 1 for Calculus I due 2024-12-20"
- "Add assignment Lab Report for Physics due 2024-12-25"
- "View my assignments"
- "Complete Problem Set 1"

Study Logging:
- "Log 45 minute study session on derivatives"
- "Log 60 minute study session on kinematics with notes solved 10 problems"
- "Show my study stats"

Special Commands:
- "help" - Show all commands
- "status" - Show current overview
- "clear" - Clear screen
- "quit" - Exit application

The AI agent understands natural language and will call the appropriate tools
to help you manage your academic life!
"""
