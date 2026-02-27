"""
Unit tests for portmanteau file operations with enhanced FastMCP 2.14.3+ responses.

Tests file_ops portmanteau tool with conversational returns and quality metrics.
"""

import pytest

from filesystem_mcp.tools.portmanteau_file import file_ops
from tests.conftest import (
    assert_enhanced_error_response,
    assert_enhanced_success_response,
)


def call_file_ops(**kwargs):
    """Helper to call file_ops tool directly."""
    # For testing, we'll call the main portmanteau function
    # This tests the full operation dispatch logic
    import asyncio

    from filesystem_mcp.tools.portmanteau_directory import dir_ops as dir_ops_tool

    # Import the main tool functions
    from filesystem_mcp.tools.portmanteau_file import file_ops as file_ops_tool

    operation = kwargs.get("operation")

    # Route to the appropriate tool based on operation
    if operation in ["read_file", "write_file", "edit_file", "move_file", "read_file_lines",
                     "read_multiple_files", "file_exists", "get_file_info", "head_file", "tail_file"]:
        return asyncio.run(file_ops_tool(operation=operation, **{k: v for k, v in kwargs.items() if k != "operation"}))
    elif operation in ["list_directory", "create_directory", "remove_directory", "directory_tree",
                       "calculate_directory_size", "find_empty_directories"]:
        return asyncio.run(dir_ops_tool(operation=operation, **{k: v for k, v in kwargs.items() if k != "operation"}))
    else:
        # For invalid operations, call file_ops which will return error
        return asyncio.run(file_ops_tool(operation=operation, **{k: v for k, v in kwargs.items() if k != "operation"}))


# Remove old parse function - using conftest.parse_enhanced_response instead


