"""
Test suite for filesystem-mcp.

This package contains comprehensive unit and integration tests for all
filesystem-mcp tools and functionality. Tests follow pytest best practices
with async testing support and proper mocking.
"""

import logging

import pytest

# Configure test logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    import asyncio

    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Test configuration
TEST_CONFIG = {
    "timeout": 30,  # seconds
    "retries": 3,
    "parallel": True,
    "coverage": True,
}


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on file location."""
    for item in items:
        # Mark integration tests
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        # Mark unit tests
        elif "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)

        # Mark slow tests
        if "slow" in item.keywords:
            item.add_marker(pytest.mark.slow)
