# 🚀 Filesystem MCP - FastMCP 2.12 Migration Plan

## 📋 Executive Summary

This comprehensive migration plan upgrades the filesystem-mcp repository from FastMCP 2.10 to FastMCP 2.12 standards, implements proper DXT building capabilities, and modernizes the codebase with structured logging and Pydantic V2 patterns.

## 🎯 Migration Goals

1. **FastMCP 2.12 Compliance** - Upgrade from 2.10 to 2.12 standards
2. **DXT Building Support** - Implement proper DXT packaging and deployment
3. **Structured Logging** - Replace print/console.log with comprehensive logging
4. **Pydantic V2 Migration** - Update from V1 to V2 patterns
5. **Tool Registration Modernization** - Use @app.tool() decorator patterns
6. **Multiline Decorator Patterns** - Implement without triple quotes in docstrings

## 📊 Current vs Target State

| Component | Current (FastMCP 2.10) | Target (FastMCP 2.12) |
|-----------|----------------------|---------------------|
| **Framework** | FastMCP 2.10.0 | FastMCP 2.12.0+ |
| **Python** | >=3.8 | >=3.9 |
| **Pydantic** | V1 patterns | V2 field_validator |
| **Tool Registration** | Custom @tool decorator | @app.tool() decorator |
| **Logging** | Basic logging | Structured logging with file output |
| **Packaging** | setuptools | DXT + setuptools |
| **Dependencies** | Basic requirements | Comprehensive with version pinning |

## 🏗️ Implementation Plan

### Phase 1: Foundation Setup (✅ COMPLETED)

#### 1.1 Dependencies Update
- ✅ Updated pyproject.toml for FastMCP 2.12.0+
- ✅ Added Pydantic 2.5.0+ and modern dependencies
- ✅ Updated Python requirement to 3.9+
- ✅ Added comprehensive development dependencies

#### 1.2 Folder Structure Modernization
- ✅ Implemented src/ directory structure for DXT compatibility
- ✅ Updated main application to FastMCP 2.12 patterns
- ✅ Created proper tools module structure

### Phase 2: Code Modernization (IN PROGRESS)

#### 2.1 Pydantic V2 Migration
**Files to Update:**
- `filesystem_mcp/tools/file_operations/__init__.py`
- `filesystem_mcp/tools/repo_operations/__init__.py`
- `filesystem_mcp/tools/docker_operations.py`

**Changes Required:**
```python
# ❌ Old (Pydantic V1)
class MyModel(BaseModel):
    @validator('field_name')
    def validate_field(cls, v):
        return v

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}

# ✅ New (Pydantic V2)
class MyModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_validator('field_name')
    @classmethod
    def validate_field(cls, v):
        return v
```

#### 2.2 Tool Registration System
**Current Pattern:**
```python
# ❌ Old custom decorator
@tool(name="read_file", description="...")
async def read_file(...):
    pass
```

**Target Pattern:**
```python
# ✅ New FastMCP 2.12 pattern
@app.tool()
async def read_file(
    file_path: str,
    encoding: str = "utf-8"
) -> dict:
    """Read the contents of a file with proper error handling and metadata.

    This tool reads a file and returns its content along with comprehensive
    metadata. It includes proper error handling, security checks, and
    structured logging for debugging.

    Args:
        file_path: Path to the file to read (relative or absolute)
        encoding: Character encoding to use (default: utf-8)

    Returns:
        Dictionary containing file content and metadata
    """
```

#### 2.3 Structured Logging Implementation
**Current Issues:**
- Mixed logging levels
- No structured output
- Missing file logging
- Inconsistent error handling

**Target Implementation:**
```python
# ✅ New structured logging pattern
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr),  # For Claude Desktop visibility
        logging.FileHandler('filesystem_mcp.log')  # Persistent log file
    ]
)

logger = logging.getLogger(__name__)

# In functions
logger.info(f"Reading file: {file_path}")
logger.debug(f"Resolved path: {path}")
logger.error(f"Unexpected error: {e}", exc_info=True)
```

### Phase 3: DXT Building Implementation

#### 3.1 DXT Manifest Creation
**File:** `dxt/manifest.json`

