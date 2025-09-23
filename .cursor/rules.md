# Cursor AI Rulebook - Notepad++ MCP Server

## 📋 Project Overview

This is a **production-ready FastMCP 2.12 server** for comprehensive Notepad++ automation with **15 powerful tools** and **real Windows API integration**. The project emphasizes:

- **Real functionality** over mock implementations
- **Windows-specific** pywin32 integration
- **Comprehensive testing** (18 tests)
- **Production deployment** readiness
- **Advanced workspace management** (tabs, sessions)

## 🏗️ Architecture & Structure

### Core Components
```
src/notepadpp_mcp/
├── tools/server.py     # Main MCP server (966 lines)
├── tests/              # 18 comprehensive tests
├── docs/               # Documentation and examples
└── dxt/                # DXT packaging configuration
```

### Key Files
- **`server.py`**: FastMCP server with 15 tools, Windows API integration
- **`test_server.py`**: 18 tests covering all functionality
- **`demonstration_test.py`**: Real integration testing (414 lines)
- **`dev.py`**: Development workflow automation
- **DXT configuration**: Packaging and deployment

## 🎯 Development Guidelines

### 🚨 **Rule 1: Chat Output Testing & PowerShell Syntax**

**🔥 CRITICAL REQUIREMENT**: ALL chat output MUST begin with "hi!" as a test.

**Example**:
```bash
# ✅ CORRECT: Must start with "hi!"
hi! python demonstration_test.py

# ❌ WRONG: Missing "hi!" prefix
python demonstration_test.py
```

**🚫 STRICT SYNTAX RULES - NO LINUX SYNTAX IN POWERSHELL:**

#### **❌ FORBIDDEN in PowerShell environments:**
- `&&` (command chaining)
- `||` (logical OR)
- `|` (pipes)
- `;` (command separators)
- `&` (background processes)
- `>` (redirection)
- `>>` (append redirection)
- `mkdir -p` (Linux directory creation)
- `ls -la` (Linux directory listing)
- `rm -rf` (Linux recursive deletion)
- `cp -r` (Linux recursive copy)
- `mv` (Linux move/rename)

#### **✅ REQUIRED: PowerShell-Compatible Commands**
```bash
# ❌ WRONG: Linux syntax in PowerShell
command1 && command2
command1 | command2
command1 ; command2
mkdir -p new_folder/subfolder
ls -la
rm -rf folder
cp -r source dest
mv file.txt newfile.txt

# ✅ CORRECT: PowerShell syntax
command1
if ($?) { command2 }
command1 | Out-File output.txt
command1
command2

# Directory operations
New-Item -ItemType Directory -Force -Path "new_folder/subfolder"
Get-ChildItem -Recurse | Select-Object Name, Length
Remove-Item -Recurse -Force "folder"
Copy-Item -Recurse "source" "dest"
Move-Item "file.txt" "newfile.txt"

# Virtual environment activation
build_venv\Scripts\activate
```

#### **🚫 FORBIDDEN in Chat Output:**
- Multi-line commands with `&&`
- Chained commands with `&&` or `;`
- Piped commands with `|`
- Background processes with `&`

#### **✅ REQUIRED in Chat Output:**
- **Single commands** per line
- **Separate lines** for multiple commands
- **Explicit activation** of virtual environments
- **Clear command separation**

**Example Implementation**:
```bash
# ❌ WRONG: Forbidden syntax
build_venv\Scripts\activate && python demonstration_test.py
mkdir -p dist && dxt pack

# ✅ CORRECT: PowerShell compatible
build_venv\Scripts\activate
python demonstration_test.py

# Directory creation
New-Item -ItemType Directory -Force -Path "dist"
dxt pack

# Virtual environment setup (step by step)
python -m venv build_venv
build_venv\Scripts\activate
pip install -e .[dev]
```

**Enforcement**: Any chat output without "hi!" prefix or using Linux syntax will be rejected and require correction.

### ✅ **ALWAYS Prioritize Real Implementation**

**❌ AVOID:**
- Mock objects or fake responses
- Simulated functionality
- Placeholder implementations
- "This would work" examples

