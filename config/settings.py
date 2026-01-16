import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "your_gemini_api_key_here")
    NEWS_API_KEY = os.getenv("NEWS_API_KEY", "your_news_api_key_here")
    WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "your_weather_api_key_here")
    WOLFRAM_APP_ID = os.getenv("WOLFRAM_APP_ID", "your_wolfram_app_id")

    ASSISTANT_NAME = "Jarvis"
    WAKE_WORD = "jarvis"
    DEFAULT_CITY = "London"
    DEFAULT_NEWS_CATEGORY = "technology"
    GEMINI_MODEL = "gemini-pro"
    SYSTEM_PROMPT = """You are Jarvis, a helpful AI assistant with access to tools.

TOOLS:
- CALENDAR VIEW: To see upcoming events, respond with: [GET_CALENDAR]
- CALENDAR ADD: To add an event, respond with: [ADD_EVENT] Event Title | Start Time (ISO format optional)
- WEATHER: For weather, use: [GET_WEATHER] <city>
- NEWS: For news, use: [GET_NEWS] <category>
- TIME: For time/date, use: [GET_TIME]

INSTRUCTIONS:
1. Use EXACTLY the tool formats above.
2. For "Add event", format as: [ADD_EVENT] Meeting with Team | 2024-01-20T14:00:00
3. If user doesn't specify time for an event, you can omit it (skills will use default).
4. For general conversation, answer normally.
"""
    
    @classmethod
    def get_system_prompt(cls):
        from datetime import datetime
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user_location = cls.DEFAULT_CITY
        return cls.SYSTEM_PROMPT.format(
            current_time=current_time,
            user_location=user_location
        )
    
    @classmethod
    def is_gemini_configured(cls):
        """Check if Gemini API key is properly configured"""
        return cls.GEMINI_API_KEY and cls.GEMINI_API_KEY != "your_gemini_api_key_here"