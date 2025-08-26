#!/usr/bin/env python3

import asyncio
import json
import logging
import websockets
from websockets.server import serve
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class SimulatedTool:
    """Simulated MCP tool"""
    name: str
    description: str
    parameters: Dict[str, Any]

class MCPServerSimulator:
    """Simple MCP server simulator for testing"""
    
    def __init__(self, port: int = 3000):
        self.port = port
        self.clients = set()
        self.tools = self._create_sample_tools()
        self.resources = self._create_sample_resources()
        
    def _create_sample_tools(self) -> List[SimulatedTool]:
        """Create sample tools for testing"""
        return [
            SimulatedTool(
                name="get_weather",
                description="Get current weather information for a location",
                parameters={
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "City name or coordinates"
                        },
                        "units": {
                            "type": "string",
                            "enum": ["celsius", "fahrenheit"],
                            "default": "celsius"
                        }
                    },
                    "required": ["location"]
                }
            ),
            SimulatedTool(
                name="search_web",
                description="Search the web for information",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        },
                        "max_results": {
                            "type": "integer",
                            "default": 5
                        }
                    },
                    "required": ["query"]
                }
            ),
            SimulatedTool(
                name="calculate",
                description="Perform mathematical calculations",
                parameters={
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "Mathematical expression to evaluate"
                        }
                    },
                    "required": ["expression"]
                }
            ),
            SimulatedTool(
                name="get_time",
                description="Get current time and date information",
                parameters={
                    "type": "object",
                    "properties": {
                        "timezone": {
                            "type": "string",
                            "description": "Timezone (e.g., 'UTC', 'America/New_York')",
                            "default": "UTC"
                        }
                    }
                }
            )
        ]
    
    def _create_sample_resources(self) -> List[Dict[str, Any]]:
        """Create sample resources for testing"""
        return [
            {
                "uri": "file:///sample/config.json",
                "name": "Sample Configuration",
                "description": "Sample configuration file",
                "mimeType": "application/json"
            },
            {
                "uri": "file:///sample/readme.md",
                "name": "Sample Readme",
                "description": "Sample readme file",
                "mimeType": "text/markdown"
            }
        ]
    
    async def handle_client(self, websocket, path):
        """Handle client connection"""
        client_id = id(websocket)
        self.clients.add(websocket)
        logger.info(f"Client {client_id} connected")
        
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    response = await self.process_message(data)
                    if response:
                        await websocket.send(json.dumps(response))
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON from client {client_id}")
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": -32700,
                            "message": "Parse error"
                        }
                    }
                    await websocket.send(json.dumps(error_response))
                except Exception as e:
                    logger.error(f"Error processing message from client {client_id}: {e}")
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": data.get("id") if 'data' in locals() else None,
                        "error": {
                            "code": -32603,
                            "message": "Internal error"
                        }
                    }
                    await websocket.send(json.dumps(error_response))
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client {client_id} disconnected")
        finally:
            self.clients.discard(websocket)
    
    async def process_message(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process incoming MCP message"""
        message_id = data.get("id")
        method = data.get("method")
        params = data.get("params", {})
        
        logger.info(f"Processing message: {method}")
        
        if method == "hello":
            return await self.handle_hello(message_id, params)
        elif method == "tools/list":
            return await self.handle_list_tools(message_id)
        elif method == "tools/call":
            return await self.handle_call_tool(message_id, params)
        elif method == "resources/list":
            return await self.handle_list_resources(message_id)
        elif method == "resources/read":
            return await self.handle_read_resource(message_id, params)
        else:
            return {
                "jsonrpc": "2.0",
                "id": message_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
    
    async def handle_hello(self, message_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle hello message"""
        logger.info("Handling hello message")
        return {
            "jsonrpc": "2.0",
            "id": message_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                    "resources": {}
                },
                "serverInfo": {
                    "name": "MCP Server Simulator",
                    "version": "1.0.0"
                }
            }
        }
    
    async def handle_list_tools(self, message_id: str) -> Dict[str, Any]:
        """Handle tools/list message"""
        logger.info("Handling list tools message")
        
        tools_data = []
        for tool in self.tools:
            tools_data.append({
                "name": tool.name,
                "description": tool.description,
                "inputSchema": {
                    "type": "object",
                    "properties": tool.parameters.get("properties", {}),
                    "required": tool.parameters.get("required", [])
                }
            })
        
        return {
            "jsonrpc": "2.0",
            "id": message_id,
            "result": {
                "tools": tools_data
            }
        }
    
    async def handle_call_tool(self, message_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call message"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        logger.info(f"Handling tool call: {tool_name} with args: {arguments}")
        
        # Simulate tool execution
        result = await self.simulate_tool_execution(tool_name, arguments)
        
        return {
            "jsonrpc": "2.0",
            "id": message_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": result
                    }
                ]
            }
        }
    
    async def handle_list_resources(self, message_id: str) -> Dict[str, Any]:
        """Handle resources/list message"""
        logger.info("Handling list resources message")
        
        return {
            "jsonrpc": "2.0",
            "id": message_id,
            "result": {
                "resources": self.resources
            }
        }
    
    async def handle_read_resource(self, message_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources/read message"""
        uri = params.get("uri")
        logger.info(f"Handling read resource: {uri}")
        
        # Simulate resource content
        if "config.json" in uri:
            content = {
                "name": "Sample Config",
                "version": "1.0.0",
                "settings": {
                    "debug": True,
                    "timeout": 30
                }
            }
        elif "readme.md" in uri:
            content = "# Sample Readme\n\nThis is a sample readme file for testing."
        else:
            content = "Resource not found"
        
        return {
            "jsonrpc": "2.0",
            "id": message_id,
            "result": {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json" if "json" in uri else "text/plain",
                        "text": json.dumps(content) if isinstance(content, dict) else content
                    }
                ]
            }
        }
    
    async def simulate_tool_execution(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Simulate tool execution"""
        await asyncio.sleep(0.1)  # Simulate processing time
        
        if tool_name == "get_weather":
            location = arguments.get("location", "Unknown")
            units = arguments.get("units", "celsius")
            return f"Weather in {location}: 22°{units.upper()[:1]}, Partly Cloudy"
        
        elif tool_name == "search_web":
            query = arguments.get("query", "")
            max_results = arguments.get("max_results", 5)
            return f"Search results for '{query}': Found {max_results} relevant results"
        
        elif tool_name == "calculate":
            expression = arguments.get("expression", "")
            try:
                # Simple evaluation (in production, use safer methods)
                result = eval(expression)
                return f"Result of {expression} = {result}"
            except Exception as e:
                return f"Error calculating {expression}: {str(e)}"
        
        elif tool_name == "get_time":
            timezone = arguments.get("timezone", "UTC")
            import datetime
            now = datetime.datetime.now()
            return f"Current time in {timezone}: {now.strftime('%Y-%m-%d %H:%M:%S')}"
        
        else:
            return f"Unknown tool: {tool_name}"
    
    async def start_server(self):
        """Start the MCP server simulator"""
        logger.info(f"Starting MCP Server Simulator on port {self.port}")
        
        async with serve(self.handle_client, "localhost", self.port):
            logger.info(f"MCP Server Simulator is running on ws://localhost:{self.port}")
            logger.info("Available tools:")
            for tool in self.tools:
                logger.info(f"  - {tool.name}: {tool.description}")
            
            # Keep the server running
            await asyncio.Future()  # Run forever
    
    def stop_server(self):
        """Stop the server"""
        logger.info("Stopping MCP Server Simulator")
        # This would need to be implemented with proper server shutdown

async def main():
    """Main function to run the MCP server simulator"""
    simulator = MCPServerSimulator(port=3000)
    
    try:
        await simulator.start_server()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
