# MCP (Model Context Protocol) Integration

This document describes the MCP integration implemented in the Voice Chat Assistant application.

## Overview

The Model Context Protocol (MCP) integration allows the voice chat assistant to connect to external MCP servers and use their tools and resources. This enables the assistant to perform actions like:

- File system operations
- Web searches
- Weather information
- Mathematical calculations
- GitHub operations
- And more through MCP-compatible servers

## Architecture

### Components

1. **MCP Client** (`mcp_client.py`)
   - Handles WebSocket connections to MCP servers
   - Manages tool discovery and execution
   - Supports multiple concurrent server connections

2. **MCP Configuration Manager** (`mcp_config.py`)
   - Manages server configurations
   - Handles tool settings and permissions
   - Provides import/export functionality

3. **MCP Configuration GUI** (`mcp_config_gui.py`)
   - User-friendly interface for managing MCP settings
   - Server configuration and testing
   - Tool management and validation

4. **OpenAI Integration** (`openai_client.py`)
   - Extends OpenAI client to support MCP tools
   - Handles tool calls from OpenAI responses
   - Manages conversation context with tool results

## Installation

### Prerequisites

The MCP integration requires additional dependencies. These are already included in `requirements.txt`:

```bash
pip install -r requirements.txt
```

### Dependencies

- `websockets>=12.0` - WebSocket client/server support
- `httpx>=0.25.0` - HTTP client for async requests
- `anyio>=4.0.0` - Async I/O utilities
- `pydantic>=2.0.0` - Data validation
- `aiofiles>=23.0.0` - Async file operations

## Configuration

### Basic Setup

1. **Enable MCP**: MCP is enabled by default. You can disable it in the configuration.

2. **Add MCP Servers**: Use the MCP Configuration GUI or edit the configuration file directly.

3. **Configure Tools**: Set up which tools are available and their permissions.

### Configuration File

The MCP configuration is stored in `mcp_config.json`:

```json
{
  "servers": [
    {
      "name": "github",
      "url": "ws://localhost:3000",
      "description": "GitHub MCP Server",
      "enabled": true,
      "auto_connect": false,
      "timeout": 30,
      "retry_attempts": 3
    }
  ],
  "tools": [
    {
      "tool_name": "create_repository",
      "client_name": "github",
      "enabled": true,
      "max_calls_per_minute": 10,
      "require_confirmation": false,
      "auto_execute": false
    }
  ],
  "global_settings": {
    "enable_mcp": true,
    "default_timeout": 30,
    "max_concurrent_connections": 5,
    "log_level": "INFO",
    "auto_reconnect": true,
    "connection_retry_delay": 5
  }
}
```

## Usage

### Starting the Application

1. **Run the main application**:
   ```bash
   python voice_chat_gui.py
   ```

2. **Access MCP Configuration**:
   - Click the "MCP Config" button in the main interface
   - Or run the configuration GUI directly:
   ```bash
   python mcp_config_gui.py
   ```

### Using MCP Tools

Once configured, you can use MCP tools through voice commands:

1. **Start the assistant** with the wake word: "Hey assistant"
2. **Ask for actions** that require MCP tools:
   - "What's the weather in New York?"
   - "Search for information about Python programming"
   - "Calculate 15 times 23"
   - "What time is it in Tokyo?"

### Example Voice Interactions

```
User: "Hey assistant"
Assistant: "Hello! I'm ready to help you."

User: "What's the weather like in London?"
Assistant: "Let me check the weather for you..."
[Tool call: get_weather with location="London"]
Assistant: "The weather in London is currently 18°C with partly cloudy skies."

User: "Calculate 25 squared plus 10"
Assistant: "Let me calculate that for you..."
[Tool call: calculate with expression="25**2 + 10"]
Assistant: "25 squared plus 10 equals 635."
```

## Testing

### Running Tests

1. **Integration Tests**:
   ```bash
   python test_mcp_integration.py
   ```

2. **Server Simulator**:
   ```bash
   python mcp_server_simulator.py
   ```

3. **Manual Testing**:
   - Start the MCP server simulator
   - Configure a test server in the MCP config GUI
   - Test tool calls through the voice interface

### Test Server Simulator

The included `mcp_server_simulator.py` provides a test MCP server with sample tools:

- `get_weather` - Returns simulated weather data
- `search_web` - Simulates web search results
- `calculate` - Performs mathematical calculations
- `get_time` - Returns current time information

To use the simulator:

1. Start the simulator:
   ```bash
   python mcp_server_simulator.py
   ```

2. Add a server configuration:
   - Name: "test"
   - URL: "ws://localhost:3000"
   - Enable auto-connect

3. Test the integration through the voice interface

## Advanced Configuration

### Server Management

#### Adding a New Server

