import json
from datetime import datetime
from typing import Dict, Any, List
from google import genai
from google.genai import types
from config.settings import Settings

class AICore:
    def __init__(self):
        self.conversation_history = []
        self.system_prompt = Settings.get_system_prompt()
        from openai import OpenAI
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        self.client = OpenAI(
            api_key=os.getenv("GEMINI_API_KEY"),
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        )
        
        self.use_gemini = True  
        
    def process_command(self, text: str) -> str:
        """Process user input and generate response"""
        
        self.conversation_history.append({"role": "user", "content": text})
        
        try:
            if self.use_gemini:
                return self._process_with_gemini(text)
            else:
                return self._fallback_response(text)
                
        except Exception as e:
            return f"I encountered an error: {str(e)}"
    
    def _process_with_gemini(self, text: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model="gemini-2.5-flash",  
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": text}
                ],
                max_tokens=150
            )
            reply = response.choices[0].message.content
            
            self.conversation_history.append({"role": "assistant", "content": reply})
            return reply
            
        except Exception as e:
            print(f"Gemini API error: {e}")
            return self._fallback_response(text)
    
    def _fallback_response(self, text: str) -> str:
        """Fallback response when Gemini is not configured"""
        from assistant.local_ai import LocalAI
        local_ai = LocalAI()
        return local_ai.process(text)
    
    def get_available_skills(self) -> List[str]:
        """Return list of available skills"""
        return [
            "voice_commands",
            "weather_check",
            "news_fetch",
            "time_date",
            "calculations",
            "web_search",
            "reminders"
        ]
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []