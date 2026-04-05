"""
Unit tests for system tools.

Tests help system and status reporting functions.
"""

import json

import pytest
from filesystem_mcp.tools.portmanteau_host import host_ops
from filesystem_mcp.tools.portmanteau_monitoring import (
    monitor_get_system_status,
)


def parse_tool_result(result):
    """Parse the JSON content from a ToolResult or plain dict."""
    if isinstance(result, dict):
        return result
    return json.loads(result.content[0].text)


class TestGetHelp:
    """Test the get_help function."""

    @pytest.mark.asyncio
    async def test_get_help_overview(self):
        """Test getting help overview."""
        result = await host_ops(operation="get_help")

        data = parse_tool_result(result)
        assert data["success"] is True
        assert "categories" in data["result"]
        assert len(data["result"]["categories"]) >= 4

    @pytest.mark.asyncio
    async def test_get_help_category(self):
        """Test getting help for a specific category."""
        result = await host_ops(operation="get_help", category="filesystem")

        data = parse_tool_result(result)
        assert data["success"] is True
        assert "result" in data
        assert data["result"]["category"] == "filesystem"
        assert "tools" in data["result"]

    @pytest.mark.asyncio
    async def test_get_help_tool(self):
        """Test getting help for a specific tool."""
        result = await host_ops(operation="get_help", tool_name="file_ops")

        data = parse_tool_result(result)
        assert data["success"] is True
        assert "result" in data
        assert data["result"]["tool"] == "file_ops"
        assert "description" in data["result"]
        assert "operations" in data["result"]

    @pytest.mark.asyncio
    async def test_get_help_invalid_category(self):
        """Test getting help for invalid category."""
        result = await host_ops(operation="get_help", category="invalid_category")

        data = parse_tool_result(result)
        assert data["success"] is False
        assert "error" in data
        assert "Unknown category" in data["error"]

    @pytest.mark.asyncio
    async def test_get_help_invalid_tool(self):
        """Test getting help for invalid tool in valid category."""
        result = await host_ops(operation="get_help", tool_name="invalid_tool")

        data = parse_tool_result(result)
        assert data["success"] is False
        assert "error" in data
        assert "Unknown tool" in data["error"]


class TestGetSystemStatus:
    """Test the get_system_status function."""

    @pytest.mark.asyncio
    async def test_get_system_status_success(self):
        """Test getting system status successfully."""
        result = await monitor_get_system_status()

        data = parse_tool_result(result)
        assert data["success"] is True
        assert "result" in data
        assert "timestamp" in data["result"]
        assert "system" in data["result"]
        assert "memory" in data["result"]

    @pytest.mark.asyncio
    async def test_get_system_status_with_processes(self):
        """Test getting system status with process information."""
        result = await monitor_get_system_status(include_processes=True)

        data = parse_tool_result(result)
        assert data["success"] is True
        assert "result" in data
        if "processes" in data["result"]:
            assert isinstance(data["result"]["processes"], list)

    @pytest.mark.asyncio
    async def test_get_system_status_with_disk(self):
        """Test getting system status with disk information."""
        result = await monitor_get_system_status(include_disk=True)

        data = parse_tool_result(result)
        assert data["success"] is True
        assert "result" in data
        assert "disk" in data["result"]
        assert isinstance(data["result"]["disk"], dict)

    @pytest.mark.asyncio
    async def test_get_system_status_no_processes(self):
        """Test getting system status without process information."""
        result = await monitor_get_system_status(include_processes=False)

        data = parse_tool_result(result)
        assert data["success"] is True
        assert "result" in data
        assert "processes" not in data["result"]
