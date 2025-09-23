"""
FastMCP 2.10 compliant server implementation for filesystem-mcp.
"""
import json
import sys
import logging
from typing import Any, Dict, List, Optional, Union, Callable, Awaitable
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("filesystem-mcp")

class MCPMessage:
    """Represents an MCP message."""
    
    def __init__(
        self,
        jsonrpc: str = "2.0",
        id: Optional[Union[str, int]] = None,
        method: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        result: Optional[Any] = None,
        error: Optional[Dict[str, Any]] = None
    ):
        self.jsonrpc = jsonrpc
        self.id = id
        self.method = method
        self.params = params or {}
        self.result = result
        self.error = error
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the message to a dictionary."""
        msg = {"jsonrpc": self.jsonrpc}
        if self.id is not None:
            msg["id"] = self.id
        if self.method is not None:
            msg["method"] = self.method
        if self.params is not None:
            msg["params"] = self.params
        if self.result is not None:
            msg["result"] = self.result
        if self.error is not None:
            msg["error"] = self.error
        return msg
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MCPMessage':
        """Create an MCPMessage from a dictionary."""
        return cls(
            jsonrpc=data.get("jsonrpc", "2.0"),
            id=data.get("id"),
            method=data.get("method"),
            params=data.get("params", {}),
            result=data.get("result"),
            error=data.get("error")
        )

class MCPServer:
    """FastMCP 2.10 compliant server implementation."""
    
    def __init__(self):
        self.methods = {}
        self._shutdown = False
        self._executor = ThreadPoolExecutor()
        
        # Register standard MCP methods
        self.register_method("mcp.ping", self._handle_ping)
        self.register_method("mcp.shutdown", self._handle_shutdown)
    
    def register_method(self, name: str, func: Callable[..., Awaitable[Any]]):
        """Register an MCP method handler."""
        self.methods[name] = func
    
    async def _handle_ping(self) -> str:
        """Handle mcp.ping method."""
        return "pong"
    
    async def _handle_shutdown(self) -> None:
        """Handle mcp.shutdown method."""
        self._shutdown = True
    
    async def _process_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a single MCP message."""
        try:
            msg = MCPMessage.from_dict(message)
            
            # Handle notifications (no id)
            if msg.id is None:
                if msg.method == "mcp.shutdown":
                    await self._handle_shutdown()
                return None
            
            # Handle method calls
            if msg.method in self.methods:
                try:
                    # Handle both sync and async methods
                    result = self.methods[msg.method](**msg.params)
                    if asyncio.iscoroutine(result):
                        result = await result
                    
                    return MCPMessage(
                        id=msg.id,
                        result=result
                    ).to_dict()
                except Exception as e:
                    logger.exception(f"Error executing method {msg.method}")
                    return MCPMessage(
                        id=msg.id,
                        error={
                            "code": -32603,
                            "message": f"Internal error: {str(e)}"
                        }
                    ).to_dict()
            else:
                return MCPMessage(
                    id=msg.id,
                    error={
                        "code": -32601,
                        "message": f"Method not found: {msg.method}"
                    }
                ).to_dict()
                
        except Exception as e:
            logger.exception("Error processing message")
            return {
                "jsonrpc": "2.0",
                "id": message.get("id") if isinstance(message, dict) else None,
                "error": {
                    "code": -32700,
                    "message": f"Parse error: {str(e)}"
                }
            }
    
    async def _read_message(self) -> Optional[Dict[str, Any]]:
        """Read a message from stdin."""
        try:
            # Read the Content-Length header
            line = await asyncio.get_event_loop().run_in_executor(
                self._executor,
                sys.stdin.readline
            )
            if not line:
                return None
                
            if not line.startswith("Content-Length: "):
                logger.error(f"Invalid message header: {line.strip()}")
                return None
                
            # Read the content
            content_length = int(line[len("Content-Length: "):])
            await asyncio.get_event_loop().run_in_executor(
                self._executor,
                lambda: sys.stdin.read(2)  # Read the \r\n after the header
            )
            
            # Read the JSON content
            json_content = await asyncio.get_event_loop().run_in_executor(
                self._executor,
                lambda: sys.stdin.read(content_length)
            )
            
            return json.loads(json_content)
            
        except Exception as e:
            logger.exception("Error reading message from stdin")
            return None
    
    async def _write_message(self, message: Dict[str, Any]) -> None:
        """Write a message to stdout."""
        try:
            json_content = json.dumps(message)
            content = f"Content-Length: {len(json_content)}\r\n\r\n{json_content}"
            
            await asyncio.get_event_loop().run_in_executor(
                self._executor,
                lambda: sys.stdout.write(content)
            )
            sys.stdout.flush()
            
        except Exception as e:
            logger.exception("Error writing message to stdout")
    
    async def run(self) -> None:
        """Run the MCP server."""
        logger.info("Starting FastMCP 2.10 server...")
        
        # Set stdout to binary mode on Windows
        if sys.platform == "win32":
            import msvcrt
            import os
            msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
            msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
        
        while not self._shutdown:
            try:
                # Read a message
                message = await self._read_message()
                if message is None:
                    break
                
                # Process the message
                response = await self._process_message(message)
                
                # Send the response if there is one
                if response is not None:
                    await self._write_message(response)
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception("Error in main loop")
                break
        
        logger.info("Shutting down FastMCP server...")
