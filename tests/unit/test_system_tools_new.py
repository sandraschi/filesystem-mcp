"""
Unit tests for system tools.

Tests help system and status reporting functions.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock

from filesystem_mcp.tools.system_tools import (
    get_help,
    get_system_status
)


class TestGetHelp:
    """Test the get_help function."""

    @pytest.mark.asyncio
    async def test_get_help_overview(self):
        """Test getting help overview."""
        result = await get_help.run({})

        assert result.content["success"] is True
        assert "categories" in result.content["help_info"]
        assert len(result.content["help_info"]["categories"]) == 4

    @pytest.mark.asyncio
    async def test_get_help_category(self):
        """Test getting help for a specific category."""
        result = await get_help.run({"category": "file_operations"})

        assert result.content["success"] is True
        assert "help_info" in result.content
        assert result.content["help_info"]["category"] == "file_operations"
        assert "tools" in result.content["help_info"]

    @pytest.mark.asyncio
    async def test_get_help_tool(self):
        """Test getting help for a specific tool."""
        result = await get_help.run({
            "category": "file_operations",
            "tool_name": "read_file"
        })

        assert result.content["success"] is True
        assert "help_info" in result.content
        assert result.content["help_info"]["name"] == "file_operations.read_file"
        assert "description" in result.content["help_info"]
        assert "parameters" in result.content["help_info"]

    @pytest.mark.asyncio
    async def test_get_help_invalid_category(self):
        """Test getting help for invalid category."""
        result = await get_help.run({"category": "invalid_category"})

        assert result.content["success"] is False
        assert "error" in result.content
        assert "not found" in result.content["error"]

    @pytest.mark.asyncio
    async def test_get_help_invalid_tool(self):
        """Test getting help for invalid tool in valid category."""
        result = await get_help.run({
            "category": "file_operations",
            "tool_name": "invalid_tool"
        })

        assert result.content["success"] is False
        assert "error" in result.content
        assert "not found" in result.content["error"]


class TestGetSystemStatus:
    """Test the get_system_status function."""

    @pytest.mark.asyncio
    async def test_get_system_status_success(self):
        """Test getting system status successfully."""
        result = await get_system_status.run({})

        assert result.content["success"] is True
        assert "system_status" in result.content
        assert "timestamp" in result.content["system_status"]
        assert "system_info" in result.content["system_status"]
        assert "server_health" in result.content["system_status"]

    @pytest.mark.asyncio
    async def test_get_system_status_with_processes(self):
        """Test getting system status with process information."""
        result = await get_system_status.run({"include_processes": True})

        assert result.content["success"] is True
        assert "system_status" in result.content
        # Process info might not be available on all systems
        if "top_processes" in result.content["system_status"]:
            assert isinstance(result.content["system_status"]["top_processes"], list)

    @pytest.mark.asyncio
    async def test_get_system_status_with_disk(self):
        """Test getting system status with disk information."""
        result = await get_system_status.run({"include_disk": True})

        assert result.content["success"] is True
        assert "system_status" in result.content
        # Disk info should be available
        assert "disk" in result.content["system_status"]
        assert isinstance(result.content["system_status"]["disk"], list)

    @pytest.mark.asyncio
    async def test_get_system_status_no_processes(self):
        """Test getting system status without process information."""
        result = await get_system_status.run({"include_processes": False})

        assert result.content["success"] is True
        assert "system_status" in result.content
        # Should not include process info when disabled
        assert "top_processes" not in result.content["system_status"]
