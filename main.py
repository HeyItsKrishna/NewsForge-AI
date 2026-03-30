import os
import uuid
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

from agent import create_agent

session_service = InMemorySessionService()
APP_NAME = "newsforge_ai"
runner = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global runner
    agent = create_agent()
    runner = Runner(agent=agent, app_name=APP_NAME, session_service=session_service)
    print("NewsForge AI initialized")
    yield
    print("NewsForge AI shutting down")

app = FastAPI(title="NewsForge AI", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class ChatRequest(BaseModel):
    message: str
    session_id: str = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    timestamp: str

@app.get("/health")
async def health():
    return {"status": "healthy", "agent": "NewsForge AI", "version": "1.0.0"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    global runner
    if not runner:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    session_id = request.session_id or str(uuid.uuid4())
    user_id = "web_user"
    existing = await session_service.get_session(app_name=APP_NAME, user_id=user_id, session_id=session_id)
    if not existing:
        await session_service.create_session(app_name=APP_NAME, user_id=user_id, session_id=session_id)
    content = genai_types.Content(role="user", parts=[genai_types.Part(text=request.message)])
    full_response = ""
    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
        if event.is_final_response() and event.content and event.content.parts:
            for part in event.content.parts:
                if hasattr(part, "text") and part.text:
                    full_response += part.text
    return ChatResponse(
        response=full_response or "Could not generate a response. Please try again.",
        session_id=session_id,
        timestamp=datetime.utcnow().isoformat()
    )

@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    with open("index.html", "r") as f:
        return HTMLResponse(content=f.read())

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
