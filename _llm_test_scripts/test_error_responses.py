#!/usr/bin/env python3
"""
Test script to verify error response functions work correctly.
"""

import sys

sys.path.insert(0, 'src')

def test_error_response_functions():
    """Test that our error response functions work correctly."""
    try:
        from filesystem_mcp.tools.utils import (
            _clarification_response,
            _error_response,
            _success_response,
        )

        print("Testing _error_response function...")

        # Test basic error response
        result = _error_response(
            error="Test error message",
            error_type="test_error"
        )

        assert result["success"] is False
        assert result["error"] == "Test error message"
        assert result["error_type"] == "test_error"
        assert "recovery_options" in result
        assert "diagnostic_info" in result
        assert "timestamp" in result

        print("[PASS] _error_response works correctly")

        # Test error response with all parameters
        result = _error_response(
            error="Complex error",
            error_type="complex_error",
            recovery_options=["Try option 1", "Try option 2"],
            diagnostic_info={"test": "data"},
            suggested_fixes=["Fix 1", "Fix 2"],
            alternative_approaches=["Approach A", "Approach B"],
            estimated_resolution_time="5 minutes"
        )

        assert result["success"] is False
        assert result["error"] == "Complex error"
        assert result["error_type"] == "complex_error"
        assert result["recovery_options"] == ["Try option 1", "Try option 2"]
        assert result["diagnostic_info"]["test"] == "data"
        assert result["suggested_fixes"] == ["Fix 1", "Fix 2"]
        assert result["alternative_approaches"] == ["Approach A", "Approach B"]
        assert result["estimated_resolution_time"] == "5 minutes"

        print("[PASS] _error_response with all parameters works correctly")

        print("Testing _success_response function...")

        # Test success response
        result = _success_response(
            result={"test": "data"},
            operation="test_operation"
        )

        assert result["success"] is True
        assert result["operation"] == "test_operation"
        assert result["result"]["test"] == "data"
        assert "quality_metrics" in result
        assert "recommendations" in result
        assert "next_steps" in result
        assert "related_operations" in result
        assert "timestamp" in result

        print("[PASS] _success_response works correctly")

        print("Testing _clarification_response function...")

        # Test clarification response
        result = _clarification_response(
            ambiguities=["Unclear parameter"],
            suggested_questions=["What do you mean?"]
        )

        assert result["status"] == "clarification_needed"
        assert result["ambiguities"] == ["Unclear parameter"]
        assert "suggested_questions" in result
        assert "timestamp" in result

        print("[PASS] _clarification_response works correctly")

        print("\n[SUCCESS] All error response functions work correctly!")
        print("No issues like the Advanced Memory MCP error found.")
        return True

    except Exception as e:
        print(f"\n[FAILED] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_error_response_functions()
    sys.exit(0 if success else 1)
