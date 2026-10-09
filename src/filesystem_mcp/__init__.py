"""
Filesystem MCP - A FastMCP 3.2+ compliant server for file system operations with concurrency safety.

This module provides a comprehensive MCP server with file system, Git repository,
and Docker container management capabilities using the portmanteau pattern for
consolidated tool interfaces with enhanced conversational responses and sampling.

CRITICAL: All file operations now use atomic patterns and proper locking to prevent
corruption when multiple clients access the same files simultaneously via FastMCP 3.2+ universal connect pattern.
"""

import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import structlog

# Configure structlog for JSON output with proper MCP stderr handling
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

# Setup file handler for persistent logs
# Use the repository's logs directory instead of CWD to avoid PermissionErrors in Claude Desktop
try:
    # Resolve path to repo root: src/filesystem_mcp/__init__.py -> src/filesystem_mcp -> src -> repo_root
    repo_root = Path(__file__).resolve().parent.parent.parent
    log_dir = repo_root / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "filesystem_mcp.log"
except Exception:
    # Fallback to home directory if repo path resolution fails
    log_dir = Path.home() / ".filesystem-mcp"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "filesystem_mcp.log"

file_handler = logging.FileHandler(log_file)
file_handler.setFormatter(logging.Formatter("%(message)s"))

# Setup stderr handler for MCP server logs (stdout is reserved for MCP protocol)
stderr_handler = logging.StreamHandler(sys.stderr)
stderr_handler.setFormatter(logging.Formatter("%(message)s"))

# Configure root logger - file and stderr output
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(file_handler)
root_logger.addHandler(stderr_handler)

logger = structlog.get_logger(__name__)

# Import FastMCP 2.14.3+ compliant server
from fastmcp import FastMCP
from fastmcp.server import create_proxy


@asynccontextmanager
async def server_lifespan(mcp_instance: FastMCP):
    """Server lifespan for startup and cleanup."""
    logger.info("Filesystem MCP server starting up", version="2.2.0")
    logger.info("FastMCP 3.2+ with concurrency safety enabled")
    yield
    logger.info("Filesystem MCP server shutting down")


# Create the main application instance
app = FastMCP(
    name="filesystem-mcp",
    instructions="""You are an MCP server for file system and Docker operations with FastMCP 3.2+ concurrency safety.

CORE CAPABILITIES:
- File system operations: read, write, edit, move, search, analyze files and directories
- Git repository management: clone, commit, branch, merge, diff, history tracking
- Docker container orchestration: lifecycle, images, networks, volumes, compose
- System monitoring: resources, processes, performance metrics
- Agentic workflows: SEP-1577 compliant autonomous file operations with and without sampling

CONCURRENCY SAFETY:
- All file write operations use atomic patterns to prevent corruption
- Proper locking mechanisms prevent race conditions
- FastMCP 3.2+ universal connect pattern support (stdio + HTTP)
- Thread-safe operations for 5+ simultaneous clients

AVAILABLE TOOLS:
\u2022 file_ops, dir_ops, search_ops - file and directory I/O
\u2022 container_ops, infra_ops - Docker containers, images, networks, volumes
\u2022 compose_up, compose_down, compose_ps, compose_logs, compose_config, compose_restart - Docker Compose
\u2022 monitor_get_* - system metrics and processes (e.g. monitor_get_resource_usage)
\u2022 host_ops - host info, environment, help
\u2022 agentic_file_workflow - LLM sampling workflow (requires client ctx.sample)

Portmanteau tools (file_ops, dir_ops) use an operation enum; Compose and monitoring are atomic per operation.""",
    lifespan=server_lifespan,
    version="2.2.0",
)

from starlette.requests import Request
from starlette.responses import JSONResponse, Response


@app.custom_route("/api/health", methods=["GET"])
async def _api_health(_request: Request) -> Response:
    return JSONResponse(
        {
            "status": "healthy",
            "server_name": "filesystem-mcp",
            "version": "2.2.0",
        }
    )


