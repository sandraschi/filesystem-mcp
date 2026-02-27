"""
Unit tests for enhanced FastMCP 2.14.3+ response patterns.

Tests conversational tool returns, error recovery, and clarification responses.
"""

from filesystem_mcp.tools.utils import (
    _clarification_response,
    _error_response,
    _interactive_response,
    _progress_response,
    _success_response,
)


class TestEnhancedSuccessResponse:
    """Test enhanced success response patterns."""

    def test_basic_success_response(self):
        """Test basic success response structure."""
        result = {"data": "test"}
        response = _success_response(result=result, operation="test_op")

        assert response["success"] is True
        assert response["operation"] == "test_op"
        assert response["result"] == result
        # execution_time_ms is optional when not provided
        assert "quality_metrics" in response
        assert "recommendations" in response
        assert "next_steps" in response
        assert "related_operations" in response
        assert "timestamp" in response

    def test_success_response_with_all_metadata(self):
        """Test success response with comprehensive metadata."""
        result = {"files_processed": 10}
        recommendations = ["Consider backup", "Review results"]
        next_steps = ["Verify changes", "Run tests"]
        related_ops = ["file_ops", "dir_ops"]

        response = _success_response(
            result=result,
            operation="batch_process",
            execution_time_ms=1500,
            quality_metrics={"efficiency": 0.95},
            recommendations=recommendations,
            next_steps=next_steps,
            related_operations=related_ops
        )

        assert response["success"] is True
        assert response["operation"] == "batch_process"
        assert response["result"]["files_processed"] == 10
        assert response["execution_time_ms"] == 1500
        assert response["quality_metrics"]["efficiency"] == 0.95
        assert response["recommendations"] == recommendations
        assert response["next_steps"] == next_steps
        assert response["related_operations"] == related_ops

    def test_success_response_file_operation(self):
        """Test success response for file operations."""
        file_result = {
            "path": "/test/file.txt",
            "content": "test content",
            "size_bytes": 12,
            "line_count": 1,
            "file_info": {"extension": ".txt", "readable": True}
        }

        response = _success_response(
            result=file_result,
            operation="read_file",
            execution_time_ms=50,
            quality_metrics={
                "line_count": 1,
                "file_size_mb": 0.0,
                "encoding_detected": "utf-8",
                "content_type": "text"
            },
            recommendations=["File is small - quick processing"],
            next_steps=["Use content for analysis"],
            related_operations=["grep_file", "get_file_info"]
        )

        assert response["success"] is True
        assert response["operation"] == "read_file"
        assert response["result"]["path"] == "/test/file.txt"
        assert response["execution_time_ms"] == 50
        assert response["quality_metrics"]["content_type"] == "text"
        assert len(response["recommendations"]) > 0
        assert len(response["next_steps"]) > 0
        assert "grep_file" in response["related_operations"]


class TestEnhancedErrorResponse:
    """Test enhanced error response patterns."""

    def test_basic_error_response(self):
        """Test basic error response structure."""
        response = _error_response(
            error="File not found",
            error_type="file_not_found"
        )

        assert response["success"] is False
        assert response["error"] == "File not found"
        assert response["error_type"] == "file_not_found"
        assert "recovery_options" in response
        assert "diagnostic_info" in response
        assert "timestamp" in response

    def test_error_response_with_recovery(self):
        """Test error response with detailed recovery options."""
        response = _error_response(
            error="Permission denied accessing system directory",
            error_type="permission_denied",
            recovery_options=[
                "Check file permissions",
                "Run with elevated privileges",
                "Use alternative location"
            ],
            suggested_fixes=[
                "chmod +r file.txt",
                "Use sudo for system files"
            ],
            diagnostic_info={
                "path": "/etc/passwd",
                "operation": "read",
                "platform": "linux"
            },
            estimated_resolution_time="2-5 minutes"
        )

        assert response["success"] is False
        assert response["error_type"] == "permission_denied"
        assert len(response["recovery_options"]) == 3
        assert len(response["suggested_fixes"]) == 2
        assert response["diagnostic_info"]["platform"] == "linux"
        assert response["estimated_resolution_time"] == "2-5 minutes"

    def test_error_response_io_error(self):
        """Test error response for I/O operations."""
        response = _error_response(
            error="Cannot decode file as UTF-8",
            error_type="encoding_error",
            recovery_options=[
                "Try different encoding (latin-1, cp1252)",
                "Check if file is binary",
                "Use binary read mode"
            ],
            suggested_fixes=[
                "Specify encoding parameter",
                "Use 'latin-1' for binary-like text"
            ]
        )

        assert response["error_type"] == "encoding_error"
        assert "encoding" in str(response["recovery_options"]).lower()
        assert "binary" in str(response["suggested_fixes"]).lower()


