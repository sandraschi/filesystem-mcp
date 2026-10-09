"""Prompt templates for filesystem-mcp.

Static MCP prompt templates (no sampling): copy-shape workflows agents can
fetch via ``prompts/get`` and fill in. Registered on import; the package
``__init__`` imports this module right after the tool modules.
"""

from .tools.utils import _get_app


def _register_prompts() -> None:
    app = _get_app()

    @app.prompt(
        name="file-workflow-guide",
        description="Copy-shape workflow for safe file operations (read/edit/write with backups).",
    )
    async def file_workflow_guide(operation: str = "read_file") -> str:
        """Guide an agent through a concurrency-safe file workflow."""
        return (
            f"You are working with filesystem-mcp file tools.\n\n"
            f"Requested operation: {operation}\n\n"
            f"Rules:\n"
            f"1. Explore first: dir_ops(operation='list_directory', path='<dir>') before reading.\n"
            f"2. Read before editing: file_ops(operation='read_file', path='<file>').\n"
            f"3. Prefer file_ops(operation='write_file') for new files (atomic + locked).\n"
            f"4. For edits use edit_file with old_string/new_string; a timestamped .bak is kept.\n"
            f"5. Large files: read_file_lines with offset/limit, or head_file/tail_file.\n"
            f"6. If a call returns status clarification_needed, answer the suggested_questions.\n"
        )

    @app.prompt(
        name="container-triage",
        description="Copy-shape workflow for Docker container triage (list, inspect, logs).",
    )
    async def container_triage() -> str:
        """Guide an agent through container triage."""
        return (
            "You are triaging Docker containers with filesystem-mcp.\n\n"
            "Steps:\n"
            "1. container_ops(operation='list_containers', show_stats=True) for the fleet view.\n"
            "2. container_ops(operation='get_container', container_id='<id>') for a suspect.\n"
            "3. container_ops(operation='container_logs', container_id='<id>', tail=100) for errors.\n"
            "4. infra_ops(operation='list_images') to check for stale/duplicate images.\n"
            "5. compose_ps / compose_logs for Compose-managed stacks.\n"
            "Do NOT restart or remove anything without explicit user confirmation."
        )

    @app.prompt(
        name="system-health-check",
        description="Copy-shape workflow for a host health pass (CPU, memory, disk, top processes).",
    )
    async def system_health_check() -> str:
        """Guide an agent through a host health pass."""
        return (
            "You are checking host health with filesystem-mcp monitoring tools.\n\n"
            "Steps:\n"
            "1. monitor_get_system_status(include_processes=False) for the snapshot.\n"
            "2. monitor_get_resource_usage() if CPU or memory look hot.\n"
            "3. monitor_get_process_info(filter_pattern='<suspect>', max_processes=20) to drill in.\n"
            "4. monitor_get_disk_usage() when disk_percent exceeds 85.\n"
            "Report numbers, not adjectives; suggest one next action."
        )


_register_prompts()