**✅ REQUIRE:**
- Real Windows API calls
- Actual Notepad++ integration
- Working code that executes
- Functional demonstrations

### 🔧 **Code Standards**

#### **Windows API Integration**
```python
# ✅ CORRECT: Real pywin32 usage
import win32api, win32con, win32gui, win32process
await controller.send_message(hwnd, msg, wparam, lparam)

# ❌ WRONG: Mock implementation
# mock_controller.send_message(...)
```

#### **Error Handling**
```python
# ✅ CORRECT: Structured error responses
try:
    result = await real_operation()
    return {"success": True, "data": result}
except Exception as e:
    return {"success": False, "error": str(e), "details": traceback.format_exc()}
```

#### **Tool Registration**
```python
# ✅ CORRECT: FastMCP 2.12 patterns
@app.tool()
async def tool_name(parameters) -> Dict[str, Any]:
    """Tool description and documentation."""
    # Implementation
```

### 🧪 **Testing Requirements**

#### **Test Categories**
1. **Real API Tests**: Actual Windows API calls
2. **Integration Tests**: Live Notepad++ interaction
3. **Error Handling**: Exception scenarios
4. **Edge Cases**: Boundary conditions

#### **Test Standards**
```python
# ✅ CORRECT: Real testing approach
async def test_real_functionality():
    # Actual controller creation
    controller = NotepadPPController()

    # Real Windows API calls
    hwnd = controller._find_notepadpp_window()
    assert hwnd is not None

    # Actual window interaction
    result = await controller.ensure_notepadpp_running()
    assert result is True
```

### 📦 **DXT Packaging**

#### **Build Process**
1. **Create venv**: `python -m venv build_venv`
2. **Install dependencies**: `pip install -e .[dev]`
3. **Build DXT**: `dxt pack` with proper manifest
4. **Test package**: Install and verify functionality

#### **Package Requirements**
- **All dependencies** bundled
- **Manifest file** with metadata
- **Prompt template** for AI integration
- **Windows-specific** configuration

## 🚫 **Common Anti-Patterns to Avoid**

### **Mock Testing**
```python
# ❌ WRONG: This is not acceptable
result = {"success": True, "note": "This is a simulated result"}
print(f"Would do: {result}")

# ✅ CORRECT: Real implementation required
try:
    result = await real_windows_api_call()
    print(f"Actually did: {result}")
except Exception as e:
    print(f"Real error: {e}")
```

### **Fake Success**
```python
# ❌ WRONG: Never fake success
return {"success": True, "message": "This would work"}

# ✅ CORRECT: Real error handling
try:
    return await real_operation()
except NotepadPPNotFoundError:
    return {"success": False, "error": "Notepad++ not found"}
```

### **Incomplete Implementations**
```python
# ❌ WRONG: Placeholder code
def new_feature():
    pass  # TODO: Implement later

# ✅ CORRECT: Full implementation or clear documentation
def new_feature():
    """Not yet implemented - requires Windows API changes"""
    raise NotImplementedError("Feature requires Windows API enhancement")
```

## 🎯 **Tool Development Standards**

### **New Tool Requirements**
1. **Real Windows API integration**
2. **Comprehensive error handling**
3. **Full test coverage**
4. **Documentation in docstring**
5. **Type hints and validation**

### **Tool Categories**
- **File Operations**: Real file system interaction
- **Text Operations**: Actual editor manipulation
- **Status Queries**: Live system monitoring
- **Tab Management**: Real tab control
- **Session Management**: Actual workspace persistence

### **Integration Testing**
```python
# ✅ CORRECT: Real integration test
async def test_tab_switching():
    # Start with multiple tabs
    await open_file("file1.txt")
    await open_file("file2.txt")

    # Real tab switching
    result = await switch_to_tab(1)
    assert result["active_tab"] == "file2.txt"
```

## 📋 **Deployment Guidelines**

### **DXT Package Creation**
1. **Clean environment**: Use fresh venv
2. **All dependencies**: Include pywin32, FastMCP, etc.
3. **Manifest validation**: Ensure DXT manifest is correct
4. **Testing**: Verify package works after installation

