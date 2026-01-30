"""
Plugin registry for dynamic discovery and management of assistant plugins.
"""
import importlib
import inspect
import os
from typing import Dict, Any, List, Type

# Use absolute import instead of relative
try:
    # When running as part of the assistant package
    from assistant.plugin_base import AssistantPlugin
except ImportError:
    # Fallback for standalone testing
    from plugin_base import AssistantPlugin

class PluginRegistry:
    def __init__(self, database=None):
        self._plugins: Dict[str, AssistantPlugin] = {}
        self._initialized = False
        self.database = database
    
    def register(self, plugin: AssistantPlugin) -> None:
        plugin_name = plugin.get_name()
        if plugin_name in self._plugins:
            raise ValueError(f"Plugin '{plugin_name}' is already registered")
        self._plugins[plugin_name] = plugin
    
    def register_module(self, module_name: str) -> None:
        try:
            module = importlib.import_module(module_name)
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, AssistantPlugin) and 
                    obj != AssistantPlugin):
                    plugin_instance = obj()
                    self.register(plugin_instance)
        except ImportError as e:
            print(f"Failed to import plugin module {module_name}: {e}")
    
    def auto_discover(self, plugins_dir: str = "assistant/plugins") -> None:
        if self._initialized:
            return
        
        if not os.path.exists(plugins_dir):
            os.makedirs(plugins_dir, exist_ok=True)
        
        for filename in os.listdir(plugins_dir):
            if filename.endswith(".py") and filename != "__init__.py":
                module_name = f"assistant.plugins.{filename[:-3]}"
                self.register_module(module_name)
        
        self._initialized = True
    
    def get_plugin(self, name: str):
        return self._plugins.get(name)
    
    def get_all_plugins(self):
        return list(self._plugins.values())
    
    def get_all_metadata(self):
        return [plugin.get_metadata() for plugin in self._plugins.values()]
    
    def execute_plugin(self, name: str, **kwargs) -> str:
        plugin = self.get_plugin(name)
        if not plugin:
            return f"Plugin '{name}' not found"
        try:
            result = plugin.execute(**kwargs)
            
            # Log plugin execution to database if available
            if self.database:
                self.database.update_plugin_stats(name, "global_session")
            
            return result
        except Exception as e:
            return f"Error executing plugin '{name}': {str(e)}"