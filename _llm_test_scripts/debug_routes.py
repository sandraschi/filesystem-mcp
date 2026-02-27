import sys
import os
from pathlib import Path

# Add src to sys.path
current_dir = os.getcwd()
sys.path.insert(0, os.path.join(current_dir, "src"))

try:
    from filesystem_mcp import app

    print("Successfully imported app")

    http_app = app.http_app()
    print(f"HTTP App type: {type(http_app)}")

    if hasattr(http_app, "routes"):
        print("Routes:")
        for route in http_app.routes:
            print(f" - {route.path} ({route.name})")
    else:
        print("HTTP App has no 'routes' attribute")

except Exception as e:
    print(f"Error: {e}")
