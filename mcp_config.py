#!/usr/bin/env python3

import json
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

@dataclass
class MCPServerConfig:
    """Configuration for an MCP server"""
    name: str
    url: str
    description: str = ""
    enabled: bool = True
    auto_connect: bool = False
    timeout: int = 30
    retry_attempts: int = 3
    credentials: Optional[Dict[str, str]] = None

@dataclass
class MCPToolConfig:
    """Configuration for MCP tool usage"""
    tool_name: str
    client_name: str
    enabled: bool = True
    max_calls_per_minute: int = 10
    require_confirmation: bool = False
    auto_execute: bool = False

class MCPConfigurationManager:
    """Manages MCP configuration settings"""
    
    def __init__(self, config_file: str = "mcp_config.json"):
        self.config_file = Path(config_file)
        self.logger = logging.getLogger(__name__)
        
        # Default configurations
        self.servers: Dict[str, MCPServerConfig] = {}
        self.tools: Dict[str, MCPToolConfig] = {}
        self.global_settings = {
            "enable_mcp": True,
            "default_timeout": 30,
            "max_concurrent_connections": 5,
            "log_level": "INFO",
            "auto_reconnect": True,
            "connection_retry_delay": 5
        }
        
        # Load existing configuration
        self.load_configuration()
        
        # Add some default MCP servers if none exist
        if not self.servers:
            self._add_default_servers()
    
    def _add_default_servers(self):
        """Add some default MCP server configurations"""
        default_servers = [
            MCPServerConfig(
                name="github",
                url="ws://localhost:3000",
                description="GitHub MCP Server for repository operations",
                enabled=False,
                auto_connect=False
            ),
            MCPServerConfig(
                name="filesystem",
                url="ws://localhost:3001", 
                description="Filesystem MCP Server for file operations",
                enabled=False,
                auto_connect=False
            ),
            MCPServerConfig(
                name="weather",
                url="ws://localhost:3002",
                description="Weather MCP Server for weather information",
                enabled=False,
                auto_connect=False
            )
        ]
        
        for server in default_servers:
            self.add_server(server)
    
    def add_server(self, server_config: MCPServerConfig) -> bool:
        """Add a new MCP server configuration"""
        try:
            self.servers[server_config.name] = server_config
            self.save_configuration()
            self.logger.info(f"Added MCP server: {server_config.name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to add MCP server {server_config.name}: {e}")
            return False
    
    def remove_server(self, server_name: str) -> bool:
        """Remove an MCP server configuration"""
        try:
            if server_name in self.servers:
                del self.servers[server_name]
                self.save_configuration()
                self.logger.info(f"Removed MCP server: {server_name}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to remove MCP server {server_name}: {e}")
            return False
    
    def update_server(self, server_name: str, **kwargs) -> bool:
        """Update an existing MCP server configuration"""
        try:
            if server_name in self.servers:
                server = self.servers[server_name]
                for key, value in kwargs.items():
                    if hasattr(server, key):
                        setattr(server, key, value)
                self.save_configuration()
                self.logger.info(f"Updated MCP server: {server_name}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to update MCP server {server_name}: {e}")
            return False
    
    def get_server(self, server_name: str) -> Optional[MCPServerConfig]:
        """Get an MCP server configuration"""
        return self.servers.get(server_name)
    
    def get_enabled_servers(self) -> List[MCPServerConfig]:
        """Get list of enabled MCP servers"""
        return [server for server in self.servers.values() if server.enabled]
    
    def get_all_servers(self) -> List[MCPServerConfig]:
        """Get list of all MCP servers"""
        return list(self.servers.values())
    
    def add_tool_config(self, tool_config: MCPToolConfig) -> bool:
        """Add a new MCP tool configuration"""
        try:
            key = f"{tool_config.client_name}:{tool_config.tool_name}"
            self.tools[key] = tool_config
            self.save_configuration()
            self.logger.info(f"Added MCP tool config: {key}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to add MCP tool config: {e}")
            return False
    
    def get_tool_config(self, client_name: str, tool_name: str) -> Optional[MCPToolConfig]:
        """Get MCP tool configuration"""
        key = f"{client_name}:{tool_name}"
        return self.tools.get(key)
    
    def update_global_setting(self, key: str, value: Any) -> bool:
        """Update a global setting"""
        try:
            if key in self.global_settings:
                self.global_settings[key] = value
                self.save_configuration()
                self.logger.info(f"Updated global setting: {key} = {value}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to update global setting {key}: {e}")
            return False
    
    def get_global_setting(self, key: str, default: Any = None) -> Any:
        """Get a global setting"""
        return self.global_settings.get(key, default)
    
    def load_configuration(self):
        """Load configuration from file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                
                # Load servers
                self.servers.clear()
                for server_data in data.get('servers', []):
                    server = MCPServerConfig(**server_data)
                    self.servers[server.name] = server
                
                # Load tools
                self.tools.clear()
                for tool_data in data.get('tools', []):
                    tool = MCPToolConfig(**tool_data)
                    key = f"{tool.client_name}:{tool.tool_name}"
                    self.tools[key] = tool
                
                # Load global settings
                self.global_settings.update(data.get('global_settings', {}))
                
                self.logger.info(f"Loaded MCP configuration from {self.config_file}")
            else:
                self.logger.info("No existing MCP configuration found, using defaults")
                
        except Exception as e:
            self.logger.error(f"Failed to load MCP configuration: {e}")
    
    def save_configuration(self):
        """Save configuration to file"""
        try:
            # Prepare data for serialization
            data = {
                'servers': [asdict(server) for server in self.servers.values()],
                'tools': [asdict(tool) for tool in self.tools.values()],
                'global_settings': self.global_settings
            }
            
            # Create directory if it doesn't exist
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.logger.info(f"Saved MCP configuration to {self.config_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save MCP configuration: {e}")
    
    def validate_configuration(self) -> List[str]:
        """Validate the current configuration and return list of errors"""
        errors = []
        
        # Validate servers
        for server in self.servers.values():
            if not server.name:
                errors.append(f"Server missing name")
            if not server.url:
                errors.append(f"Server {server.name} missing URL")
            if not server.url.startswith(('ws://', 'wss://')):
                errors.append(f"Server {server.name} has invalid URL format")
        
        # Validate tools
        for tool in self.tools.values():
            if not tool.tool_name:
                errors.append("Tool missing name")
            if not tool.client_name:
                errors.append(f"Tool {tool.tool_name} missing client name")
            if tool.max_calls_per_minute < 1:
                errors.append(f"Tool {tool.tool_name} has invalid max calls per minute")
        
        # Validate global settings
        if self.global_settings.get('default_timeout', 0) < 1:
            errors.append("Default timeout must be at least 1 second")
        if self.global_settings.get('max_concurrent_connections', 0) < 1:
            errors.append("Max concurrent connections must be at least 1")
        
        return errors
    
    def export_configuration(self, file_path: str) -> bool:
        """Export configuration to a file"""
        try:
            data = {
                'servers': [asdict(server) for server in self.servers.values()],
                'tools': [asdict(tool) for tool in self.tools.values()],
                'global_settings': self.global_settings
            }
            
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.logger.info(f"Exported MCP configuration to {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export MCP configuration: {e}")
            return False
    
    def import_configuration(self, file_path: str) -> bool:
        """Import configuration from a file"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Clear existing configuration
            self.servers.clear()
            self.tools.clear()
            
            # Import servers
            for server_data in data.get('servers', []):
                server = MCPServerConfig(**server_data)
                self.servers[server.name] = server
            
            # Import tools
            for tool_data in data.get('tools', []):
                tool = MCPToolConfig(**tool_data)
                key = f"{tool.client_name}:{tool.tool_name}"
                self.tools[key] = tool
            
            # Import global settings
            self.global_settings.update(data.get('global_settings', {}))
            
            # Save the imported configuration
            self.save_configuration()
            
            self.logger.info(f"Imported MCP configuration from {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to import MCP configuration: {e}")
            return False

# Global configuration manager instance
mcp_config_manager = MCPConfigurationManager()
