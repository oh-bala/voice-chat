#!/usr/bin/env python3

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
from typing import Dict, List, Optional
from voice_chat.mcp.mcp_config import mcp_config_manager, MCPServerConfig, MCPToolConfig

class MCPConfigGUI:
    """GUI for managing MCP configuration"""
    
    def __init__(self, parent=None):
        self.parent = parent
        self.root = tk.Toplevel(parent) if parent else tk.Tk()
        self.root.title("MCP Configuration")
        self.root.geometry("900x700")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Current selection
        self.selected_server = None
        self.selected_tool = None
        
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """Setup the user interface"""
        # Main notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Servers tab
        self.setup_servers_tab()
        
        # Tools tab
        self.setup_tools_tab()
        
        # Global Settings tab
        self.setup_global_settings_tab()
        
        # Import/Export tab
        self.setup_import_export_tab()
    
    def setup_servers_tab(self):
        """Setup the servers configuration tab"""
        servers_frame = ttk.Frame(self.notebook)
        self.notebook.add(servers_frame, text="MCP Servers")
        
        # Left panel - Server list
        left_frame = ttk.Frame(servers_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        ttk.Label(left_frame, text="MCP Servers", font=("Arial", 12, "bold")).pack(pady=(0, 10))
        
        # Server listbox
        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.server_listbox = tk.Listbox(list_frame, selectmode=tk.SINGLE)
        self.server_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.server_listbox.bind('<<ListboxSelect>>', self.on_server_select)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.server_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.server_listbox.config(yscrollcommand=scrollbar.set)
        
        # Server buttons
        button_frame = ttk.Frame(left_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="Add Server", command=self.add_server).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Remove Server", command=self.remove_server).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Test Connection", command=self.test_server_connection).pack(side=tk.LEFT)
        
        # Right panel - Server details
        right_frame = ttk.Frame(servers_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        ttk.Label(right_frame, text="Server Details", font=("Arial", 12, "bold")).pack(pady=(0, 10))
        
        # Server details form
        details_frame = ttk.LabelFrame(right_frame, text="Configuration", padding="10")
        details_frame.pack(fill=tk.BOTH, expand=True)
        
        # Name
        ttk.Label(details_frame, text="Name:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.server_name_var = tk.StringVar()
        self.server_name_entry = ttk.Entry(details_frame, textvariable=self.server_name_var)
        self.server_name_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=2)
        
        # URL
        ttk.Label(details_frame, text="URL:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.server_url_var = tk.StringVar()
        self.server_url_entry = ttk.Entry(details_frame, textvariable=self.server_url_var)
        self.server_url_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=2)
        
        # Description
        ttk.Label(details_frame, text="Description:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.server_desc_var = tk.StringVar()
        self.server_desc_entry = ttk.Entry(details_frame, textvariable=self.server_desc_var)
        self.server_desc_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=2)
        
        # Enabled
        self.server_enabled_var = tk.BooleanVar()
        self.server_enabled_check = ttk.Checkbutton(details_frame, text="Enabled", variable=self.server_enabled_var)
        self.server_enabled_check.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        # Auto Connect
        self.server_auto_connect_var = tk.BooleanVar()
        self.server_auto_connect_check = ttk.Checkbutton(details_frame, text="Auto Connect", variable=self.server_auto_connect_var)
        self.server_auto_connect_check.grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        # Timeout
        ttk.Label(details_frame, text="Timeout (seconds):").grid(row=5, column=0, sticky=tk.W, pady=2)
        self.server_timeout_var = tk.StringVar(value="30")
        self.server_timeout_entry = ttk.Entry(details_frame, textvariable=self.server_timeout_var)
        self.server_timeout_entry.grid(row=5, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=2)
        
        # Retry Attempts
        ttk.Label(details_frame, text="Retry Attempts:").grid(row=6, column=0, sticky=tk.W, pady=2)
        self.server_retry_var = tk.StringVar(value="3")
        self.server_retry_entry = ttk.Entry(details_frame, textvariable=self.server_retry_var)
        self.server_retry_entry.grid(row=6, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=2)
        
        # Save button
        ttk.Button(details_frame, text="Save Changes", command=self.save_server).grid(row=7, column=0, columnspan=2, pady=(20, 0))
        
        # Configure grid weights
        details_frame.columnconfigure(1, weight=1)
    
    def setup_tools_tab(self):
        """Setup the tools configuration tab"""
        tools_frame = ttk.Frame(self.notebook)
        self.notebook.add(tools_frame, text="MCP Tools")
        
        # Tool list
        list_frame = ttk.Frame(tools_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(list_frame, text="Available Tools", font=("Arial", 12, "bold")).pack(anchor=tk.W)
        
        # Tool treeview
        columns = ("Client", "Tool", "Enabled", "Max Calls/Min", "Auto Execute")
        self.tool_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.tool_tree.heading(col, text=col)
            self.tool_tree.column(col, width=120)
        
        self.tool_tree.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        self.tool_tree.bind('<<TreeviewSelect>>', self.on_tool_select)
        
        # Tool buttons
        button_frame = ttk.Frame(tools_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Button(button_frame, text="Refresh Tools", command=self.refresh_tools).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Edit Tool", command=self.edit_tool).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Test Tool", command=self.test_tool).pack(side=tk.LEFT)
    
    def setup_global_settings_tab(self):
        """Setup the global settings tab"""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="Global Settings")
        
        # Settings form
        form_frame = ttk.LabelFrame(settings_frame, text="MCP Global Settings", padding="20")
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Enable MCP
        self.mcp_enabled_var = tk.BooleanVar()
        ttk.Checkbutton(form_frame, text="Enable MCP Functionality", variable=self.mcp_enabled_var).pack(anchor=tk.W, pady=5)
        
        # Default Timeout
        timeout_frame = ttk.Frame(form_frame)
        timeout_frame.pack(fill=tk.X, pady=5)
        ttk.Label(timeout_frame, text="Default Timeout (seconds):").pack(side=tk.LEFT)
        self.default_timeout_var = tk.StringVar()
        ttk.Entry(timeout_frame, textvariable=self.default_timeout_var, width=10).pack(side=tk.LEFT, padx=(10, 0))
        
        # Max Concurrent Connections
        max_conn_frame = ttk.Frame(form_frame)
        max_conn_frame.pack(fill=tk.X, pady=5)
        ttk.Label(max_conn_frame, text="Max Concurrent Connections:").pack(side=tk.LEFT)
        self.max_connections_var = tk.StringVar()
        ttk.Entry(max_conn_frame, textvariable=self.max_connections_var, width=10).pack(side=tk.LEFT, padx=(10, 0))
        
        # Log Level
        log_level_frame = ttk.Frame(form_frame)
        log_level_frame.pack(fill=tk.X, pady=5)
        ttk.Label(log_level_frame, text="Log Level:").pack(side=tk.LEFT)
        self.log_level_var = tk.StringVar()
        log_level_combo = ttk.Combobox(log_level_frame, textvariable=self.log_level_var, 
                                      values=["DEBUG", "INFO", "WARNING", "ERROR"], state="readonly")
        log_level_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        # Auto Reconnect
        self.auto_reconnect_var = tk.BooleanVar()
        ttk.Checkbutton(form_frame, text="Auto Reconnect on Connection Loss", variable=self.auto_reconnect_var).pack(anchor=tk.W, pady=5)
        
        # Connection Retry Delay
        retry_delay_frame = ttk.Frame(form_frame)
        retry_delay_frame.pack(fill=tk.X, pady=5)
        ttk.Label(retry_delay_frame, text="Connection Retry Delay (seconds):").pack(side=tk.LEFT)
        self.retry_delay_var = tk.StringVar()
        ttk.Entry(retry_delay_frame, textvariable=self.retry_delay_var, width=10).pack(side=tk.LEFT, padx=(10, 0))
        
        # Save button
        ttk.Button(form_frame, text="Save Global Settings", command=self.save_global_settings).pack(pady=(20, 0))
    
    def setup_import_export_tab(self):
        """Setup the import/export tab"""
        import_export_frame = ttk.Frame(self.notebook)
        self.notebook.add(import_export_frame, text="Import/Export")
        
        # Import section
        import_frame = ttk.LabelFrame(import_export_frame, text="Import Configuration", padding="20")
        import_frame.pack(fill=tk.X, padx=20, pady=(20, 10))
        
        ttk.Label(import_frame, text="Import MCP configuration from a JSON file:").pack(anchor=tk.W)
        
        import_button_frame = ttk.Frame(import_frame)
        import_button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(import_button_frame, text="Browse...", command=self.import_config).pack(side=tk.LEFT, padx=(0, 10))
        self.import_path_var = tk.StringVar()
        ttk.Entry(import_button_frame, textvariable=self.import_path_var, state="readonly").pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Export section
        export_frame = ttk.LabelFrame(import_export_frame, text="Export Configuration", padding="20")
        export_frame.pack(fill=tk.X, padx=20, pady=(10, 20))
        
        ttk.Label(export_frame, text="Export current MCP configuration to a JSON file:").pack(anchor=tk.W)
        
        export_button_frame = ttk.Frame(export_frame)
        export_button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(export_button_frame, text="Browse...", command=self.export_config).pack(side=tk.LEFT, padx=(0, 10))
        self.export_path_var = tk.StringVar()
        ttk.Entry(export_button_frame, textvariable=self.export_path_var, state="readonly").pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Validation section
        validation_frame = ttk.LabelFrame(import_export_frame, text="Configuration Validation", padding="20")
        validation_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        ttk.Button(validation_frame, text="Validate Configuration", command=self.validate_config).pack(anchor=tk.W)
        
        self.validation_text = tk.Text(validation_frame, height=10, wrap=tk.WORD)
        self.validation_text.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
    
    def load_data(self):
        """Load data into the GUI"""
        self.load_servers()
        self.load_tools()
        self.load_global_settings()
    
    def load_servers(self):
        """Load servers into the listbox"""
        self.server_listbox.delete(0, tk.END)
        for server in mcp_config_manager.get_all_servers():
            status = "✓" if server.enabled else "✗"
            self.server_listbox.insert(tk.END, f"{status} {server.name}")
    
    def load_tools(self):
        """Load tools into the treeview"""
        for item in self.tool_tree.get_children():
            self.tool_tree.delete(item)
        
        for tool in mcp_config_manager.tools.values():
            self.tool_tree.insert("", tk.END, values=(
                tool.client_name,
                tool.tool_name,
                "Yes" if tool.enabled else "No",
                tool.max_calls_per_minute,
                "Yes" if tool.auto_execute else "No"
            ))
    
    def load_global_settings(self):
        """Load global settings into the form"""
        self.mcp_enabled_var.set(mcp_config_manager.get_global_setting("enable_mcp", True))
        self.default_timeout_var.set(str(mcp_config_manager.get_global_setting("default_timeout", 30)))
        self.max_connections_var.set(str(mcp_config_manager.get_global_setting("max_concurrent_connections", 5)))
        self.log_level_var.set(mcp_config_manager.get_global_setting("log_level", "INFO"))
        self.auto_reconnect_var.set(mcp_config_manager.get_global_setting("auto_reconnect", True))
        self.retry_delay_var.set(str(mcp_config_manager.get_global_setting("connection_retry_delay", 5)))
    
    def on_server_select(self, event):
        """Handle server selection"""
        selection = self.server_listbox.curselection()
        if selection:
            index = selection[0]
            server_name = self.server_listbox.get(index).split(" ", 1)[1]
            self.selected_server = server_name
            self.load_server_details(server_name)
    
    def load_server_details(self, server_name: str):
        """Load server details into the form"""
        server = mcp_config_manager.get_server(server_name)
        if server:
            self.server_name_var.set(server.name)
            self.server_url_var.set(server.url)
            self.server_desc_var.set(server.description)
            self.server_enabled_var.set(server.enabled)
            self.server_auto_connect_var.set(server.auto_connect)
            self.server_timeout_var.set(str(server.timeout))
            self.server_retry_var.set(str(server.retry_attempts))
    
    def add_server(self):
        """Add a new server"""
        self.selected_server = None
        self.server_name_var.set("")
        self.server_url_var.set("")
        self.server_desc_var.set("")
        self.server_enabled_var.set(True)
        self.server_auto_connect_var.set(False)
        self.server_timeout_var.set("30")
        self.server_retry_var.set("3")
    
    def remove_server(self):
        """Remove the selected server"""
        if self.selected_server:
            if messagebox.askyesno("Confirm", f"Are you sure you want to remove server '{self.selected_server}'?"):
                mcp_config_manager.remove_server(self.selected_server)
                self.load_servers()
                self.selected_server = None
                self.clear_server_form()
    
    def save_server(self):
        """Save server configuration"""
        try:
            server_config = MCPServerConfig(
                name=self.server_name_var.get(),
                url=self.server_url_var.get(),
                description=self.server_desc_var.get(),
                enabled=self.server_enabled_var.get(),
                auto_connect=self.server_auto_connect_var.get(),
                timeout=int(self.server_timeout_var.get()),
                retry_attempts=int(self.server_retry_var.get())
            )
            
            mcp_config_manager.add_server(server_config)
            self.load_servers()
            messagebox.showinfo("Success", "Server configuration saved successfully!")
            
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save server: {e}")
    
    def clear_server_form(self):
        """Clear the server form"""
        self.server_name_var.set("")
        self.server_url_var.set("")
        self.server_desc_var.set("")
        self.server_enabled_var.set(False)
        self.server_auto_connect_var.set(False)
        self.server_timeout_var.set("30")
        self.server_retry_var.set("3")
    
    def test_server_connection(self):
        """Test connection to the selected server"""
        if not self.selected_server:
            messagebox.showwarning("Warning", "Please select a server first.")
            return
        
        # This would need to be implemented with actual MCP client testing
        messagebox.showinfo("Info", f"Connection test for '{self.selected_server}' would be implemented here.")
    
    def on_tool_select(self, event):
        """Handle tool selection"""
        selection = self.tool_tree.selection()
        if selection:
            item = self.tool_tree.item(selection[0])
            values = item['values']
            self.selected_tool = f"{values[0]}:{values[1]}"
    
    def refresh_tools(self):
        """Refresh the tools list"""
        self.load_tools()
        messagebox.showinfo("Info", "Tools list refreshed.")
    
    def edit_tool(self):
        """Edit the selected tool"""
        if not self.selected_tool:
            messagebox.showwarning("Warning", "Please select a tool first.")
            return
        
        # This would open a tool configuration dialog
        messagebox.showinfo("Info", f"Edit tool '{self.selected_tool}' would be implemented here.")
    
    def test_tool(self):
        """Test the selected tool"""
        if not self.selected_tool:
            messagebox.showwarning("Warning", "Please select a tool first.")
            return
        
        # This would test the tool with sample parameters
        messagebox.showinfo("Info", f"Test tool '{self.selected_tool}' would be implemented here.")
    
    def save_global_settings(self):
        """Save global settings"""
        try:
            settings = {
                "enable_mcp": self.mcp_enabled_var.get(),
                "default_timeout": int(self.default_timeout_var.get()),
                "max_concurrent_connections": int(self.max_connections_var.get()),
                "log_level": self.log_level_var.get(),
                "auto_reconnect": self.auto_reconnect_var.get(),
                "connection_retry_delay": int(self.retry_delay_var.get())
            }
            
            for key, value in settings.items():
                mcp_config_manager.update_global_setting(key, value)
            
            messagebox.showinfo("Success", "Global settings saved successfully!")
            
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")
    
    def import_config(self):
        """Import configuration from file"""
        file_path = filedialog.askopenfilename(
            title="Import MCP Configuration",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            self.import_path_var.set(file_path)
            if mcp_config_manager.import_configuration(file_path):
                self.load_data()
                messagebox.showinfo("Success", "Configuration imported successfully!")
            else:
                messagebox.showerror("Error", "Failed to import configuration.")
    
    def export_config(self):
        """Export configuration to file"""
        file_path = filedialog.asksaveasfilename(
            title="Export MCP Configuration",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            self.export_path_var.set(file_path)
            if mcp_config_manager.export_configuration(file_path):
                messagebox.showinfo("Success", "Configuration exported successfully!")
            else:
                messagebox.showerror("Error", "Failed to export configuration.")
    
    def validate_config(self):
        """Validate the current configuration"""
        errors = mcp_config_manager.validate_configuration()
        
        self.validation_text.delete(1.0, tk.END)
        
        if errors:
            self.validation_text.insert(tk.END, "Configuration validation found the following errors:\n\n")
            for error in errors:
                self.validation_text.insert(tk.END, f"• {error}\n")
        else:
            self.validation_text.insert(tk.END, "Configuration is valid! No errors found.")
    
    def on_closing(self):
        """Handle window closing"""
        if self.parent:
            self.root.destroy()
        else:
            self.root.quit()
    
    def run(self):
        """Run the GUI"""
        self.root.mainloop()


if __name__ == "__main__":
    app = MCPConfigGUI()
    app.run()
