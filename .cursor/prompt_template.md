# Notepad++ MCP Server - AI Development Context

You are working on a **production-ready FastMCP 2.12 server** for Notepad++ automation. This project has specific requirements and standards:

## 🎯 Project Identity
- **Name**: Notepad++ MCP Server v1.0
- **Purpose**: Comprehensive Notepad++ automation via MCP protocol
- **Platform**: Windows-only with pywin32 integration
- **Tools**: 15 production-ready tools
- **Testing**: 18 comprehensive tests with real Windows API integration

## 🏗️ Architecture Overview
```
FastMCP Server → NotepadPPController → Windows API → Notepad++ Application
```

### Core Components:
1. **server.py** (966 lines): Main MCP server with tool registration
2. **test_server.py** (264 lines): 18 comprehensive tests
3. **demonstration_test.py** (414 lines): Real integration testing
4. **dxt.toml**: DXT packaging configuration with extensive prompt template

## 🔧 Development Standards

### ✅ **ALWAYS Use Real Implementation**
- **Require** actual Windows API calls (pywin32)
- **Forbid** mock objects or simulated responses
- **Test** with real Notepad++ integration
- **Verify** functionality through demonstration script

### 📋 **Code Patterns**
```python
# Real Windows API integration
@app.tool()
async def real_tool() -> Dict[str, Any]:
    """Actual Notepad++ automation using Windows API."""
    controller = NotepadPPController()
    await controller.ensure_notepadpp_running()
    # Real implementation with win32api, win32gui calls
```

### 🧪 **Testing Requirements**
- All tests must use real Windows API calls
- Integration tests with actual Notepad++ interaction
- Error handling for Notepad++ not found/running
- Edge case testing with real scenarios

## 🚫 **Anti-Patterns to Avoid**

### **Mock Testing** ❌
```python
# WRONG: This is not acceptable
result = {"success": True, "note": "This is a simulated result"}
```

### **Fake Success** ❌
```python
# WRONG: Never fake success
return {"success": True, "message": "This would work"}
```

### **Incomplete Implementation** ❌
```python
# WRONG: Placeholder code
def new_feature():
    pass  # TODO: Implement later
```

## 🎯 **Tool Categories (15 Total)**

### 📁 **File Operations** (4 tools)
- Real file system interaction
- Actual Notepad++ file opening/creation
- File metadata retrieval

### 📝 **Text Operations** (2 tools)
- Real text insertion at cursor
- Actual search functionality

### 📊 **Status & Information** (3 tools)
- Live system monitoring
- Real process information
- Window handle detection

### 📑 **Tab Management** (3 tools) ✨ NEW
- Actual tab switching
- Real tab listing and control
- Tab closure functionality

### 💾 **Session Management** (3 tools) ✨ NEW
- Real workspace persistence
- Session save/load functionality
- Workspace state management

## 🛠️ **Development Workflow**

### **Environment Setup**
1. **Create venv**: `python -m venv build_venv`
2. **Install dependencies**: `pip install -e .[dev]`
3. **Test integration**: `python demonstration_test.py`

### **Code Standards**
- **Black formatting**: 100 character line length
- **Type hints**: Required for all functions
- **Error handling**: Structured exception handling
- **Documentation**: Comprehensive docstrings

### **Testing Strategy**
- **Real API tests**: Actual Windows API calls
- **Integration tests**: Live Notepad++ interaction
- **Error scenarios**: Exception handling validation
- **Edge cases**: Boundary condition testing

## 🚀 **Key Features**

### **Windows Integration**
- Real pywin32 Windows API usage
- Actual Notepad++ window detection
- Live Scintilla editor control
- Keyboard and mouse simulation

### **Production Ready**
- Comprehensive error handling
- Structured logging
- Real test coverage
- DXT packaging for deployment

### **Advanced Capabilities**
- Multi-tab workspace management
- Session save/restore functionality
- Real-time status monitoring
- Hierarchical help system

## 📦 **DXT Packaging**

### **Build Process**
1. Clean virtual environment
2. All dependencies bundled
3. Extensive prompt template included
4. Windows-specific configuration

### **Installation Methods**
1. **DXT drag-and-drop** (preferred)
2. **Python pip install**
3. **Manual configuration**

## 🐛 **Common Issues**

### **Notepad++ Not Found**
- Verify Notepad++ installation
- Check Windows registry entries
- Run demonstration script for diagnostics

### **Windows API Issues**
- Ensure pywin32 is properly installed
- Check Windows API availability
- Verify user permissions

### **Integration Problems**
- Test with demonstration script first
- Verify MCP server configuration
- Check Claude Desktop logs

## 🎯 **Quality Standards**

### **Code Quality**
- **Real implementation** required
- **No mock objects** allowed
- **Comprehensive testing** mandatory
- **Production-ready** error handling

### **Documentation**
- **Tool docstrings** with examples
- **Usage guidelines** and best practices
- **Troubleshooting** procedures
- **Architecture** explanations

### **Testing**
- **18 tests** covering all functionality
- **Real Windows API** integration tests
- **Error scenario** validation
- **Edge case** handling

---
**Remember: This project requires REAL Windows API integration with actual Notepad++ automation. Mock implementations and simulated functionality are not acceptable.**
