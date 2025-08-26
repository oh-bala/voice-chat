#!/usr/bin/env python3

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
import httpx
import websockets
from websockets.exceptions import ConnectionClosed
import anyio
from pydantic import BaseModel, Field

class MCPMessageType(Enum):
    """MCP message types"""
    HELLO = "hello"
    HELLO_ACK = "hello_ack"
    LIST_TOOLS = "list_tools"
    LIST_TOOLS_RESULT = "list_tools_result"
    CALL_TOOL = "call_tool"
    CALL_TOOL_RESULT = "call_tool_result"
    LIST_RESOURCES = "list_resources"
    LIST_RESOURCES_RESULT = "list_resources_result"
    READ_RESOURCE = "read_resource"
    READ_RESOURCE_RESULT = "read_resource_result"
    ERROR = "error"

@dataclass
class MCPTool:
    """Represents an MCP tool"""
    name: str
    description: str
    inputSchema: Dict[str, Any]
    parameters: Dict[str, Any]

@dataclass
class MCPResource:
    """Represents an MCP resource"""
    uri: str
    name: str
    description: str
    mimeType: str

class MCPMessage(BaseModel):
    """Base MCP message"""
    jsonrpc: str = "2.0"
    id: Optional[str] = None
    method: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None

class MCPClient:
    """MCP Client for communicating with MCP servers"""
    
    def __init__(self, server_url: str, client_name: str = "voice-chat-assistant"):
        self.server_url = server_url
        self.client_name = client_name
        self.websocket = None
        self.connected = False
        self.message_id_counter = 0
        self.pending_requests: Dict[str, asyncio.Future] = {}
        self.tools: List[MCPTool] = []
        self.resources: List[MCPResource] = []
        self.logger = logging.getLogger(__name__)
        
    async def connect(self) -> bool:
        """Connect to the MCP server"""
        try:
            self.websocket = await websockets.connect(self.server_url)
            self.connected = True
            hello_message = MCPMessage(
                id=str(self._get_next_id()),
                method="hello",
                params={
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}, "resources": {}},
                    "clientInfo": {"name": self.client_name, "version": "1.0.0"}
                }
            )
            await self._send_message(hello_message)
            asyncio.create_task(self._message_listener())
            self.logger.info(f"Connected to MCP server: {self.server_url}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to MCP server: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from the MCP server"""
        if self.websocket:
            await self.websocket.close()
            self.connected = False
            self.logger.info("Disconnected from MCP server")
    
    async def list_tools(self) -> List[MCPTool]:
        if not self.connected:
            raise ConnectionError("Not connected to MCP server")
        message = MCPMessage(id=str(self._get_next_id()), method="tools/list")
        response = await self._send_request(message)
        if response.get("error"):
            raise Exception(f"MCP error: {response['error']}")
        tools_data = response.get("result", {}).get("tools", [])
        self.tools = [MCPTool(**tool) for tool in tools_data]
        return self.tools
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if not self.connected:
            raise ConnectionError("Not connected to MCP server")
        message = MCPMessage(
            id=str(self._get_next_id()),
            method="tools/call",
            params={"name": tool_name, "arguments": arguments}
        )
        response = await self._send_request(message)
        if response.get("error"):
            raise Exception(f"MCP error: {response['error']}")
        return response.get("result", {})
    
    async def list_resources(self) -> List[MCPResource]:
        if not self.connected:
            raise ConnectionError("Not connected to MCP server")
        message = MCPMessage(id=str(self._get_next_id()), method="resources/list")
        response = await self._send_request(message)
        if response.get("error"):
            raise Exception(f"MCP error: {response['error']}")
        resources_data = response.get("result", {}).get("resources", [])
        self.resources = [MCPResource(**resource) for resource in resources_data]
        return self.resources
    
    async def read_resource(self, uri: str) -> Dict[str, Any]:
        if not self.connected:
            raise ConnectionError("Not connected to MCP server")
        message = MCPMessage(id=str(self._get_next_id()), method="resources/read", params={"uri": uri})
        response = await self._send_request(message)
        if response.get("error"):
            raise Exception(f"MCP error: {response['error']}")
        return response.get("result", {})
    
    def _get_next_id(self) -> int:
        self.message_id_counter += 1
        return self.message_id_counter
    
    async def _send_message(self, message: MCPMessage):
        if not self.websocket:
            raise ConnectionError("WebSocket not connected")
        message_data = message.model_dump(exclude_none=True)
        await self.websocket.send(json.dumps(message_data))
    
    async def _send_request(self, message: MCPMessage) -> Dict[str, Any]:
        future = asyncio.Future()
        self.pending_requests[message.id] = future
        await self._send_message(message)
        try:
            response = await asyncio.wait_for(future, timeout=30.0)
            return response
        finally:
            if message.id in self.pending_requests:
                del self.pending_requests[message.id]
    
    async def _message_listener(self):
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    await self._handle_message(data)
                except json.JSONDecodeError as e:
                    self.logger.error(f"Invalid JSON message: {e}")
                except Exception as e:
                    self.logger.error(f"Error handling message: {e}")
        except ConnectionClosed:
            self.logger.info("WebSocket connection closed")
        except Exception as e:
            self.logger.error(f"Error in message listener: {e}")
        finally:
            self.connected = False
    
    async def _handle_message(self, data: Dict[str, Any]):
        message_id = data.get("id")
        if message_id and message_id in self.pending_requests:
            future = self.pending_requests[message_id]
            if not future.done():
                future.set_result(data)
        else:
            self.logger.debug(f"Received message: {data}")
    
    def get_available_tools(self) -> List[str]:
        return [tool.name for tool in self.tools]
    
    def get_tool_description(self, tool_name: str) -> Optional[str]:
        for tool in self.tools:
            if tool.name == tool_name:
                return tool.description
        return None

class MCPManager:
    """Manager for multiple MCP clients"""
    
    def __init__(self):
        self.clients: Dict[str, MCPClient] = {}
        self.logger = logging.getLogger(__name__)
    
    async def add_client(self, name: str, server_url: str) -> bool:
        try:
            client = MCPClient(server_url, f"voice-chat-{name}")
            if await client.connect():
                self.clients[name] = client
                self.logger.info(f"Added MCP client: {name}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to add MCP client {name}: {e}")
            return False
    
    async def remove_client(self, name: str):
        if name in self.clients:
            await self.clients[name].disconnect()
            del self.clients[name]
            self.logger.info(f"Removed MCP client: {name}")
    
    async def call_tool(self, client_name: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if client_name not in self.clients:
            raise ValueError(f"MCP client '{client_name}' not found")
        return await self.clients[client_name].call_tool(tool_name, arguments)
    
    def get_available_clients(self) -> List[str]:
        return list(self.clients.keys())
    
    def get_client_tools(self, client_name: str) -> List[str]:
        if client_name not in self.clients:
            return []
        return self.clients[client_name].get_available_tools()
    
    async def shutdown(self):
        for name in list(self.clients.keys()):
            await self.remove_client(name)
