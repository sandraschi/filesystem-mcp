from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Literal
import uvicorn
import os
import sys
import logging
import httpx
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("filesystem_backend")

# Add src to sys.path to import filesystem_mcp
# RESOLUTION: filesystem-mcp/webapp/backend/app -> filesystem-mcp/src
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", "..", "..", "src"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the authentic FastMCP instance from the source
try:
    from filesystem_mcp import app as mcp_instance

    logger.info("Successfully imported filesystem_mcp app")
except ImportError as e:
    logger.error(f"❌ Failed to import filesystem_mcp: {e}")
    mcp_instance = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Filesystem MCP Backend Starting...")
    if mcp_instance:
        # FastMCP's lifespan logic is handled when mounted/run,
        # but we can add extra startup logic here if needed.
        pass
    yield
    logger.info("🛑 Filesystem MCP Backend Stopping...")


app = FastAPI(title="Filesystem MCP Backend", lifespan=lifespan)

# CORS Configuration
origins = ["http://localhost:10743", "http://127.0.0.1:10743", "*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "mcp_connected": mcp_instance is not None}


# --- LLM Proxy Support (Copied from Virtualization MCP pattern) ---


class LLMProviderConfig(BaseModel):
    id: str
    name: str
    type: Literal["ollama", "lmstudio", "openai", "anthropic"]
    baseUrl: str
    apiKey: Optional[str] = None
    enabled: bool = False
    defaultModel: Optional[str] = None


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    provider: LLMProviderConfig
    model: str
    messages: List[Message]


@app.post("/api/llm/chat")
async def chat(request: ChatRequest):
    """Proxy chat requests to the appropriate LLM provider."""
    provider = request.provider

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            if provider.type == "ollama":
                payload = {
                    "model": request.model,
                    "messages": [
                        {"role": m.role, "content": m.content} for m in request.messages
                    ],
                    "stream": False,
                }
                response = await client.post(
                    f"{provider.baseUrl}/api/chat", json=payload
                )
            elif provider.type == "lmstudio":
                payload = {
                    "model": request.model,
                    "messages": [
                        {"role": m.role, "content": m.content} for m in request.messages
                    ],
                }
                response = await client.post(
                    f"{provider.baseUrl}/v1/chat/completions", json=payload
                )
            elif provider.type == "openai":
                headers = (
                    {"Authorization": f"Bearer {provider.apiKey}"}
                    if provider.apiKey
                    else {}
                )
                payload = {
                    "model": request.model,
                    "messages": [
                        {"role": m.role, "content": m.content} for m in request.messages
                    ],
                }
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    json=payload,
                    headers=headers,
                )
            elif provider.type == "anthropic":
                # Basic proxy for now, Anthropic is more complex (headers etc)
                return {"error": "Anthropic proxy not fully implemented in bridge yet."}
            else:
                return {"error": "Unknown provider"}

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code, detail=response.text
                )

            data = response.json()
            # Normalize response
            content = ""
            if "message" in data:  # Ollama
                content = data["message"]["content"]
            elif "choices" in data:  # OpenAI/LM Studio
                content = data["choices"][0]["message"]["content"]

            return {"content": content}

    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Mount MCP Endpoint ---
if mcp_instance:
    try:
        # Create the ASGI app from FastMCP instance (Plex Pattern)
        # FastMCP.http_app() returns a Starlette/FastAPI compatible app
        mcp_asgi_app = mcp_instance.http_app()
        app.mount("/mcp", mcp_asgi_app)
        logger.info("Mounting MCP app at /mcp")
    except Exception as e:
        logger.error(f"Failed to mount MCP app: {e}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=10742, reload=True)
