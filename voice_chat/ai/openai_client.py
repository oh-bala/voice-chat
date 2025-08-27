import openai
import logging
import asyncio
import json
import threading
from typing import Dict, List, Optional, Any
from config import Config
from voice_chat.mcp.mcp_client import MCPManager
from voice_chat.mcp.mcp_config import mcp_config_manager

class OpenAIClient:
    def __init__(self, language_code: str = None):
        Config.validate()
        self.language_code = language_code or Config.DEFAULT_LANGUAGE
        self.client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
        self.mcp_manager = MCPManager()
        self.mcp_enabled = mcp_config_manager.get_global_setting("enable_mcp", True)
        self.conversation_history = [
            {
                "role": "system",
                "content": self._get_system_prompt()
            }
        ]
        if self.mcp_enabled:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self._initialize_mcp_connections())
            except RuntimeError:
                threading.Thread(
                    target=lambda: asyncio.run(self._initialize_mcp_connections()),
                    daemon=True,
                ).start()

    def set_language(self, language_code: str):
        """Update the language for the AI client"""
        self.language_code = language_code
        # Update the system prompt with the new language
        if self.conversation_history and self.conversation_history[0]["role"] == "system":
            self.conversation_history[0]["content"] = self._get_system_prompt()

    def _get_system_prompt(self) -> str:
        """Get language-specific system prompt"""
        language_config = Config.get_language_config(self.language_code)
        language_name = language_config["name"]
        
        if self.language_code == "zh":
            return f"""你是一个有用的语音助手。请用{language_name}回复，提供清晰、简洁的回答，适合语音交互。保持回答相对简短和对话性。始终用{language_name}回复，不要使用其他语言。"""
        else:
            return f"""You are a helpful voice assistant. Please respond in {language_name}. Provide clear, concise responses suitable for voice interaction. Keep responses relatively short and conversational. Always respond in {language_name}, do not use other languages."""

    def get_response_sync(self, user_message: str) -> str:
        try:
            loop = asyncio.get_running_loop()
            # If an event loop is running, run in a worker thread to avoid blocking
            result_container = {}
            def runner():
                result_container["resp"] = asyncio.run(self.get_response(user_message))
            t = threading.Thread(target=runner, daemon=True)
            t.start()
            t.join()
            return result_container.get("resp")
        except RuntimeError:
            return asyncio.run(self.get_response(user_message))

    async def get_response(self, user_message):
        try:
            self.conversation_history.append({
                "role": "user",
                "content": user_message
            })
            tools = []
            if self.mcp_enabled:
                tools = await self._get_mcp_tools()
            response = self.client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=self.conversation_history,
                max_tokens=300,
                temperature=0.7,
                tools=tools if tools else None,
                tool_choice="auto" if tools else None
            )
            assistant_message = response.choices[0].message.content
            if response.choices[0].message.tool_calls:
                tool_results = await self._handle_tool_calls(response.choices[0].message.tool_calls)
                if tool_results:
                    self.conversation_history.append({
                        "role": "assistant",
                        "content": assistant_message,
                        "tool_calls": response.choices[0].message.tool_calls
                    })
                    self.conversation_history.append({
                        "role": "tool",
                        "content": tool_results
                    })
                    final_response = await self._get_final_response()
                    return final_response
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })
            if len(self.conversation_history) > 11:
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
        self.conversation_history = [
            {
                "role": "system",
                "content": self._get_system_prompt()
            }
        ]
        print("Conversation reset!")

    def get_conversation_summary(self):
        user_messages = [msg for msg in self.conversation_history if msg["role"] == "user"]
        assistant_messages = [msg for msg in self.conversation_history if msg["role"] == "assistant"]
        return {
            "total_exchanges": min(len(user_messages), len(assistant_messages)),
            "user_messages": len(user_messages),
            "assistant_messages": len(assistant_messages)
        }

    async def _initialize_mcp_connections(self):
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
        tools = []
        try:
            for client_name in self.mcp_manager.get_available_clients():
                client_tools = self.mcp_manager.get_client_tools(client_name)
                for tool_name in client_tools:
                    tool_config = mcp_config_manager.get_tool_config(client_name, tool_name)
                    if tool_config and tool_config.enabled:
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
        results = []
        try:
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                if "_" in function_name:
                    client_name, tool_name = function_name.split("_", 1)
                    result = await self.mcp_manager.call_tool(client_name, tool_name, arguments.get("arguments", {}))
                    results.append(f"Tool {function_name} result: {result}")
                else:
                    results.append(f"Unknown tool: {function_name}")
            return "\n".join(results)
        except Exception as e:
            logging.error(f"Error handling tool calls: {e}")
            return f"Error executing tools: {str(e)}"

    async def _get_final_response(self) -> str:
        try:
            response = self.client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=self.conversation_history,
                max_tokens=300,
                temperature=0.7
            )
            assistant_message = response.choices[0].message.content
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })
            return assistant_message
        except Exception as e:
            logging.error(f"Error getting final response: {e}")
            return "I encountered an error while processing the tool results."

    async def shutdown(self):
        try:
            await self.mcp_manager.shutdown()
            logging.info("OpenAI client and MCP connections shut down")
        except Exception as e:
            logging.error(f"Error during shutdown: {e}")
