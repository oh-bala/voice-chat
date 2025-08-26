#!/usr/bin/env python3

import asyncio
import json
import logging
import sys
from typing import Dict, Any

# Add the current directory to the path to import our modules
sys.path.append('.')

from mcp_client import MCPClient, MCPManager
from mcp_config import mcp_config_manager, MCPServerConfig, MCPToolConfig
from openai_client import OpenAIClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MCPIntegrationTester:
    """Test MCP integration functionality"""
    
    def __init__(self):
        self.mcp_manager = MCPManager()
        self.test_results = []
    
    async def run_all_tests(self):
        """Run all MCP integration tests"""
        logger.info("Starting MCP Integration Tests")
        
        try:
            # Test 1: Configuration Management
            await self.test_configuration_management()
            
            # Test 2: MCP Client Connection
            await self.test_mcp_client_connection()
            
            # Test 3: Tool Discovery
            await self.test_tool_discovery()
            
            # Test 4: Tool Execution
            await self.test_tool_execution()
            
            # Test 5: OpenAI Integration
            await self.test_openai_integration()
            
            # Test 6: Error Handling
            await self.test_error_handling()
            
            # Print test results
            self.print_test_results()
            
        except Exception as e:
            logger.error(f"Test suite failed: {e}")
            self.add_test_result("Test Suite", False, f"Test suite failed: {e}")
            self.print_test_results()
    
    async def test_configuration_management(self):
        """Test MCP configuration management"""
        logger.info("Testing Configuration Management...")
        
        try:
            # Test adding a server
            test_server = MCPServerConfig(
                name="test_server",
                url="ws://localhost:3000",
                description="Test MCP Server",
                enabled=True,
                auto_connect=False
            )
            
            success = mcp_config_manager.add_server(test_server)
            if success:
                self.add_test_result("Add Server", True, "Successfully added test server")
            else:
                self.add_test_result("Add Server", False, "Failed to add test server")
            
            # Test getting server
            server = mcp_config_manager.get_server("test_server")
            if server and server.name == "test_server":
                self.add_test_result("Get Server", True, "Successfully retrieved test server")
            else:
                self.add_test_result("Get Server", False, "Failed to retrieve test server")
            
            # Test updating server
            success = mcp_config_manager.update_server("test_server", description="Updated description")
            if success:
                self.add_test_result("Update Server", True, "Successfully updated test server")
            else:
                self.add_test_result("Update Server", False, "Failed to update test server")
            
            # Test adding tool config
            test_tool = MCPToolConfig(
                tool_name="test_tool",
                client_name="test_client",
                enabled=True,
                max_calls_per_minute=10,
                require_confirmation=False,
                auto_execute=False
            )
            
            success = mcp_config_manager.add_tool_config(test_tool)
            if success:
                self.add_test_result("Add Tool Config", True, "Successfully added tool config")
            else:
                self.add_test_result("Add Tool Config", False, "Failed to add tool config")
            
            # Test global settings
            success = mcp_config_manager.update_global_setting("test_setting", "test_value")
            if success:
                self.add_test_result("Update Global Setting", True, "Successfully updated global setting")
            else:
                self.add_test_result("Update Global Setting", False, "Failed to update global setting")
            
            # Test configuration validation
            errors = mcp_config_manager.validate_configuration()
            if not errors:
                self.add_test_result("Configuration Validation", True, "Configuration is valid")
            else:
                self.add_test_result("Configuration Validation", False, f"Configuration has errors: {errors}")
            
            # Cleanup
            mcp_config_manager.remove_server("test_server")
            
        except Exception as e:
            self.add_test_result("Configuration Management", False, f"Configuration test failed: {e}")
    
    async def test_mcp_client_connection(self):
        """Test MCP client connection functionality"""
        logger.info("Testing MCP Client Connection...")
        
        try:
            # Test with a mock server URL (this will fail but test the connection logic)
            test_url = "ws://localhost:9999"  # Non-existent server
            
            client = MCPClient(test_url, "test-client")
            
            # Test connection (should fail gracefully)
            connected = await client.connect()
            if not connected:
                self.add_test_result("MCP Client Connection", True, "Connection failed gracefully as expected")
            else:
                self.add_test_result("MCP Client Connection", False, "Connection should have failed")
            
            # Test client properties
            if client.server_url == test_url:
                self.add_test_result("MCP Client Properties", True, "Client properties set correctly")
            else:
                self.add_test_result("MCP Client Properties", False, "Client properties not set correctly")
            
            # Test disconnect
            await client.disconnect()
            if not client.connected:
                self.add_test_result("MCP Client Disconnect", True, "Client disconnected successfully")
            else:
                self.add_test_result("MCP Client Disconnect", False, "Client failed to disconnect")
            
        except Exception as e:
            self.add_test_result("MCP Client Connection", False, f"Client connection test failed: {e}")
    
    async def test_tool_discovery(self):
        """Test MCP tool discovery"""
        logger.info("Testing Tool Discovery...")
        
        try:
            # Test with manager
            clients = self.mcp_manager.get_available_clients()
            if isinstance(clients, list):
                self.add_test_result("Get Available Clients", True, f"Found {len(clients)} clients")
            else:
                self.add_test_result("Get Available Clients", False, "Failed to get available clients")
            
            # Test tool listing (with no clients, should return empty list)
            if len(clients) == 0:
                self.add_test_result("Tool Discovery (No Clients)", True, "Correctly handled no clients")
            else:
                for client_name in clients:
                    tools = self.mcp_manager.get_client_tools(client_name)
                    if isinstance(tools, list):
                        self.add_test_result(f"Tool Discovery ({client_name})", True, f"Found {len(tools)} tools")
                    else:
                        self.add_test_result(f"Tool Discovery ({client_name})", False, "Failed to get tools")
            
        except Exception as e:
            self.add_test_result("Tool Discovery", False, f"Tool discovery test failed: {e}")
    
    async def test_tool_execution(self):
        """Test MCP tool execution"""
        logger.info("Testing Tool Execution...")
        
        try:
            # Test calling tool on non-existent client
            try:
                result = await self.mcp_manager.call_tool("non_existent_client", "non_existent_tool", {})
                self.add_test_result("Tool Execution (Non-existent)", False, "Should have raised an exception")
            except ValueError:
                self.add_test_result("Tool Execution (Non-existent)", True, "Correctly handled non-existent client")
            except Exception as e:
                self.add_test_result("Tool Execution (Non-existent)", False, f"Unexpected exception: {e}")
            
        except Exception as e:
            self.add_test_result("Tool Execution", False, f"Tool execution test failed: {e}")
    
    async def test_openai_integration(self):
        """Test OpenAI integration with MCP"""
        logger.info("Testing OpenAI Integration...")
        
        try:
            # Test OpenAI client initialization
            openai_client = OpenAIClient()
            
            # Test MCP tools formatting
            tools = await openai_client._get_mcp_tools()
            if isinstance(tools, list):
                self.add_test_result("OpenAI MCP Tools Formatting", True, f"Formatted {len(tools)} tools")
            else:
                self.add_test_result("OpenAI MCP Tools Formatting", False, "Failed to format MCP tools")
            
            # Test tool call handling
            mock_tool_calls = []
            result = await openai_client._handle_tool_calls(mock_tool_calls)
            if result == "":
                self.add_test_result("OpenAI Tool Call Handling", True, "Handled empty tool calls correctly")
            else:
                self.add_test_result("OpenAI Tool Call Handling", False, "Failed to handle empty tool calls")
            
            # Test shutdown
            await openai_client.shutdown()
            self.add_test_result("OpenAI Client Shutdown", True, "Client shutdown successfully")
            
        except Exception as e:
            self.add_test_result("OpenAI Integration", False, f"OpenAI integration test failed: {e}")
    
    async def test_error_handling(self):
        """Test error handling in MCP components"""
        logger.info("Testing Error Handling...")
        
        try:
            # Test invalid server URL
            try:
                client = MCPClient("invalid_url", "test-client")
                await client.connect()
                self.add_test_result("Error Handling (Invalid URL)", False, "Should have failed with invalid URL")
            except Exception:
                self.add_test_result("Error Handling (Invalid URL)", True, "Correctly handled invalid URL")
            
            # Test invalid configuration
            try:
                invalid_server = MCPServerConfig(name="", url="", description="")
                mcp_config_manager.add_server(invalid_server)
                self.add_test_result("Error Handling (Invalid Config)", False, "Should have failed with invalid config")
            except Exception:
                self.add_test_result("Error Handling (Invalid Config)", True, "Correctly handled invalid config")
            
        except Exception as e:
            self.add_test_result("Error Handling", False, f"Error handling test failed: {e}")
    
    def add_test_result(self, test_name: str, success: bool, message: str):
        """Add a test result"""
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message
        })
        status = "PASS" if success else "FAIL"
        logger.info(f"{status}: {test_name} - {message}")
    
    def print_test_results(self):
        """Print test results summary"""
        print("\n" + "="*60)
        print("MCP INTEGRATION TEST RESULTS")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print("\nDetailed Results:")
        print("-" * 60)
        
        for result in self.test_results:
            status = "✓ PASS" if result["success"] else "✗ FAIL"
            print(f"{status:<10} {result['test']}")
            print(f"           {result['message']}")
            print()
        
        if failed_tests > 0:
            print("FAILED TESTS:")
            print("-" * 60)
            for result in self.test_results:
                if not result["success"]:
                    print(f"✗ {result['test']}: {result['message']}")
        
        print("="*60)
        
        if failed_tests == 0:
            print("🎉 ALL TESTS PASSED! MCP integration is working correctly.")
        else:
            print(f"⚠️  {failed_tests} test(s) failed. Please review the issues above.")

async def main():
    """Main test function"""
    tester = MCPIntegrationTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    # Run the tests
    asyncio.run(main())
