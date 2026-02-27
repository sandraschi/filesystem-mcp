"""
Unit tests for system tools.

Tests help system and status reporting functions.
"""

import json

import pytest
from filesystem_mcp.tools.portmanteau_host import host_ops
from filesystem_mcp.tools.portmanteau_monitoring import monitor_ops


def parse_tool_result(result):
    """Parse the JSON content from a ToolResult."""
    return json.loads(result.content[0].text)


class TestGetHelp:
    """Test the get_help function."""

    @pytest.mark.asyncio
    async def test_get_help_overview(self):
        """Test getting help overview."""
        result = await host_ops.run({"operation": "get_help"})

        data = parse_tool_result(result)
        assert data["success"] is True
        assert "categories" in data["help_info"]
        assert len(data["help_info"]["categories"]) == 4

    @pytest.mark.asyncio
    async def test_get_help_category(self):
        """Test getting help for a specific category."""
        result = await host_ops.run(
            {"operation": "get_help", "category": "file_operations"}
        )

        data = parse_tool_result(result)
        assert data["success"] is True
        assert "help_info" in data
        assert data["help_info"]["category"] == "file_operations"
        assert "tools" in data["help_info"]

    @pytest.mark.asyncio
    async def test_get_help_tool(self):
        """Test getting help for a specific tool."""
        result = await host_ops.run(
            {
                "operation": "get_help",
                "category": "file_operations",
                "tool_name": "read_file",
            }
        )

        data = parse_tool_result(result)
        assert data["success"] is True
        assert "help_info" in data
        assert data["help_info"]["name"] == "file_operations.read_file"
        assert "description" in data["help_info"]
        assert "parameters" in data["help_info"]

    @pytest.mark.asyncio
    async def test_get_help_invalid_category(self):
        """Test getting help for invalid category."""
        result = await host_ops.run(
            {"operation": "get_help", "category": "invalid_category"}
        )

        data = parse_tool_result(result)
        assert data["success"] is False
        assert "error" in data
        assert "not found" in data["error"]

    @pytest.mark.asyncio
    async def test_get_help_invalid_tool(self):
        """Test getting help for invalid tool in valid category."""
        result = await host_ops.run(
            {
                "operation": "get_help",
                "category": "file_operations",
                "tool_name": "invalid_tool",
            }
        )

        data = parse_tool_result(result)
        assert data["success"] is False
        assert "error" in data
        assert "not found" in data["error"]


class TestGetSystemStatus:
    """Test the get_system_status function."""

    @pytest.mark.asyncio
    async def test_get_system_status_success(self):
        """Test getting system status successfully."""
        result = await monitor_ops.run({"operation": "get_system_status"})

        data = parse_tool_result(result)
        assert data["success"] is True
        assert "system_status" in data
        assert "timestamp" in data["system_status"]
        assert "system_info" in data["system_status"]
        assert "server_health" in data["system_status"]

    @pytest.mark.asyncio
    async def test_get_system_status_with_processes(self):
        """Test getting system status with process information."""
        result = await monitor_ops.run(
            {"operation": "get_system_status", "include_processes": True}
        )

        data = parse_tool_result(result)
        assert data["success"] is True
        assert "system_status" in data
        # Process info might not be available on all systems
        if "top_processes" in data["system_status"]:
            assert isinstance(data["system_status"]["top_processes"], list)

    @pytest.mark.asyncio
    async def test_get_system_status_with_disk(self):
        """Test getting system status with disk information."""
        result = await monitor_ops.run(
            {"operation": "get_system_status", "include_disk": True}
        )

        data = parse_tool_result(result)
        assert data["success"] is True
        assert "system_status" in data
        # Disk info should be available
        assert "disk" in data["system_status"]
        assert isinstance(data["system_status"]["disk"], list)

    @pytest.mark.asyncio
    async def test_get_system_status_no_processes(self):
        """Test getting system status without process information."""
        result = await monitor_ops.run(
            {"operation": "get_system_status", "include_processes": False}
        )

        data = parse_tool_result(result)
        assert data["success"] is True
        assert "system_status" in data
        # Should not include process info when disabled
        assert "top_processes" not in data["system_status"]
