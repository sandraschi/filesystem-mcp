# Contributing to Filesystem MCP

Thank you for your interest in contributing to Filesystem MCP! We welcome contributions from the community to help improve this project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Style](#code-style)
- [Testing](#testing)
- [Documentation](#documentation)
- [Submitting a Pull Request](#submitting-a-pull-request)
- [Reporting Issues](#reporting-issues)
- [Feature Requests](#feature-requests)
- [License](#license)

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
   ```bash
   git clone https://github.com/your-username/filesystem-mcp.git
   cd filesystem-mcp
   ```
3. **Set up the development environment**
   ```bash
   # Create and activate a virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate

   # Install the package in development mode
   pip install -e .

   # Install development dependencies
   pip install -r requirements-dev.txt
   ```
4. **Install pre-commit hooks**
   ```bash
   pre-commit install
   ```

## Development Workflow

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. **Make your changes**
3. **Run tests**
   ```bash
   pytest
   ```
4. **Commit your changes** with a descriptive message
   ```bash
   git commit -m "feat: add new feature"
   ```
5. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```
6. **Open a Pull Request** from your fork to the main repository

## Code Style

We use the following tools to maintain code quality:

- **Black** for code formatting
- **isort** for import sorting
- **mypy** for static type checking
- **pylint** for code quality analysis

Before committing, run:

```bash
black .
isort .
mypy .
pylint filesystem_mcp/
```

## Testing

We use `pytest` for testing. To run the test suite:

```bash
# Run all tests
pytest

# Run tests with coverage report
pytest --cov=filesystem_mcp --cov-report=term-missing

# Run a specific test file
pytest tests/test_file_operations.py -v
```

## Documentation

- Update the relevant sections in the `README.md` for user-facing changes
- Add or update docstrings for any new or modified functions/classes
- Update the `CHANGELOG.md` with a summary of changes

## Submitting a Pull Request

1. Ensure your code passes all tests and linters
2. Update the documentation if necessary
3. Add a clear description of your changes in the PR
4. Reference any related issues
5. Ensure your commit messages follow the [Conventional Commits](https://www.conventionalcommits.org/) specification

## Reporting Issues

When reporting issues, please include:

- A clear title and description
- Steps to reproduce the issue
- Expected vs. actual behavior
- Any relevant error messages or logs
- Your environment (OS, Python version, etc.)

## Feature Requests

For feature requests, please:

1. Check if the feature has already been requested
2. Describe the feature and why it would be useful
3. Include any relevant use cases or examples

## License

By contributing to Filesystem MCP, you agree that your contributions will be licensed under its MIT License.