**Required Structure:**
```json
{
  "dxt_version": "0.1",
  "name": "filesystem-mcp",
  "version": "2.0.0",
  "description": "Comprehensive MCP server for file system, Git, and Docker operations",
  "author": {
    "name": "Sandra Schimanovich",
    "email": "sandra@sandraschi.dev"
  },
  "server": {
    "type": "python",
    "entry_point": "src/filesystem_mcp/__main__.py",
    "mcp_config": {
      "command": "python",
      "args": ["-m", "filesystem_mcp"],
      "cwd": "src",
      "env": {
        "PYTHONPATH": "src",
        "PYTHONUNBUFFERED": "1"
      }
    }
  },
  "capabilities": {
    "tools": true,
    "resources": true,
    "prompts": true
  },
  "user_config": {
    "working_directory": {
      "type": "directory",
      "title": "Working Directory",
      "description": "Directory for file operations",
      "required": true,
      "default": "${HOME}/Documents/FilesystemMCP"
    }
  }
}
```

#### 3.2 DXT Configuration
**File:** `dxt/dxt.json`

**Required Structure:**
```json
{
  "name": "filesystem-mcp",
  "version": "2.0.0",
  "description": "DXT build configuration for filesystem-mcp",
  "outputDir": "dist",
  "mcp": {
    "version": "2.12.0",
    "server": {
      "command": "python",
      "args": ["-m", "filesystem_mcp"],
      "transport": "stdio"
    }
  },
  "dependencies": {
    "python": ">=3.9.0"
  }
}
```

#### 3.3 Build Process
**Required Commands:**
```bash
# 1. Validate configuration
dxt validate dxt/manifest.json

# 2. Build DXT package
dxt pack . dist/filesystem-mcp-2.0.0.dxt

# 3. Sign package (production)
dxt sign --key signing.key dist/filesystem-mcp-2.0.0.dxt

# 4. Verify package
dxt verify dist/filesystem-mcp-2.0.0.dxt
```

### Phase 4: Repository Structure

#### 4.1 New Folder Structure
```
filesystem-mcp/
├── dxt/                          # DXT configuration and manifests
│   ├── manifest.json             # Runtime configuration
│   └── dxt.json                  # Build configuration
├── src/                          # Source code (DXT requirement)
│   └── filesystem_mcp/           # Main Python package
│       ├── __init__.py          # Main application
│       ├── __main__.py          # Entry point
│       └── tools/                # Tool modules
│           ├── __init__.py       # Tool registration
│           ├── file_operations/  # File operations
│           ├── repo_operations/  # Git operations
│           └── docker_operations/ # Docker operations
├── docs/                         # Documentation
│   ├── DXT_BUILDING_GUIDE.md    # DXT building guide
│   └── standards/                # Development standards
├── .github/                      # GitHub workflows
│   └── workflows/
│       └── build-dxt.yml         # DXT build pipeline
├── requirements.txt              # Python dependencies
├── pyproject.toml                # Project metadata
└── README.md                     # Project documentation
```

#### 4.2 Migration Strategy
1. Create new `src/` directory structure
2. Move existing code to `src/filesystem_mcp/`
3. Create DXT configuration files
4. Update import paths throughout codebase
5. Test both old and new structures during transition

### Phase 5: CI/CD Integration

#### 5.1 GitHub Actions Workflow
**File:** `.github/workflows/build-dxt.yml`

**Key Features:**
- Automated testing and linting
- DXT package building
- Multi-platform support (Windows, macOS, Linux)
- Version tagging and releases
- FastMCP 2.12 validation

#### 5.2 Build Script
**File:** `scripts/build-dxt.ps1`

**PowerShell script for consistent builds:**
```powershell
param(
    [switch]$NoSign,
    [string]$OutputDir = "dist"
)

# Build Python package
python -m build

# Build DXT package
dxt pack . $OutputDir/package.dxt

# Sign if not disabled
if (-not $NoSign) {
    dxt sign --key signing.key $OutputDir/package.dxt
}

Write-Host "✅ DXT package built successfully"
```

### Phase 6: Documentation Updates

#### 6.1 README.md Updates
- FastMCP 2.12 compatibility badge
- DXT installation instructions
- Updated tool descriptions
- Troubleshooting section for DXT

