from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, TextPart, UserPromptPart

from app.agent import agent

app = FastAPI(title="personal-ai-agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_SESSIONS = 500
# In-memory conversation store keyed by session_id. Each entry holds the full pydantic-ai message list.
SESSIONS: dict[str, list[ModelMessage]] = {}


class HistoryItem(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    # Optional client-side history, used when no server session exists for session_id.
    history: list[HistoryItem] | None = None


class ChatResponse(BaseModel):
    reply: str


def _history_to_messages(items: list[HistoryItem]) -> list[ModelMessage]:
    messages: list[ModelMessage] = []
    for item in items:
        if item.role == "user":
            messages.append(ModelRequest(parts=[UserPromptPart(content=item.content)]))
        elif item.role == "assistant":
            messages.append(ModelResponse(parts=[TextPart(content=item.content)]))
    return messages


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    if req.session_id and req.session_id in SESSIONS:
        history = SESSIONS[req.session_id]
    elif req.history:
        history = _history_to_messages(req.history)
    else:
        history = []

    result = await agent.run(req.message, message_history=history)

    if req.session_id:
        SESSIONS.pop(req.session_id, None)
        SESSIONS[req.session_id] = result.all_messages()
        while len(SESSIONS) > MAX_SESSIONS:
            SESSIONS.pop(next(iter(SESSIONS)))

    return ChatResponse(reply=result.output)
