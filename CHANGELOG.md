# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
