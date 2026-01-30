"""
Base plugin interface for all assistant tools/plugins.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

class AssistantPlugin(ABC):
    @abstractmethod
    def get_name(self) -> str:
        """Return the plugin's unique name."""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Return a description of what this plugin does."""
        pass
    
    @abstractmethod
    def get_parameters(self) -> Dict[str, Any]:
        """
        Return parameter schema for AI function calling.
        Format: {"type": "object", "properties": {...}, "required": [...]}
        """
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> str:
        """Execute the plugin's functionality with given parameters."""
        pass
    
    def get_metadata(self) -> Dict[str, Any]:
        """Return complete metadata including name, description, parameters."""
        return {
            "name": self.get_name(),
            "description": self.get_description(),
            "parameters": self.get_parameters()
        }