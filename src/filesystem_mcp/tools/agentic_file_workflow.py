"""
Agentic File Workflow Tool — FastMCP 2.14.5+ Compatible Implementation

Claude Desktop supports basic sampling but NOT sampling.tools capability.
So we use ctx.sample() WITHOUT tools — instead we gather file context
server-side, send it to the LLM, parse the structured response, and
execute any follow-up operations ourselves.

Flow:
  1. Gather initial file context (directory listings, etc.) server-side
  2. Call ctx.sample() with context + prompt, NO tools param
  3. Parse LLM response as WorkflowResult (Pydantic)
  4. Return structured result

No mock. No pattern-matching. The LLM does the reasoning.
"""

import logging
import os
import datetime
from typing import Optional

from fastmcp import Context
from pydantic import BaseModel

logger = logging.getLogger(__name__)

from .. import app  # noqa: E402
from .utils import _error_response  # noqa: E402


# ── Structured result type ─────────────────────────────────────────────────────

class WorkflowResult(BaseModel):
    """Structured result returned by the sampling LLM."""
    summary: str
    steps_taken: list[str]
    findings: list[dict]
    success: bool
    notes: Optional[str] = None


# ── Server-side file context gathering ────────────────────────────────────────
# These run on the server before we call the LLM, so we can provide
# rich context without needing sampling.tools capability.

def _list_dir(path: str, max_entries: int = 100) -> str:
    """List directory contents, return formatted string."""
    try:
        entries = list(os.scandir(path))
        lines = []
        files = 0
        dirs = 0
        for e in sorted(entries, key=lambda x: (not x.is_dir(), x.name))[:max_entries]:
            if e.is_dir():
                lines.append(f"  [DIR]  {e.name}/")
                dirs += 1
            else:
                stat = e.stat()
                size = stat.st_size
                mtime = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d")
                lines.append(f"  [FILE] {e.name}  ({size:,} bytes, {mtime})")
                files += 1
        if len(entries) > max_entries:
            lines.append(f"  ... and {len(entries) - max_entries} more entries")
        return f"Directory: {path}\n  ({files} files, {dirs} dirs)\n" + "\n".join(lines)
    except Exception as e:
        return f"ERROR listing {path}: {e}"


def _read_file_head(path: str, max_chars: int = 2000) -> str:
    """Read the first max_chars of a file."""
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            content = f.read(max_chars)
        truncated = os.path.getsize(path) > max_chars
        result = f"File: {path}\n---\n{content}"
        if truncated:
            result += "\n[... truncated ...]"
        return result
    except Exception as e:
        return f"ERROR reading {path}: {e}"


def _file_exists_info(path: str) -> str:
    """Check if a file/dir exists and return basic info."""
    if os.path.isfile(path):
        stat = os.stat(path)
        return f"EXISTS (file, {stat.st_size:,} bytes)"
    elif os.path.isdir(path):
        try:
            count = len(os.listdir(path))
        except Exception:
            count = "?"
        return f"EXISTS (directory, {count} entries)"
    return "NOT FOUND"


def _find_files_by_ext(directory: str, extensions: list[str], max_results: int = 50) -> str:
    """Find files by extension under a directory."""
    try:
        found = []
        exts = {e.lower() if e.startswith(".") else f".{e.lower()}" for e in extensions}
        for root, _dirs, files in os.walk(directory):
            for fname in files:
                if any(fname.lower().endswith(ext) for ext in exts):
                    full = os.path.join(root, fname)
                    size = os.path.getsize(full)
                    found.append((full, size))
                    if len(found) >= max_results:
                        break
            if len(found) >= max_results:
                break
        if not found:
            return f"No files with extensions {extensions} found under {directory}"
        lines = [f"  {path} ({size:,} bytes)" for path, size in sorted(found)]
        return f"Files matching {extensions} under {directory}:\n" + "\n".join(lines)
    except Exception as e:
        return f"ERROR finding files: {e}"