#### 6.2 DXT-Specific Documentation
- `docs/DXT_BUILDING_GUIDE.md` - Complete DXT building guide
- `docs/DXT_TROUBLESHOOTING.md` - DXT-specific troubleshooting
- `docs/DXT_MANIFEST_REFERENCE.md` - Manifest configuration reference

## 🔧 Implementation Checklist

### Critical Path Items
- [x] Update pyproject.toml dependencies
- [x] Create src/ directory structure
- [x] Implement structured logging
- [ ] Complete Pydantic V2 migration
- [ ] Implement @app.tool() decorators
- [ ] Create DXT manifest.json
- [ ] Create DXT dxt.json
- [ ] Test DXT package building
- [ ] Update documentation

### Quality Assurance
- [ ] Validate FastMCP 2.12 compatibility
- [ ] Test all tools with new decorator pattern
- [ ] Verify DXT package installation
- [ ] Test on multiple platforms
- [ ] Validate logging output
- [ ] Check error handling

## 📋 Tool Registration Patterns

### Current Custom Decorator Pattern
```python
# ❌ Old pattern with triple quotes in docstring
@tool(
    name="read_file",
    description="""Read the contents of a file with proper error handling and metadata.

    This function reads a file and returns its content along with metadata.
    It includes proper error handling and security checks.""",
    response_model=FileContent
)
async def read_file(file_path: str, encoding: str = "utf-8") -> FileContent:
    pass
```

### Target FastMCP 2.12 Pattern
```python
# ✅ New pattern - no triple quotes needed in docstring
@app.tool()
async def read_file(
    file_path: str,
    encoding: str = "utf-8"
) -> dict:
    """Read the contents of a file with proper error handling and metadata.

    This tool reads a file and returns its content along with comprehensive
    metadata. It includes proper error handling, security checks, and
    structured logging for debugging.

    Args:
        file_path: Path to the file to read (relative or absolute)
        encoding: Character encoding to use (default: utf-8)

    Returns:
        Dictionary containing file content and metadata

    Error Handling:
        Returns error dict if file not found, permission denied, or other issues
    """
    try:
        logger.info(f"Reading file: {file_path}")
        # Implementation...
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return {"success": False, "error": str(e)}
```

## 🚀 DXT Package Structure

### Final Package Layout
```
filesystem-mcp-2.0.0.dxt/
├── manifest.json              # Runtime configuration
├── src/                       # Python source code
│   └── filesystem_mcp/
├── lib/                       # Dependencies
│   ├── fastmcp/
│   └── pydantic/
├── requirements.txt           # Python dependencies
└── prompts/                   # AI prompt templates
    ├── system.md
    ├── user.md
    └── examples.json
```

### Installation Process
1. User downloads `.dxt` file
2. Drags file to Claude Desktop
3. DXT runtime handles installation
4. User configures working directory
5. Extension becomes available

## 📊 Success Metrics

### Technical Success
- [ ] All tools register correctly with FastMCP 2.12
- [ ] DXT package builds without errors
- [ ] No Pydantic V1 deprecation warnings
- [ ] Structured logging works in Claude Desktop
- [ ] Package installs correctly via DXT

### User Experience
- [ ] Extension loads in < 2 seconds
- [ ] All tools function as expected
- [ ] Clear error messages for failures
- [ ] Comprehensive logging for debugging
- [ ] Easy configuration process

## 🎯 Next Steps

1. **Immediate**: Complete Pydantic V2 migration
2. **Week 1**: Implement @app.tool() decorators for all tools
3. **Week 2**: Create DXT configuration files
4. **Week 3**: Test DXT package building and installation
5. **Week 4**: Update documentation and create CI/CD pipeline

## 📞 Support and Resources

- **DXT Documentation**: docs/DXT_BUILDING_GUIDE.md
- **FastMCP 2.12 Guide**: docs/TROUBLESHOOTING_FASTMCP_2.12.md
- **Migration Examples**: Examples in this document
- **Community**: GitHub issues for specific problems

This migration plan ensures a smooth transition to FastMCP 2.12 standards while implementing proper DXT building capabilities for professional MCP server distribution.