class TestClarificationResponse:
    """Test clarification response patterns."""

    def test_basic_clarification_response(self):
        """Test basic clarification response structure."""
        response = _clarification_response(
            ambiguities=["operation parameter unclear"],
            suggested_questions=[
                "What operation would you like to perform?",
                "Did you mean 'read_file' or 'list_directory'?"
            ]
        )

        assert response["status"] == "clarification_needed"
        assert "operation parameter unclear" in response["ambiguities"]
        assert len(response["suggested_questions"]) == 2
        assert "timestamp" in response

    def test_clarification_with_options(self):
        """Test clarification response with multiple choice options."""
        operations = ["read_file", "write_file", "list_directory", "delete_file"]
        response = _clarification_response(
            ambiguities=["Unclear which file operation to perform"],
            options={
                "operation": operations,
                "confirmation": ["yes", "no", "cancel"]
            },
            suggested_questions=[
                "Which file operation do you need?",
                "Would you like to read, write, or list files?"
            ],
            preserved_context={"attempted_path": "/tmp/test.txt"}
        )

        assert response["status"] == "clarification_needed"
        assert response["options"]["operation"] == operations
        assert response["preserved_context"]["attempted_path"] == "/tmp/test.txt"


class TestProgressResponse:
    """Test progress response patterns."""

    def test_basic_progress_response(self):
        """Test basic progress response structure."""
        response = _progress_response(
            operation="file_analysis",
            current=5,
            total=10,
            phase="analyzing_files"
        )

        assert response["status"] == "in_progress"
        assert response["operation"] == "file_analysis"
        assert response["progress"]["current"] == 5
        assert response["progress"]["total"] == 10
        assert response["progress"]["percentage"] == 50.0
        assert response["phase"] == "analyzing_files"
        assert "timestamp" in response

    def test_progress_response_with_details(self):
        """Test progress response with detailed information."""
        details = {
            "current_file": "data.json",
            "files_processed": 5,
            "total_files": 10,
            "bytes_processed": 1024000
        }

        response = _progress_response(
            operation="batch_file_processing",
            current=5,
            total=10,
            phase="processing_files",
            estimated_completion="2 minutes remaining",
            details=details
        )

        assert response["operation"] == "batch_file_processing"
        assert response["progress"]["percentage"] == 50.0
        assert response["estimated_completion"] == "2 minutes remaining"
        assert response["details"]["current_file"] == "data.json"


class TestInteractiveResponse:
    """Test interactive response patterns."""

    def test_basic_interactive_response(self):
        """Test basic interactive response structure."""
        options = ["proceed", "cancel", "retry"]
        response = _interactive_response(
            message="File already exists. What would you like to do?",
            options=options
        )

        assert response["status"] == "interactive"
        assert "File already exists" in response["message"]
        assert response["options"] == options
        assert "timestamp" in response

    def test_interactive_response_with_context(self):
        """Test interactive response with context and follow-ups."""
        response = _interactive_response(
            message="Multiple files found. Which one to process?",
            options=["file1.txt", "file2.txt", "all", "cancel"],
            context={"search_pattern": "*.txt", "directory": "/tmp"},
            follow_up_operations=[
                "read_file(path='file1.txt')",
                "read_file(path='file2.txt')",
                "batch_process_files()"
            ]
        )

        assert response["status"] == "interactive"
        assert response["context"]["search_pattern"] == "*.txt"
        assert len(response["follow_up_operations"]) == 3


class TestResponseIntegration:
    """Test integration of different response patterns."""

    def test_workflow_error_to_clarification(self):
        """Test error response that leads to clarification."""
        # First error response
        error_response = _error_response(
            error="Ambiguous file operation requested",
            error_type="ambiguous_request",
            recovery_options=["Provide more specific operation details"],
            suggested_fixes=["Specify exact file operation needed"]
        )

        assert error_response["success"] is False
        assert "ambiguous" in error_response["error_type"]

        # Follow-up clarification response
        clarification_response = _clarification_response(
            ambiguities=["File operation not clearly specified"],
            options={
                "operation": ["read_file", "write_file", "edit_file", "list_directory"]
            },
            suggested_questions=["What specific file operation do you need?"],
            preserved_context={"original_request": "process file"}
        )

        assert clarification_response["status"] == "clarification_needed"
        assert "operation" in clarification_response["options"]

    def test_success_with_progress_context(self):
        """Test success response that includes progress context."""
        # Progress update
        progress_response = _progress_response(
            operation="file_backup",
            current=7,
            total=10,
            phase="copying_files",
            estimated_completion="30 seconds"
        )

        assert progress_response["progress"]["percentage"] == 70.0

        # Final success response
        success_response = _success_response(
            result={
                "files_backed_up": 10,
                "total_size_mb": 50.5,
                "backup_location": "/backup/2024-01-22"
            },
            operation="file_backup",
            execution_time_ms=45000,
            quality_metrics={
                "success_rate": 1.0,
                "compression_ratio": 0.8,
                "verification_passed": True
            },
            recommendations=[
                "Verify backup integrity",
                "Update backup rotation policy"
            ],
            next_steps=[
                "Test backup restoration",
                "Update documentation"
            ]
        )

        assert success_response["success"] is True
        assert success_response["result"]["files_backed_up"] == 10
        assert success_response["quality_metrics"]["success_rate"] == 1.0
