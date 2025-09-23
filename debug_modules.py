from filesystem_mcp.tools import file_operations, repo_operations, docker_operations

def debug_modules():
    tool_modules = [file_operations, repo_operations, docker_operations]

    for module in tool_modules:
        print(f"\n=== {module.__name__} ===")
        for name, obj in module.__dict__.items():
            if name.startswith('_') or not callable(obj):
                continue

            if hasattr(obj, '_mcp_tool'):
                tool_meta = getattr(obj, '_mcp_tool')
                print(f"Function: {name}")
                print(f"  Tool name: {tool_meta.get('name', 'None')}")
                print(f"  Description: {tool_meta.get('description', 'None')[:100]}...")
                print(f"  Parameters: {len(tool_meta.get('parameters', {}))} params")

if __name__ == "__main__":
    debug_modules()
