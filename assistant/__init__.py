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

try:
    from .voice_recognizer import VoiceRecognizer
except ImportError:
    VoiceRecognizer = None

# Plugin system - always available
from .plugin_base import AssistantPlugin
from .plugin_registry import PluginRegistry

__all__ = [
    'AssistantPlugin', 
    'PluginRegistry',
    'AICore',
    'SpeechHandler',
    'VoiceRecognizer'
]