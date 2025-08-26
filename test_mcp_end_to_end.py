#!/usr/bin/env python3

import asyncio
import sys
import os

# Add the current directory to the path
sys.path.append('.')

def test_mcp_imports():
    """Test that all MCP modules can be imported"""
    print("Testing MCP module imports...")
    
    try:
        from mcp_client import MCPClient, MCPManager
        print("✓ MCP Client imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import MCP Client: {e}")
        return False
    
    try:
        from mcp_config import mcp_config_manager, MCPServerConfig, MCPToolConfig
        print("✓ MCP Config imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import MCP Config: {e}")
        return False
    
    try:
        from mcp_config_gui import MCPConfigGUI
        print("✓ MCP Config GUI imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import MCP Config GUI: {e}")
        return False
    
    try:
        from openai_client import OpenAIClient
        print("✓ OpenAI Client imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import OpenAI Client: {e}")
        return False
    
    return True

def test_mcp_configuration():
    """Test MCP configuration functionality"""
    print("\nTesting MCP configuration...")
    
    try:
        from mcp_config import mcp_config_manager, MCPServerConfig
        
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
            print("✓ Successfully added test server")
        else:
            print("✗ Failed to add test server")
            return False
        
        # Test getting the server
        server = mcp_config_manager.get_server("test_server")
        if server and server.name == "test_server":
            print("✓ Successfully retrieved test server")
        else:
            print("✗ Failed to retrieve test server")
            return False
        
        # Cleanup
        mcp_config_manager.remove_server("test_server")
        print("✓ Successfully removed test server")
        
        return True
        
    except Exception as e:
        print(f"✗ MCP configuration test failed: {e}")
        return False

async def test_mcp_client():
    """Test MCP client functionality"""
    print("\nTesting MCP client...")
    
    try:
        from mcp_client import MCPClient
        
        # Test client creation
        client = MCPClient("ws://localhost:3000", "test-client")
        print("✓ Successfully created MCP client")
        
        # Test connection (should fail gracefully for non-existent server)
        connected = await client.connect()
        if not connected:
            print("✓ Connection failed gracefully as expected")
        else:
            print("✗ Connection should have failed")
            return False
        
        # Test disconnect
        await client.disconnect()
        print("✓ Successfully disconnected client")
        
        return True
        
    except Exception as e:
        print(f"✗ MCP client test failed: {e}")
        return False

async def test_openai_integration():
    """Test OpenAI integration with MCP"""
    print("\nTesting OpenAI integration...")
    
    try:
        from openai_client import OpenAIClient
        
        # Test OpenAI client creation
        openai_client = OpenAIClient()
        print("✓ Successfully created OpenAI client")
        
        # Test MCP tools formatting
        tools = await openai_client._get_mcp_tools()
        if isinstance(tools, list):
            print(f"✓ Successfully formatted {len(tools)} MCP tools")
        else:
            print("✗ Failed to format MCP tools")
            return False
        
        # Test shutdown
        await openai_client.shutdown()
        print("✓ Successfully shut down OpenAI client")
        
        return True
        
    except Exception as e:
        print(f"✗ OpenAI integration test failed: {e}")
        return False

def test_voice_chat_integration():
    """Test voice chat GUI integration"""
    print("\nTesting Voice Chat GUI integration...")
    
    try:
        from voice_chat_gui import VoiceChatGUI
        print("✓ Successfully imported Voice Chat GUI")
        
        # Test that the MCP config button method exists
        if hasattr(VoiceChatGUI, 'open_mcp_config'):
            print("✓ MCP config button method exists")
        else:
            print("✗ MCP config button method missing")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Voice Chat GUI integration test failed: {e}")
        return False

async def main():
    """Run all end-to-end tests"""
    print("=" * 60)
    print("MCP INTEGRATION END-TO-END TESTS")
    print("=" * 60)
    
    tests = [
        ("Module Imports", test_mcp_imports),
        ("Configuration", test_mcp_configuration),
        ("MCP Client", test_mcp_client),
        ("OpenAI Integration", test_openai_integration),
        ("Voice Chat Integration", test_voice_chat_integration),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            if result:
                passed += 1
                print(f"✓ {test_name} PASSED")
            else:
                print(f"✗ {test_name} FAILED")
                
        except Exception as e:
            print(f"✗ {test_name} FAILED with exception: {e}")
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! MCP integration is working correctly.")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the issues above.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
