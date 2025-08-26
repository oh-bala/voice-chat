import openai
import logging
import asyncio
import json
from typing import Dict, List, Optional, Any
from config import Config
from mcp_client import MCPManager
from mcp_config import mcp_config_manager

class OpenAIClient:
    def __init__(self):
        # Validate configuration
        Config.validate()
        
        # Initialize OpenAI client
        self.client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
        
        # Initialize MCP manager
        self.mcp_manager = MCPManager()
        self.mcp_enabled = mcp_config_manager.get_global_setting("enable_mcp", True)
        
        # Conversation history
        self.conversation_history = [
            {
                "role": "system", 
                "content": "You are a helpful voice assistant. Provide clear, concise responses suitable for voice interaction. Keep responses relatively short and conversational."
            }
        ]
        
        # Initialize MCP connections if enabled
        if self.mcp_enabled:
            asyncio.create_task(self._initialize_mcp_connections())
    
    async def get_response(self, user_message):
        """
        Get a response from OpenAI for the given user message
        
        Args:
            user_message (str): The user's message
            
        Returns:
            str: The AI's response or None if error occurred
        """
        try:
            # Add user message to conversation history
            self.conversation_history.append({
                "role": "user",
                "content": user_message
            })
            
            # Prepare tools for OpenAI if MCP is enabled
            tools = []
            if self.mcp_enabled:
                tools = await self._get_mcp_tools()
            
            # Get response from OpenAI
            response = self.client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=self.conversation_history,
                max_tokens=300,  # Limit response length for voice
                temperature=0.7,
                tools=tools if tools else None,
                tool_choice="auto" if tools else None
            )
            
            # Extract the assistant's response
            assistant_message = response.choices[0].message.content
            
            # Handle tool calls if present
            if response.choices[0].message.tool_calls:
                tool_results = await self._handle_tool_calls(response.choices[0].message.tool_calls)
                if tool_results:
                    # Add tool results to conversation
                    self.conversation_history.append({
                        "role": "assistant",
                        "content": assistant_message,
                        "tool_calls": response.choices[0].message.tool_calls
                    })
                    self.conversation_history.append({
                        "role": "tool",
                        "content": tool_results
                    })
                    # Get final response after tool execution
                    final_response = await self._get_final_response()
                    return final_response
            
            # Add assistant's response to conversation history
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })
            
            # Keep conversation history manageable (last 10 messages)
            if len(self.conversation_history) > 11:  # 1 system + 10 conversation messages
                self.conversation_history = [self.conversation_history[0]] + self.conversation_history[-10:]
            
            return assistant_message
            
        except openai.RateLimitError:
            logging.error("OpenAI API rate limit exceeded")
            return "I'm sorry, I've reached my rate limit. Please try again later."
        except openai.AuthenticationError:
            logging.error("OpenAI API authentication failed")
            return "I'm sorry, there's an authentication issue. Please check your API key."
        except Exception as e:
            logging.error(f"Error getting OpenAI response: {e}")
            return "I'm sorry, I encountered an error. Please try again."
    
    def reset_conversation(self):
        """Reset the conversation history"""
        self.conversation_history = [
            {
                "role": "system", 
                "content": "You are a helpful voice assistant. Provide clear, concise responses suitable for voice interaction. Keep responses relatively short and conversational."
            }
        ]
        print("Conversation reset!")
    
    def get_conversation_summary(self):
        """Get a summary of the current conversation"""
        user_messages = [msg for msg in self.conversation_history if msg["role"] == "user"]
        assistant_messages = [msg for msg in self.conversation_history if msg["role"] == "assistant"]
        
        return {
            "total_exchanges": min(len(user_messages), len(assistant_messages)),
            "user_messages": len(user_messages),
            "assistant_messages": len(assistant_messages)
        }
    
    async def _initialize_mcp_connections(self):
        """Initialize MCP connections for enabled servers"""
        try:
            enabled_servers = mcp_config_manager.get_enabled_servers()
            for server in enabled_servers:
                if server.auto_connect:
                    success = await self.mcp_manager.add_client(server.name, server.url)
                    if success:
                        logging.info(f"Connected to MCP server: {server.name}")
                    else:
                        logging.warning(f"Failed to connect to MCP server: {server.name}")
        except Exception as e:
            logging.error(f"Error initializing MCP connections: {e}")
    
    async def _get_mcp_tools(self) -> List[Dict[str, Any]]:
        """Get MCP tools formatted for OpenAI"""
        tools = []
        try:
            for client_name in self.mcp_manager.get_available_clients():
                client_tools = self.mcp_manager.get_client_tools(client_name)
                for tool_name in client_tools:
                    tool_config = mcp_config_manager.get_tool_config(client_name, tool_name)
                    if tool_config and tool_config.enabled:
                        # Get tool description from MCP client
                        description = self.mcp_manager.clients[client_name].get_tool_description(tool_name)
                        if description:
                            tools.append({
                                "type": "function",
                                "function": {
                                    "name": f"{client_name}_{tool_name}",
                                    "description": description,
                                    "parameters": {
                                        "type": "object",
                                        "properties": {
                                            "client_name": {"type": "string", "description": "MCP client name"},
                                            "tool_name": {"type": "string", "description": "MCP tool name"},
                                            "arguments": {"type": "object", "description": "Tool arguments"}
                                        },
                                        "required": ["client_name", "tool_name", "arguments"]
                                    }
                                }
                            })
        except Exception as e:
            logging.error(f"Error getting MCP tools: {e}")
        return tools
    
    async def _handle_tool_calls(self, tool_calls) -> str:
        """Handle tool calls from OpenAI"""
        results = []
        try:
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                
                # Parse client and tool names from function name
                if "_" in function_name:
                    client_name, tool_name = function_name.split("_", 1)
                    
                    # Call the MCP tool
                    result = await self.mcp_manager.call_tool(client_name, tool_name, arguments.get("arguments", {}))
                    results.append(f"Tool {function_name} result: {result}")
                else:
                    results.append(f"Unknown tool: {function_name}")
            
            return "\n".join(results)
        except Exception as e:
            logging.error(f"Error handling tool calls: {e}")
            return f"Error executing tools: {str(e)}"
    
    async def _get_final_response(self) -> str:
        """Get final response after tool execution"""
        try:
            response = self.client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=self.conversation_history,
                max_tokens=300,
                temperature=0.7
            )
            
            assistant_message = response.choices[0].message.content
            
            # Add final response to conversation history
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })
            
            return assistant_message
        except Exception as e:
            logging.error(f"Error getting final response: {e}")
            return "I encountered an error while processing the tool results."
    
    async def shutdown(self):
        """Shutdown the OpenAI client and MCP connections"""
        try:
            await self.mcp_manager.shutdown()
            logging.info("OpenAI client and MCP connections shut down")
        except Exception as e:
            logging.error(f"Error during shutdown: {e}")
