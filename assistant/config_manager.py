import os
import json
from typing import Any, Dict
from pathlib import Path

class ConfigManager:
    def __init__(self, config_path="config.json"):
        self.config_path = Path(config_path)
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                return json.load(f)
        return {
            "assistant": {
                "name": "Jarvis",
                "personality": "helpful, concise, professional",
                "default_city": "London",
                "timezone": "UTC"
            },
            "plugins": {
                "enabled": ["weather", "news", "calendar", "time"],
                "auto_discover": True
            },
            "ai": {
                "model": "gemini-1.5-flash",
                "temperature": 0.7,
                "max_tokens": 500
            }
        }
    
    def save_config(self):
        with open(self.config_path, 'w') as f:
            json.dump(self._config, f, indent=2)
    
    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def set(self, key: str, value: Any):
        keys = key.split('.')
        config = self._config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self.save_config()