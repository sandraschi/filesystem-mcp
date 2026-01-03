# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-12-25

### Added
- **Major Tool Expansion**: Added 10+ advanced file operations tools (57+ total tools)
  - `find_large_files` - Large file detection for disk management
  - `find_duplicate_files` - Content-based duplicate file detection
  - `find_empty_directories` - Empty directory cleanup
  - `compare_files` - File diff comparison with unified format
  - `read_multiple_files` - Batch file reading operations
  - `move_file` - File/directory moving with overwrite control
  - `read_file_lines` - Precise line-based file reading
  - `search_files` - Advanced recursive file search with patterns
  - `directory_tree` - Visual directory tree representation
  - `calculate_directory_size` - Directory size calculation with statistics

- **MCPB Packaging**: Professional drag-and-drop installation for Claude Desktop
  - Complete MCPB manifest with user configuration
  - Extensive prompt templates for AI integration
  - Clean package structure without bundled dependencies
  - Professional build scripts and CI/CD integration

- **Enhanced Prompt Templates**: Comprehensive AI integration templates
  - `system.md` - System-level Claude Desktop instructions
  - `user.md` - User interaction guide with examples
  - `examples.json` - Structured tool usage examples
  - `quick-start.md` - 5-minute getting started guide
  - `configuration.md` - Detailed configuration options
  - `troubleshooting.md` - Comprehensive troubleshooting guide

### Changed
- **FastMCP Upgrade**: Migrated from FastMCP 2.12.0 to 2.14.1+
- **Packaging Migration**: Complete transition from DXT to MCPB format
- **Installation Method**: MCPB drag-and-drop now primary installation method
- **Dependencies**: MCPB packages no longer bundle dependencies (installed separately)
- **Documentation**: Updated installation instructions and feature descriptions

### Fixed
- Manifest validation errors in MCPB packaging
- Broken symlinks in development environment
- Package build process optimizations

### Security
- Updated author information and contact details
- Maintained secure path validation and permission checks
- Enhanced audit logging capabilities

## [1.0.0] - 2024-05-20

### Added
- Initial release of Filesystem MCP
- **File System Operations**:
  - Read, write, and manage files and directories
  - List directory contents with detailed metadata
  - Recursive directory scanning
  - File content analysis

- **Docker Container Management**:
  - Container lifecycle management (create, start, stop, remove)
  - Image management (list, pull, build, remove)
  - Network and volume management
  - Docker Compose support
  - Container execution and log streaming

- **Git Repository Management**:
  - Clone repositories with branch and depth control
  - Repository status and commit management
  - Repository structure inspection

- **Developer Experience**:
  - Comprehensive API documentation
  - Type hints throughout the codebase
  - Unit and integration tests
  - CI/CD pipeline with GitHub Actions
  - Pre-commit hooks for code quality

### Changed
- Project structure optimized for FastMCP 2.10 compatibility
- Improved error handling and validation
- Enhanced security with secure path handling

### Fixed
- Various bug fixes and stability improvements

### Security
- Implemented secure path validation
- Added input sanitization
- Improved error messages to prevent information leakage

## [0.1.0] - 2024-05-01
### Added
- Initial project setup
- Basic file system operations
- Git repository management foundation