@app.custom_route("/health", methods=["GET"])
async def _health(request: Request) -> Response:
    return await _api_health(request)


_bridge_proxies = []
bridge_urls = os.getenv("MCP_BRIDGE_URLS", "")
if bridge_urls:
    for url in bridge_urls.split(","):
        url = url.strip()
        if url:
            try:
                app.add_provider(create_proxy(url))
                _bridge_proxies.append(url)
            except Exception as exc:
                logger.warning("Failed to register bridge proxy", url=url, error=str(exc))


# Import and register all tool modules after app creation
# This ensures all tools are available when the server starts
def _import_tools():
    """Import all portmanteau tool modules to register them with the app."""
    try:
        # Import the portmanteau tool modules - they will register with the global app object
        import importlib

        tool_modules = [
            ".tools.portmanteau_file_safe",  # Concurrency-safe file utilities
            ".tools.portmanteau_file",  # File IO portmanteau
            ".tools.portmanteau_directory",  # Directory structure
            ".tools.portmanteau_search",  # Search and comparison
            ".tools.portmanteau_container",  # Container lifecycle
            ".tools.portmanteau_infrastructure",  # Images, nets, volumes
            ".tools.portmanteau_orchestration",  # Docker Compose
            ".tools.portmanteau_monitoring",  # System monitoring
            ".tools.portmanteau_host",  # Host context
            ".tools.agentic_file_workflow",  # Sampling-based autonomous workflow
            ".tools.portmanteau_system",  # Server lifecycle (shutdown)
        ]

        for module_name in tool_modules:
            try:
                importlib.import_module(module_name, package=__name__)
                logger.debug(f"Portmanteau tool module {module_name} imported successfully")
            except ImportError as e:
                # Log warning but don't fail - some modules may have optional dependencies
                logger.warning(
                    f"Failed to import portmanteau tool module {module_name}: {e}. Some tools may not be available."
                )
            except Exception as e:
                logger.error(f"Failed to import portmanteau tool module {module_name}: {e}")
                # Only raise for non-import errors
                raise

        logger.info("All portmanteau tool modules imported successfully")
        return True

    except Exception as e:
        logger.exception("Failed to import portmanteau tool modules: %s", e)
        raise


# Import tools immediately - raises on failure, server must not start without tools
_import_tools()

# Prompt templates (registered on import; failure must not take the server down)
try:
    from . import prompts as _prompts  # noqa: F401
except Exception as e:
    logger.warning("Failed to register prompt templates", error=str(e))


