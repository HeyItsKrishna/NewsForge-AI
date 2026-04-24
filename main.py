import os
import uuid
import traceback
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

from agent import create_agent

APP_NAME = "newsforge_ai"
runner = None
session_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global runner, session_service
    session_service = InMemorySessionService()
    agent = create_agent()
    runner = Runner(agent=agent, app_name=APP_NAME, session_service=session_service)
    print("NewsForge AI initialized")
    yield

app = FastAPI(title="NewsForge AI", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/chat")
async def chat(request: Request):
    global runner, session_service
    try:
        body = await request.json()
        message = body.get("message", "")
        user_id = "web_user"
        # Always create a fresh session per request to avoid SessionNotFoundError
        session_id = str(uuid.uuid4())
        await session_service.create_session(app_name=APP_NAME, user_id=user_id, session_id=session_id)
        content = genai_types.Content(role="user", parts=[genai_types.Part(text=message)])
        full_response = ""
        async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
            if event.is_final_response() and event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        full_response += part.text
        return JSONResponse(content={
            "response": full_response or "No response generated.",
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        print(f"CHAT ERROR: {traceback.format_exc()}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    with open("index.html", "r") as f:
        return HTMLResponse(content=f.read())

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