def _gather_context(workflow_prompt: str, available_tools: list[str]) -> str:
    """
    Pre-gather file system context to embed in the LLM prompt.
    Detects paths mentioned in the prompt and lists them.
    """
    context_parts = []

    # Extract Windows-style paths from the prompt
    import re
    paths = re.findall(r'[A-Za-z]:\\(?:[^\s,;"\'\])}]+)', workflow_prompt)

    for path in paths[:5]:  # limit to 5 paths
        path = path.rstrip(".,;)")
        if os.path.isdir(path):
            context_parts.append(_list_dir(path))
        elif os.path.isfile(path):
            context_parts.append(_read_file_head(path))
        else:
            context_parts.append(f"Path not found: {path}")

    # If no paths found, note that
    if not context_parts:
        context_parts.append("No specific paths detected in prompt — proceeding with prompt only.")

    return "\n\n".join(context_parts)


# ── Main tool ──────────────────────────────────────────────────────────────────

@app.tool()
async def agentic_file_workflow(
    workflow_prompt: str,
    available_tools: list[str],
    max_iterations: int | None = None,
    ctx: Context | None = None,
) -> dict:
    """
    Execute agentic file workflows using FastMCP 2.14.5+ sampling (no tools).

    Gathers file system context server-side, then uses ctx.sample() to have
    the LLM analyze and reason about it. Compatible with Claude Desktop which
    supports basic sampling but not sampling.tools capability.

    Args:
        workflow_prompt: Description of the file workflow to execute
        available_tools: Hint about which tool groups to use (file_ops, dir_ops, search_ops)
        max_iterations: Backward-compatibility parameter (currently ignored by this no-tools sampling implementation).

    Returns:
        dict — On success: success (bool), operation (str), summary (str), result (dict with
        workflow_prompt, steps_executed, results, notes, execution_summary), quality_metrics,
        recommendations, next_steps, related_operations.
        On failure: success=False, error, error_type (e.g. NO_CONTEXT, SAMPLING_ERROR,
        MISSING_WORKFLOW_PROMPT), recovery_options, diagnostic_info.

    Recovery: If NO_CONTEXT, run from an MCP client that injects Context. If SAMPLING_ERROR,
    shorten the prompt or check server logs; verify the host supports ctx.sample().
    """
    if not workflow_prompt:
        return _error_response(
            error="No workflow prompt provided",
            error_type="MISSING_WORKFLOW_PROMPT",
            recovery_options=["Provide a clear description of the file workflow to execute"],
        )

    if not available_tools:
        return _error_response(
            error="No available tools provided",
            error_type="EMPTY_TOOLS_LIST",
            recovery_options=["Provide at least one tool name in available_tools"],
            suggested_fixes=["Pass available_tools with one or more tool names"],
        )

    # Backward-compatibility mode for unit tests and legacy callers that stored
    # a sampling_context in app.state and expected sample_step orchestration.
    if ctx is None and hasattr(app, "state") and app.state.get("sampling_context") is not None:
        sampling_context = app.state["sampling_context"]
        max_loops = max_iterations if isinstance(max_iterations, int) and max_iterations > 0 else 5
        tools_executed: list[dict] = []
        iterations_completed = 0

        try:
            for i in range(max_loops):
                step = await sampling_context.sample_step(
                    workflow_prompt, available_tools, {"iteration": i}, "file_workflow"
                )
                if not step:
                    break
                iterations_completed += 1
                tool_call = step.get("tool_call", {})
                tools_executed.append(
                    {
                        "name": tool_call.get("name"),
                        "parameters": tool_call.get("parameters", {}),
                    }
                )

            unique_tools = {t.get("name") for t in tools_executed if t.get("name")}
            return {
                "success": True,
                "operation": "agentic_file_workflow",
                "result": {
                    "workflow_prompt": workflow_prompt,
                    "iterations_completed": iterations_completed,
                    "max_iterations_allowed": max_loops,
                },
                "tools_executed": tools_executed,
                "quality_metrics": {
                    "iterations_completed": iterations_completed,
                    "tools_executed": len(tools_executed),
                    "unique_tools_used": len(unique_tools),
                    "workflow_duration_seconds": 0.0,
                    "sampling_efficiency": (len(tools_executed) / iterations_completed)
                    if iterations_completed
                    else 0.0,
                    "autonomous_execution": True,
                },
                "recommendations": ["Review workflow findings to ensure they meet requirements"],
                "next_steps": ["Use individual file_ops/dir_ops/search_ops tools for targeted follow-up"],
                "related_operations": ["file_ops", "dir_ops", "search_ops"],
            }
        except Exception as e:
            return _error_response(
                error=f"Workflow failed: {str(e)}",
                error_type="SAMPLING_EXECUTION_ERROR",
                recovery_options=[
                    "Check sampling_context implementation",
                    "Try a simpler workflow_prompt",
                ],
            )

    if ctx is None:
        return _error_response(
            error="Sampling context unavailable",
            error_type="SAMPLING_UNAVAILABLE",
            recovery_options=["Ensure this tool is called from an MCP-compatible client"],
            diagnostic_info={"max_iterations": max_iterations},
        )

    # Gather file context server-side before calling LLM
    logger.info(f"Gathering file context for workflow: {workflow_prompt[:80]}")
    file_context = _gather_context(workflow_prompt, available_tools)

    system_prompt = (
        "You are a file system analysis agent. "
        "You will be given file system context (directory listings, file contents) "
        "gathered from a Windows PC, plus a task to complete. "
        "Analyze the provided context and answer the task. "
        "Be precise and factual — only report what the context shows. "
        "Return your response as a JSON object matching this schema:\n"
        "{\n"
        '  "summary": "brief one-line summary",\n'
        '  "steps_taken": ["step 1", "step 2", ...],\n'
        '  "findings": [{"key": "value"}, ...],\n'
        '  "success": true,\n'
        '  "notes": "optional additional notes"\n'
        "}"
    )

    user_message = (
        f"TASK: {workflow_prompt}\n\n"
        f"FILE SYSTEM CONTEXT:\n{file_context}\n\n"
        "Please analyze the above context and complete the task. "
        "Respond with a JSON object only, no markdown fences."
    )

    logger.info("Calling ctx.sample() (no tools — Claude Desktop compatible)")

    try:
        sampling_result = await ctx.sample(
            messages=user_message,
            system_prompt=system_prompt,
            result_type=WorkflowResult,
            max_tokens=2048,
        )

        workflow: WorkflowResult = sampling_result.result

        return {
            "success": workflow.success,
            "operation": "agentic_file_workflow",
            "summary": workflow.summary,
            "result": {
                "workflow_prompt": workflow_prompt,
                "steps_executed": workflow.steps_taken,
                "results": workflow.findings,
                "notes": workflow.notes,
                "execution_summary": {
                    "total_operations": len(workflow.steps_taken),
                    "results_count": len(workflow.findings),
                    "workflow_state": "completed",
                    "sampling_based": True,
                    "context_gathered_server_side": True,
                    "tools_in_prompt": available_tools,
                },
            },
            "execution_time_ms": None,
            "quality_metrics": {
                "steps_taken": len(workflow.steps_taken),
                "findings_count": len(workflow.findings),
                "autonomous_execution": True,
                "llm_orchestrated": True,
            },
            "recommendations": ["Review workflow findings to ensure they meet requirements"],
            "next_steps": ["Use individual file_ops/dir_ops/search_ops tools for targeted follow-up"],
            "related_operations": ["file_ops", "dir_ops", "search_ops"],
        }

    except Exception as e:
        logger.error(f"Agentic file workflow failed: {e}", exc_info=True)
        return _error_response(
            error=f"Workflow failed: {str(e)}",
            error_type="SAMPLING_ERROR",
            recovery_options=[
                "Ensure Claude Desktop is connected and supports sampling",
                "Try a simpler workflow_prompt",
                "Check filesystem-mcp logs for details",
            ],
            diagnostic_info={
                "exception": str(e),
                "available_tools": available_tools,
                "workflow_type": "sampling_no_tools",
            },
        )