class TestFileOpsPortmanteau:
    """Test the file_ops portmanteau tool with enhanced responses."""

    def test_read_file_success_enhanced(self, temp_file):
        """Test successful file reading with enhanced response."""
        result = call_file_ops(
            operation="read_file",
            path=str(temp_file)
        )

        assert_enhanced_success_response(result, ["path", "content", "encoding"])
        assert result["result"]["content"] == "Test content"
        assert result["result"]["encoding"] == "utf-8"
        assert "line_count" in result["quality_metrics"]
        assert "file_size_mb" in result["quality_metrics"]
        assert len(result["recommendations"]) > 0

    @pytest.mark.asyncio
    async def test_read_file_not_found_enhanced(self, temp_dir):
        """Test reading non-existent file with enhanced error response."""
        nonexistent = temp_dir / "nonexistent.txt"
        result = await file_ops(
            operation="read_file",
            path=str(nonexistent)
        )

        assert_enhanced_error_response(result)
        assert result["error_type"] == "file_not_found"
        assert len(result["recovery_options"]) > 0
        assert "diagnostic_info" in result

    @pytest.mark.asyncio
    async def test_write_file_success_enhanced(self, temp_dir):
        """Test successful file writing with enhanced response."""
        test_path = temp_dir / "new_file.txt"
        content = "Hello, World!"

        result = await file_ops(
            operation="write_file",
            path=str(test_path),
            content=content
        )

        assert_enhanced_success_response(result)
        assert test_path.exists()
        assert test_path.read_text() == content
        assert result["operation"] == "write_file"
        assert "execution_time_ms" in result

    @pytest.mark.asyncio
    async def test_list_directory_enhanced(self, temp_dir):
        """Test directory listing with enhanced response."""
        # Create test files
        (temp_dir / "file1.txt").write_text("content1")
        (temp_dir / "file2.txt").write_text("content2")
        subdir = temp_dir / "subdir"
        subdir.mkdir()
        (subdir / "file3.txt").write_text("content3")

        result = await file_ops(
            operation="list_directory",
            path=str(temp_dir)
        )

        assert_enhanced_success_response(result, ["items", "total_items"])
        assert result["result"]["total_items"] >= 3
        assert len(result["result"]["items"]) >= 3
        assert "quality_metrics" in result
        assert len(result["next_steps"]) > 0

    @pytest.mark.asyncio
    async def test_file_exists_success_enhanced(self, temp_file):
        """Test file existence check with enhanced response."""
        result = await file_ops(
            operation="file_exists",
            path=str(temp_file)
        )

        assert_enhanced_success_response(result, ["exists", "type"])
        assert result["result"]["exists"] is True
        assert result["result"]["type"] == "file"

    @pytest.mark.asyncio
    async def test_get_file_info_enhanced(self, temp_file):
        """Test file info retrieval with enhanced response."""
        result = await file_ops(
            operation="get_file_info",
            path=str(temp_file)
        )

        assert_enhanced_success_response(result, ["type", "size"])
        assert result["result"]["type"] == "file"
        assert result["result"]["size"] == 12  # "Test content" length
        assert "created" in result["result"]
        assert "modified" in result["result"]
        assert result["quality_metrics"]["content_type"] == "text"

    @pytest.mark.asyncio
    async def test_edit_file_success_enhanced(self, temp_file):
        """Test file editing with enhanced response."""
        original_content = "Hello, World!\nThis is a test file."
        temp_file.write_text(original_content)

        result = await file_ops(
            operation="edit_file",
            path=str(temp_file),
            old_string="World",
            new_string="Universe"
        )

        assert_enhanced_success_response(result)
        assert result["operation"] == "edit_file"
        assert result["result"]["occurrences_replaced"] == 1
        assert result["quality_metrics"]["file_size_before"] == len(original_content)

        # Verify file was actually changed
        new_content = temp_file.read_text()
        assert "Hello, Universe!" in new_content
        assert "World" not in new_content

    def test_move_file_success_enhanced(self, temp_file, temp_dir):
        """Test file moving with enhanced response."""
        dest_path = temp_dir / "moved_file.txt"

        result = call_file_ops(
            operation="move_file",
            path=str(temp_file),
            destination_path=str(dest_path)
        )

        assert_enhanced_success_response(result, ["path", "destination_path"])
        assert dest_path.exists()
        assert not temp_file.exists()
        assert result["operation"] == "move_file"

    def test_read_file_lines_enhanced(self, temp_file):
        """Test reading specific file lines with enhanced response."""
        # Create a multi-line file
        content = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5"
        temp_file.write_text(content)

        result = call_file_ops(
            operation="read_file_lines",
            path=str(temp_file),
            offset=1,
            limit=3
        )

        assert_enhanced_success_response(result)
        assert "lines" in result["result"]
        assert len(result["result"]["lines"]) <= 3
        assert result["quality_metrics"]["line_count"] == 5

    def test_head_file_enhanced(self, temp_file):
        """Test reading file head with enhanced response."""
        # Create a multi-line file
        content = "\n".join(f"Line {i}" for i in range(1, 21))  # 20 lines
        temp_file.write_text(content)

        result = call_file_ops(
            operation="head_file",
            path=str(temp_file),
            lines=5
        )

        assert_enhanced_success_response(result)
        assert len(result["result"]["lines"]) == 5
        assert result["result"]["lines"][0] == "Line 1"
        assert result["quality_metrics"]["line_count"] == 20

    def test_tail_file_enhanced(self, temp_file):
        """Test reading file tail with enhanced response."""
        # Create a multi-line file
        content = "\n".join(f"Line {i}" for i in range(1, 21))  # 20 lines
        temp_file.write_text(content)

        result = call_file_ops(
            operation="tail_file",
            path=str(temp_file),
            lines=5
        )

        assert_enhanced_success_response(result)
        assert len(result["result"]["lines"]) == 5
        assert result["result"]["lines"][-1] == "Line 20"
        assert result["quality_metrics"]["line_count"] == 20


    def test_invalid_operation_enhanced(self, temp_file):
        """Test invalid operation with clarification response."""
        result = call_file_ops(
            operation="invalid_operation",
            path=str(temp_file)
        )

        assert_enhanced_error_response(result)
        assert "unsupported_operation" in result["error_type"]

    def test_missing_required_params_enhanced(self):
        """Test missing required parameters with clarification."""
        result = call_file_ops(
            operation="read_file"
            # Missing required 'path' parameter
        )

        # Should get clarification response for missing path
        assert result["status"] == "clarification_needed"
        assert "path" in str(result["ambiguities"]).lower()

    def test_quality_metrics_tracking(self, temp_file):
        """Test that quality metrics are properly tracked."""
        result = call_file_ops(
            operation="read_file",
            path=str(temp_file)
        )

        assert_enhanced_success_response(result)
        metrics = result["quality_metrics"]

        # Should have content analysis metrics
        assert "line_count" in metrics
        assert "file_size_mb" in metrics
        assert "encoding_detected" in metrics
        assert "content_type" in metrics

        # Should have recommendations based on file analysis
        assert len(result["recommendations"]) > 0
        assert len(result["next_steps"]) > 0
        assert len(result["related_operations"]) > 0

    def test_performance_tracking(self, temp_file):
        """Test that performance metrics are tracked."""
        result = call_file_ops(
            operation="read_file",
            path=str(temp_file)
        )

        assert_enhanced_success_response(result)
        assert "execution_time_ms" in result
        assert isinstance(result["execution_time_ms"], int)
        assert result["execution_time_ms"] >= 0
