"""Interactive CLI to test the PydanticAI agent locally, without running FastAPI.

Usage (from the backend/ directory):
    python test_agent.py

Type a question and press Enter. Type 'exit', 'quit' or press Ctrl+C to stop.
"""

import asyncio
import os

from dotenv import load_dotenv
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, ToolCallPart, ToolReturnPart

from app.agent import agent

load_dotenv()

EXIT_WORDS = {"exit", "quit", "q"}

# Names of the tools registered on the agent in app/agent.py.
# Kept explicit so the script only relies on the public API of PydanticAI.
CONFIGURED_TOOLS = (
    "search_web",
    "get_weather",
    "list_calendar_events",
    "create_calendar_event",
    "search_drive_files",
    "read_drive_file",
    "send_email",
    "search_notion",
    "create_notion_page",
)

PREVIEW_LIMIT = 300


def check_environment() -> None:
    """Fail early with a clear message if the LLM key is missing."""
    if not os.getenv("RODIUM_API_KEY"):
        print("Error: RODIUM_API_KEY is not set. Add it to backend/.env (see .env.example).")
        raise SystemExit(1)


def list_configured_tools() -> None:
    """Print the names of the tools configured on the agent."""
    print("Configured tools:")
    for name in sorted(CONFIGURED_TOOLS):
        print(f"  - {name}")


def _preview(value: object) -> str:
    text = str(value)
    if len(text) > PREVIEW_LIMIT:
        return text[:PREVIEW_LIMIT] + "..."
    return text


def describe_tool_calls(messages: list[ModelMessage]) -> None:
    """Print each tool call and its return value from the run's new messages."""
    for message in messages:
        if isinstance(message, ModelResponse):
            for part in message.parts:
                if isinstance(part, ToolCallPart):
                    print(f"  [tool call] {part.tool_name}({part.args})")
    for message in messages:
        if isinstance(message, ModelRequest):
            for part in message.parts:
                if isinstance(part, ToolReturnPart):
                    print(f"  [tool result] {part.tool_name}: {_preview(part.content)}")


async def ask(question: str) -> None:
    result = await agent.run(question)
    describe_tool_calls(result.new_messages())
    print(f"\nAgent: {result.output}\n")


async def main() -> None:
    check_environment()
    list_configured_tools()
    print("\nType a question. Type 'exit' to quit.\n")

    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break
        if not question:
            continue
        if question.lower() in EXIT_WORDS:
            print("Bye.")
            break
        try:
            await ask(question)
        except KeyboardInterrupt:
            print("\nRequest interrupted.")
        except Exception as exc:
            # Network, auth, quota or provider errors: report and keep the loop alive.
            print(f"\nError during the request: {type(exc).__name__}: {exc}\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBye.")
