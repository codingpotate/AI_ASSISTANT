"""
Assistant package exports with lazy imports to avoid circular dependencies.
"""

# Core components that can be imported safely
try:
    from .core import AICore
except ImportError:
    AICore = None

try:
    from .simple_speech import SimpleSpeech as SpeechHandler
except ImportError:
    SpeechHandler = None

# Plugin system - always available
from .plugin_base import AssistantPlugin
from .plugin_registry import PluginRegistry

# Lazy import for Skills class
def get_skills_class():
    try:
        from .skills import Skills
        return Skills
    except ImportError:
        return None

__all__ = [
    'AssistantPlugin', 
    'PluginRegistry',
    'AICore',
    'SpeechHandler',
    'get_skills_class'
]