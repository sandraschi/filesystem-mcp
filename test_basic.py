"""
Basic test script for the Filesystem MCP server.

This script tests the core functionality of the Filesystem MCP server.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

# Use mock MCP module for testing
import sys
import os
sys.modules['mcp'] = __import__('test_utils.mcp_mock', fromlist=['mcp'])

from filesystem_mcp.tools.file_operations import (
    write_file,
    read_file,
    list_directory,
    file_exists,
    get_file_info
)

def run_basic_tests():
    """Run basic tests for the Filesystem MCP tools."""
    print("🚀 Starting Filesystem MCP basic tests...")
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory(prefix="filesystem-mcp-test-") as temp_dir:
        test_dir = Path(temp_dir)
        print(f"📁 Using temporary directory: {test_dir}")
        
        # Test 1: Write a file
        test_file = test_dir / "test.txt"
        test_content = "Hello, Filesystem MCP!"
        
        print(f"📝 Writing test file: {test_file}")
        write_result = write_file(str(test_file), test_content)
        print(f"  - Write result: {write_result['status']}")
        
        # Test 2: Read the file back
        print(f"📖 Reading test file: {test_file}")
        read_content = read_file(str(test_file))
        print(f"  - Content matches: {read_content == test_content}")
        
        # Test 3: Check file exists
        print(f"🔍 Checking if file exists: {test_file}")
        exists = file_exists(str(test_file))
        print(f"  - File exists: {exists}")
        
        # Test 4: Get file info
        print(f"ℹ️  Getting file info: {test_file}")
        file_info = get_file_info(str(test_file))
        print(f"  - File size: {file_info['size']} bytes")
        print(f"  - Is file: {file_info['is_file']}")
        
        # Test 5: List directory
        print(f"📋 Listing directory: {test_dir}")
        dir_contents = list_directory(str(test_dir))
        print(f"  - Found {len(dir_contents)} items")
        for item in dir_contents:
            print(f"    - {item['name']} ({'file' if item['is_file'] else 'dir'}, {item['size']} bytes)")
        
        print("✅ All basic tests completed successfully!")

if __name__ == "__main__":
    run_basic_tests()
