"""
Setup script for the Filesystem MCP package.
"""

from setuptools import find_packages, setup

with open("README.md", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="filesystem-mcp",
    version="0.1.0",
    author="Sandra Schimanovich",
    author_email="sandra@example.com",
    description="FastMCP 2.10 compliant MCP server for file system and repository operations",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sandraschi/filesystem-mcp",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "fastmcp>=2.10.0",
        "gitpython>=3.1.0",
        "uvicorn>=0.20.0",
        "python-multipart>=0.0.5",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "black>=22.0.0",
            "isort>=5.0.0",
            "mypy>=0.900",
            "types-python-dateutil>=2.8.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "filesystem-mcp=filesystem_mcp:run",
        ],
    },
)
