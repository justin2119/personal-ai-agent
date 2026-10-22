"""Interactive CLI to test the PydanticAI agent locally, without running FastAPI.

Usage (from the backend/ directory):
    python test_agent.py

Type a question and press Enter. Type 'exit', 'quit' or press Ctrl+C to stop.
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    print("Missing dependency: python-dotenv. Run: pip install -r requirements.txt")
    sys.exit(1)

EXIT_WORDS = {"exit", "quit", "q"}


def check_environment() -> None:
    """Fail early with a clear message if the LLM key is missing."""
    if not os.getenv("RODIUM_API_KEY"):
        print("Error: RODIUM_API_KEY is not set. Add it to backend/.env (see .env.example).")
        sys.exit(1)


def load_agent():
    try:
        from app.agent import agent
    except ImportError as exc:
        print(f"Error: missing dependency or module ({exc}). Run: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as exc:
        print(f"Error while initialising the agent: {type(exc).__name__}: {exc}")
        sys.exit(1)
    return agent


def list_configured_tools(agent) -> None:
    """Print the tools registered on the agent, using the toolset internals of PydanticAI."""
    print("Configured tools:")
    names = []
    try:
        # Function tools registered with @agent.tool or passed as tools=[...]
        for name in agent._function_toolset.tools.keys():  # type: ignore[attr-defined]
            names.append(name)
    except AttributeError:
        names = []
    if not names:
        print("  (could not read the tool list from this PydanticAI version)")
        return
    for name in sorted(names):
        print(f"  - {name}")


def describe_tool_calls(messages) -> None:
    """Print each tool call and its return value from the run's new messages."""
    from pydantic_ai.messages import ToolCallPart, ToolReturnPart

    calls = {}
    for message in messages:
        for part in getattr(message, "parts", []):
            if isinstance(part, ToolCallPart):
                calls[part.tool_call_id] = part
                print(f"  [tool call] {part.tool_name}({part.args})")
    for message in messages:
        for part in getattr(message, "parts", []):
            if isinstance(part, ToolReturnPart):
                preview = str(part.content)
                if len(preview) > 300:
                    preview = preview[:300] + "..."
                print(f"  [tool result] {part.tool_name}: {preview}")


async def ask(agent, question: str) -> None:
    result = await agent.run(question)
    describe_tool_calls(result.new_messages())
    print(f"\nAgent: {result.output}\n")


async def main() -> None:
    check_environment()
    agent = load_agent()
    list_configured_tools(agent)
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
            await ask(agent, question)
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