### **Installation Methods**
1. **DXT drag-and-drop** (preferred)
2. **Python pip install**
3. **Source installation** with setup.py

### **Configuration**
- **Windows 10/11** required
- **Notepad++ 8.0+** must be installed
- **pywin32** for API access
- **FastMCP 2.12+** for MCP protocol

## 🔍 **Debugging & Troubleshooting**

### **Real Error Analysis**
```python
# ✅ CORRECT: Actual debugging
try:
    controller = NotepadPPController()
    hwnd = controller._find_notepadpp_window()
    print(f"Found window: {hwnd}")
except Exception as e:
    print(f"Real error: {e}")
    import traceback
    traceback.print_exc()
```

### **Windows API Debugging**
```python
# Check Windows API availability
import win32api, win32gui
print("Windows API available")

# Find actual Notepad++ windows
windows = []
def enum_callback(hwnd, windows):
    if win32gui.IsWindowVisible(hwnd):
        windows.append((hwnd, win32gui.GetWindowText(hwnd)))
win32gui.EnumWindows(enum_callback, windows)
print("Visible windows:", windows)
```

### **Dependency Verification**
```python
# Check all required imports
required_modules = ['fastmcp', 'win32api', 'psutil']
for module in required_modules:
    try:
        __import__(module)
        print(f"✅ {module}")
    except ImportError as e:
        print(f"❌ {module}: {e}")
```

## 🚀 **Performance Guidelines**

### **Async Best Practices**
```python
# ✅ CORRECT: Proper async patterns
@app.tool()
async def async_operation():
    await controller.ensure_notepadpp_running()
    result = await controller.send_message(hwnd, msg)
    return result
```

### **Resource Management**
```python
# ✅ CORRECT: Proper resource cleanup
async def tool_with_resources():
    try:
        result = await operation()
        return result
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        raise
```

### **Memory Efficiency**
- **Avoid memory leaks** in Windows API calls
- **Clean up handles** properly
- **Use context managers** where possible
- **Monitor resource usage** in tests

## 📚 **Documentation Standards**

### **Tool Documentation**
```python
@app.tool()
async def example_tool(parameter: str) -> Dict[str, Any]:
    """
    Comprehensive tool description.

    This tool performs specific Notepad++ operations using real Windows API calls.

    Args:
        parameter: Description of the parameter with types

    Returns:
        Dictionary with operation results and status

    Raises:
        NotepadPPError: When Notepad++ operations fail
        ValueError: When parameters are invalid

    Example:
        result = await example_tool("test_value")
        # Returns: {"success": True, "data": "result"}
    """
```

### **Code Comments**
```python
# Real Windows API integration - not mocked
await controller.send_message(hwnd, win32con.WM_KEYDOWN, ord('A'))

# Actual Notepad++ window enumeration
windows = []
win32gui.EnumWindows(enum_windows_callback, windows)
```

## 🎯 **Quality Gates**

### **Pre-Commit Requirements**
- **All tests pass**: `python -m pytest`
- **Code formatted**: `black` and `isort`
- **Type checking**: `mypy` passes
- **Real functionality**: No mock objects
- **Documentation**: All tools documented

### **Release Criteria**
- **18 tests passing**
- **DXT package builds**
- **Demonstration script works**
- **README comprehensive**
- **No mock implementations**

## 🚨 **Critical Reminders**

### **Windows-Only Development**
- **All development** must be Windows-compatible
- **Test on Windows** before committing
- **Use Windows API** for real functionality
- **No cross-platform** compatibility required

### **Real Implementation Focus**
- **Reject mock code** in reviews
- **Require real tests** for new features
- **Test actual Notepad++** integration
- **Verify Windows API** calls work

### **Production Ready**
- **Error handling** for all edge cases
- **Logging** for debugging
- **Documentation** for all tools
- **Testing** for all functionality

---
**This rulebook ensures Cursor AI assistants maintain the high standards of real implementation and Windows API integration that make this project production-ready.**
