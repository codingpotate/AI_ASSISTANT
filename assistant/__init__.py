"""
Assistant package exports
"""

# Speech handler - use SimpleSpeech as SpeechHandler
from .simple_speech import SimpleSpeech as SpeechHandler

# Core AI functionality
from .core import AICore

# Local AI fallback
from .local_ai import LocalAI

# Skills module (create it if empty)
try:
    from .skills import Skills
except ImportError:
    # Create a basic Skills class if file is missing
    class Skills:
        def __init__(self):
            pass
        def get_time_date(self):
            from datetime import datetime
            return datetime.now().strftime("It's %I:%M %p on %A, %B %d, %Y")

# Export all
__all__ = [
    'SpeechHandler',
    'AICore',
    'LocalAI',
    'Skills'
]