1. Open the MCP Configuration GUI
2. Go to the "MCP Servers" tab
3. Click "Add Server"
4. Fill in the server details:
   - **Name**: Unique identifier for the server
   - **URL**: WebSocket URL (ws:// or wss://)
   - **Description**: Human-readable description
   - **Enabled**: Whether the server should be active
   - **Auto Connect**: Connect automatically on startup
   - **Timeout**: Connection timeout in seconds
   - **Retry Attempts**: Number of connection retries

#### Testing Server Connection

1. Select a server in the configuration GUI
2. Click "Test Connection"
3. Check the status in the application logs

### Tool Configuration

#### Tool Permissions

Each tool can be configured with:

- **Enabled**: Whether the tool is available
- **Max Calls/Min**: Rate limiting
- **Require Confirmation**: Ask user before executing
- **Auto Execute**: Execute automatically without confirmation

#### Tool Discovery

Tools are automatically discovered when connecting to MCP servers. The system will:

1. Connect to the server
2. Request available tools
3. Register tools with OpenAI
4. Make tools available for voice commands

### Global Settings

#### Performance Tuning

- **Default Timeout**: Maximum time to wait for tool responses
- **Max Concurrent Connections**: Limit on simultaneous server connections
- **Auto Reconnect**: Automatically reconnect on connection loss
- **Connection Retry Delay**: Time between reconnection attempts

#### Logging

- **Log Level**: Set logging verbosity (DEBUG, INFO, WARNING, ERROR)

## Troubleshooting

### Common Issues

#### Connection Failures

**Problem**: Cannot connect to MCP server
**Solutions**:
1. Check server URL format (must start with ws:// or wss://)
2. Verify server is running and accessible
3. Check firewall settings
4. Increase timeout values

#### Tool Not Available

**Problem**: Tool not appearing in voice commands
**Solutions**:
1. Verify tool is enabled in configuration
2. Check server connection status
3. Restart the application
4. Check application logs for errors

#### Performance Issues

**Problem**: Slow tool responses
**Solutions**:
1. Increase timeout values
2. Reduce max concurrent connections
3. Check network connectivity
4. Monitor server performance

### Debugging

#### Enable Debug Logging

1. Open MCP Configuration GUI
2. Go to "Global Settings" tab
3. Set "Log Level" to "DEBUG"
4. Restart the application

#### Check Logs

Logs are written to the console and can include:
- Connection attempts and failures
- Tool discovery and registration
- Tool execution results
- Error messages and stack traces

### Error Messages

#### Common Error Codes

- **-32700**: Parse error (invalid JSON)
- **-32601**: Method not found
- **-32603**: Internal error
- **Connection refused**: Server not running or unreachable
- **Timeout**: Server not responding within timeout period

## Security Considerations

### Authentication

- MCP servers may require authentication
- Store credentials securely
- Use environment variables for sensitive data

### Tool Permissions

- Review tool permissions before enabling
- Use confirmation for sensitive operations
- Monitor tool usage and results

### Network Security

- Use WSS (secure WebSocket) for production servers
- Verify server certificates
- Restrict server access to trusted sources

## Development

### Adding New MCP Servers

1. **Implement MCP Server**: Follow the MCP specification
2. **Test with Simulator**: Use the provided simulator for testing
3. **Add Configuration**: Configure server in the GUI
4. **Test Integration**: Verify tools work through voice interface

### Extending Tool Support

1. **Tool Discovery**: Tools are automatically discovered
2. **Parameter Validation**: MCP handles parameter validation
3. **Error Handling**: Implement proper error responses
4. **Documentation**: Provide clear tool descriptions

### Custom MCP Client

The MCP client can be extended for custom functionality:

```python
from mcp_client import MCPClient

# Create custom client
client = MCPClient("ws://localhost:3000", "custom-client")

# Connect to server
await client.connect()

# List available tools
tools = await client.list_tools()

# Call a tool
result = await client.call_tool("tool_name", {"param": "value"})
```

## API Reference

### MCPClient

```python
class MCPClient:
    async def connect() -> bool
    async def disconnect()
    async def list_tools() -> List[MCPTool]
    async def call_tool(name: str, arguments: Dict) -> Dict
    async def list_resources() -> List[MCPResource]
    async def read_resource(uri: str) -> Dict
```

### MCPManager

```python
class MCPManager:
    async def add_client(name: str, server_url: str) -> bool
    async def remove_client(name: str)
    async def call_tool(client_name: str, tool_name: str, arguments: Dict) -> Dict
    def get_available_clients() -> List[str]
    def get_client_tools(client_name: str) -> List[str]
    async def shutdown()
```

### MCPConfigurationManager

```python
class MCPConfigurationManager:
    def add_server(server_config: MCPServerConfig) -> bool
    def remove_server(server_name: str) -> bool
    def update_server(server_name: str, **kwargs) -> bool
    def get_server(server_name: str) -> Optional[MCPServerConfig]
    def get_enabled_servers() -> List[MCPServerConfig]
    def add_tool_config(tool_config: MCPToolConfig) -> bool
    def update_global_setting(key: str, value: Any) -> bool
    def validate_configuration() -> List[str]
```

## Contributing

### Development Setup

1. **Clone the repository**
2. **Install dependencies**: `pip install -r requirements.txt`
3. **Run tests**: `python test_mcp_integration.py`
4. **Start simulator**: `python mcp_server_simulator.py`
5. **Test integration**: Use the voice interface

### Code Style

- Follow PEP 8 guidelines
- Use type hints
- Add docstrings for all functions
- Include error handling
- Write tests for new features

### Testing

- Run integration tests before submitting changes
- Test with multiple MCP servers
- Verify error handling
- Check performance impact

## License

This MCP integration is part of the Voice Chat Assistant project and follows the same license terms.

## Support

For issues and questions:

1. Check the troubleshooting section
2. Review application logs
3. Test with the provided simulator
4. Create an issue with detailed information

## Changelog

### Version 1.0.0
- Initial MCP integration
- Basic client and server support
- Configuration management
- GUI for settings
- Integration with OpenAI client
- Test suite and simulator