# Export ASGI app for HTTP/HTTPS mode (for web apps)
def http_app():
    """Get ASGI application for HTTP/HTTPS mode.

    Usage:
        from filesystem_mcp import http_app
        import uvicorn
        uvicorn.run(http_app(), host="127.0.0.1", port=10742)
    """
    import time

    from starlette.middleware.cors import CORSMiddleware
    from starlette.responses import JSONResponse
    from starlette.routing import Route

    _start = time.time()

    async def _tool_names() -> list[str]:
        try:
            return sorted(t.name for t in await app.list_tools())
        except Exception:
            return []

    async def diagnostics(request):
        try:
            import psutil

            cpu = psutil.cpu_percent()
            mem = psutil.virtual_memory().percent
            disk = psutil.disk_usage("/").percent
        except ImportError:
            cpu = mem = disk = 0
        return JSONResponse(
            {
                "success": True,
                "backend": {"port": 10742, "status": "running", "uptime": time.time() - _start},
                "system": {"cpu_percent": cpu, "memory_percent": mem, "disk_percent": disk},
                "tools": {"total": len(await _tool_names()), "names": await _tool_names()},
                "cua_status": {"tesseract_available": False, "window_found": False},
            }
        )

    async def status(request):
        return JSONResponse(
            {
                "success": True,
                "status": "ok",
                "server": "filesystem-mcp",
                "version": "2.2.0",
                "uptime_seconds": time.time() - _start,
                "tool_count": len(await _tool_names()),
                "providers": {"mcp": "ok"},
            }
        )

    async def capabilities(request):
        tools = await _tool_names()
        return JSONResponse(
            {
                "success": True,
                "server": "filesystem-mcp",
                "version": "2.2.0",
                "capabilities": {
                    "tools": tools,
                    "features": {
                        "file_operations": True,
                        "directory_operations": True,
                        "search": True,
                        "docker": True,
                        "monitoring": True,
                        "host_context": True,
                        "agentic_workflows": True,
                        "concurrency_safety": True,
                        "dual_transport": True,
                    },
                },
            }
        )

    async def skills(request):
        return JSONResponse({"success": True, "skills": []})

    # LLM provider registry: local auto-detect + cloud keyed.
    # Keys are NEVER accepted via GET and NEVER echoed in any response.
    _LLM_LOCAL = {
        "ollama": "http://127.0.0.1:11434",
        "lmstudio": "http://127.0.0.1:1234",
    }
    _LLM_CLOUD = {
        "openai": "https://api.openai.com/v1",
        "anthropic": "https://api.anthropic.com/v1",
    }

    async def _probe(url: str) -> bool:
        import httpx

        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                r = await client.get(url)
                return r.status_code == 200
        except Exception:
            return False

    async def _detect_locals() -> list:
        import asyncio

        names = list(_LLM_LOCAL)
        probes = {
            "ollama": f"{_LLM_LOCAL['ollama']}/api/tags",
            "lmstudio": f"{_LLM_LOCAL['lmstudio']}/v1/models",
        }
        results = await asyncio.gather(*(_probe(probes[n]) for n in names))
        return [
            {"name": n, "detected": bool(ok), "baseUrl": _LLM_LOCAL[n]} for n, ok in zip(names, results, strict=True)
        ]

    async def llm_discover(request):
        detected = await _detect_locals()
        return JSONResponse({"success": True, "providers": detected})

    async def llm_providers(request):
        """Provider registry: local detected flags + cloud configured flags (no key bytes)."""
        detected = {p["name"]: p["detected"] for p in await _detect_locals()}
        providers = [
            {
                "id": "ollama",
                "name": "Ollama",
                "local": True,
                "detected": detected.get("ollama", False),
                "baseUrl": _LLM_LOCAL["ollama"],
            },
            {
                "id": "lm-studio",
                "name": "LM Studio",
                "local": True,
                "detected": detected.get("lmstudio", False),
                "baseUrl": _LLM_LOCAL["lmstudio"],
            },
            {
                "id": "openai",
                "name": "OpenAI",
                "local": False,
                "configured": bool(os.environ.get("OPENAI_API_KEY")),
                "baseUrl": _LLM_CLOUD["openai"],
            },
            {
                "id": "anthropic",
                "name": "Anthropic",
                "local": False,
                "configured": bool(os.environ.get("ANTHROPIC_API_KEY")),
                "baseUrl": _LLM_CLOUD["anthropic"],
            },
        ]
        return JSONResponse({"success": True, "providers": providers})

    async def llm_models(request):
        """Model list per provider: live when reachable/keyed, curated fallback otherwise."""
        import httpx

        provider = request.query_params.get("provider", "ollama")
        base = _LLM_LOCAL.get(provider, _LLM_LOCAL["ollama"])
        models: list = []
        live = False
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                if provider == "ollama":
                    r = await client.get(f"{base}/api/tags")
                    if r.status_code == 200:
                        models = [m.get("name", "") for m in r.json().get("models", []) if m.get("name")]
                        live = True
                else:
                    r = await client.get(f"{base}/v1/models")
                    if r.status_code == 200:
                        models = [m.get("id", "") for m in r.json().get("data", []) if m.get("id")]
                        live = True
        except Exception as e:
            logger.warning("llm_models live lookup failed", provider=provider, error=str(e))
        if not models:
            models = ["llama3.2:1b", "llama3.2:3b", "qwen2.5:7b"] if provider == "ollama" else ["default"]
        return JSONResponse({"success": True, "provider": provider, "live": live, "models": models})

    async def llm_onboarding(request):
        detected = {p["name"]: p["detected"] for p in await _detect_locals()}
        if detected.get("ollama"):
            path = "Ollama is running: pick it in Chat -> provider, choose a pulled model, start talking."
            recommended = "ollama"
        elif detected.get("lmstudio"):
            path = "LM Studio is running: pick it in Chat -> provider and load a model first."
            recommended = "lm-studio"
        else:
            path = "No local LLM detected. Install Ollama (https://ollama.com) or add a cloud key in Settings."
            recommended = "none"
        return JSONResponse(
            {
                "success": True,
                "detected": detected,
                "recommended": recommended,
                "starter": path,
                "facts": [
                    "Chat talks to the backend proxy only; keys never leave this server.",
                    "Local providers are free; cloud providers need a key in Settings.",
                ],
            }
        )

    def _chat_base_allowed(base_url: str) -> bool:
        """SSRF guard: proxy only to loopback/LAN/Tailscale and the two cloud APIs."""
        import ipaddress
        from urllib.parse import urlparse

        try:
            host = urlparse(base_url).hostname or ""
        except Exception:
            return False
        if host in ("localhost", "api.openai.com", "api.anthropic.com"):
            return True
        try:
            ip = ipaddress.ip_address(host)
            return ip.is_loopback or ip.is_private
        except ValueError:
            return host.endswith(".ts.net") or host == "tauri.localhost"

    async def llm_chat(request):
        """Backend chat proxy (the ONLY path the Chat page uses). Keys never leave the server."""
        import httpx

        try:
            body = await request.json()
        except Exception:
            return JSONResponse({"success": False, "error": "invalid JSON body"}, status_code=400)
        provider = body.get("provider", {}) if isinstance(body, dict) else {}
        pid = str(provider.get("id") or provider.get("type") or "ollama")
        base_url = str(provider.get("baseUrl") or _LLM_LOCAL.get(pid, _LLM_LOCAL["ollama"])).rstrip("/")
        api_key = str(provider.get("apiKey") or "")
        model = str(body.get("model") or "llama3.2:1b")
        messages = body.get("messages") or []
        tools = body.get("tools")
        if not _chat_base_allowed(base_url):
            return JSONResponse({"success": False, "error": f"proxy target not allowed: {base_url}"}, status_code=400)
        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                if pid == "anthropic":
                    system = "\n".join(m.get("content", "") for m in messages if m.get("role") == "system")
                    convo = [m for m in messages if m.get("role") != "system"]
                    payload: dict = {"model": model, "max_tokens": 1024, "messages": convo}
                    if system:
                        payload["system"] = system
                    headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01"}
                    r = await client.post(f"{base_url}/messages", json=payload, headers=headers)
                    if r.status_code != 200:
                        return JSONResponse(
                            {"success": False, "error": f"provider {r.status_code}: {r.text[:300]}"},
                            status_code=502,
                        )
                    data = r.json()
                    blocks = data.get("content") or []
                    content = "".join(b.get("text", "") for b in blocks if b.get("type") == "text")
                    return JSONResponse({"success": True, "content": content, "toolCalls": []})
                payload = {"model": model, "messages": messages}
                if tools:
                    payload["tools"] = tools
                headers = {"Content-Type": "application/json"}
                if api_key:
                    headers["Authorization"] = f"Bearer {api_key}"
                # Local OpenAI-compatible servers (Ollama :11434, LM Studio :1234)
                # serve the chat API under /v1; cloud OpenAI bases already end in /v1.
                chat_path = (
                    "/v1/chat/completions"
                    if (pid in ("ollama", "lm-studio") and not base_url.endswith("/v1"))
                    else "/chat/completions"
                )
                r = await client.post(f"{base_url}{chat_path}", json=payload, headers=headers)
                if r.status_code != 200:
                    return JSONResponse(
                        {"success": False, "error": f"provider {r.status_code}: {r.text[:300]}"}, status_code=502
                    )
                data = r.json()
                choice = (data.get("choices") or [{}])[0]
                msg = choice.get("message") or {}
                return JSONResponse(
                    {"success": True, "content": msg.get("content") or "", "toolCalls": msg.get("tool_calls") or []}
                )
        except Exception as e:
            logger.warning("llm_chat proxy failed", error=str(e))
            return JSONResponse({"success": False, "error": f"proxy failed: {e}"}, status_code=502)

    async def shutdown(request):
        """Orderly exit: respond 200 immediately, exit ~500 ms later so writes flush."""
        import asyncio

        async def _late_exit():
            await asyncio.sleep(0.5)
            os._exit(0)

        asyncio.get_running_loop().create_task(_late_exit())
        return JSONResponse({"success": True, "message": "shutting down in ~500 ms"})

    async def activity(request):
        """Recent tool-action receipts (in-memory ring, newest first)."""
        from .tools.utils import _activity

        try:
            limit = int(request.query_params.get("limit", "100"))
        except ValueError:
            limit = 100
        items = list(_activity)[: max(1, min(limit, 100))]
        return JSONResponse({"success": True, "total": len(items), "items": items})

    asgi = app.http_app()
    asgi.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:10743",
            "http://127.0.0.1:10743",
            "http://localhost:10742",
            "http://127.0.0.1:10742",
            "http://tauri.localhost",
            "https://tauri.localhost",
            "tauri://localhost",
        ],
        allow_origin_regex=r"https?://(?:[a-zA-Z0-9-]+\.ts\.net|.*?\.tail-[a-f0-9]+\.ts\.net|tauri\.localhost|localhost|127\.0\.0\.1|192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|100\.\d{1,3}\.\d{1,3}\.\d{1,3})(?::\d+)?$|^tauri://localhost$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["mcp-session-id", "Mcp-Session-Id"],
    )
    asgi.routes.append(Route("/api/v1/diagnostics", endpoint=diagnostics))
    asgi.routes.append(Route("/api/status", endpoint=status))
    asgi.routes.append(Route("/api/capabilities", endpoint=capabilities))
    asgi.routes.append(Route("/api/skills", endpoint=skills))
    asgi.routes.append(Route("/api/llm/discover", endpoint=llm_discover))
    asgi.routes.append(Route("/api/llm/providers", endpoint=llm_providers))
    asgi.routes.append(Route("/api/llm/models", endpoint=llm_models))
    asgi.routes.append(Route("/api/llm/onboarding", endpoint=llm_onboarding))
    asgi.routes.append(Route("/api/llm/chat", endpoint=llm_chat, methods=["POST"]))
    asgi.routes.append(Route("/api/shutdown", endpoint=shutdown, methods=["POST"]))
    asgi.routes.append(Route("/api/activity", endpoint=activity))
    return asgi


def main():
    """Main entry point for the MCP server with unified transport handling."""
    from .transport import run_server

    logger.info("Starting Filesystem MCP server v2.2.0 (FastMCP 3.2+)")
    logger.info("Python path", python_path=sys.executable)
    logger.info("Working directory", cwd=str(Path.cwd()))
    logger.info("Concurrency safety: Enabled for all file operations")

    # Note: Some tools may not be available if optional dependencies are missing
    logger.info("Note: Some tools may not be available if optional dependencies are missing")

    # Use unified transport runner
    run_server(app, server_name="filesystem-mcp")


def run():
    """Entry point function for console script (Unified Transport)."""
    main()


if __name__ == "__main__":
    main()
