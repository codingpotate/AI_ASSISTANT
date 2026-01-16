import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from assistant import AICore, Skills, SpeechHandler
    print("Imported assistant modules")
except ImportError as e:
    print(f"Import error: {e}")
    print("Creating fallback classes...")
    
    class Skills:
        def get_time_date(self):
            from datetime import datetime
            return datetime.now().strftime("It's %I:%M %p on %A, %B %d, %Y")
        def get_weather(self, city=None):
            return "Weather: Add API key for real data"
        def get_news(self, category="general"):
            return "News: Add API key for real headlines"
        def get_calendar_events(self, count=5):
            return "Calendar: Integration not available"
        def add_calendar_event(self, summary, start_time=None, duration_hours=1):
            return "Calendar: Cannot add events"
    
    class AICore:
        def process_command(self, text):
            return "AI Core not available. Check imports."
    
    class SpeechHandler:
        def speak(self, text):
            print(f"[Assistant]: {text}")

class PersonalAssistant:
    def __init__(self, mode: str = "text"):
        self.mode = mode
        self.ai_core = AICore()
        self.skills = Skills()
        
        if mode == "voice":
            try:
                self.speech = SpeechHandler()
                print("Voice mode activated (text-to-speech only)")
            except Exception as e:
                print(f"Voice initialization failed: {e}")
                self.mode = "text"
        else:
            self.speech = None
        
        print("\n" + "="*50)
        print("AI Personal Assistant")
        print("="*50)
        print("You can ask naturally. Type 'help' for more, 'exit' to quit.")
        print("-"*50)
    
    def run_text_mode(self):
        while True:
            try:
                user_input = input("\nYou: ").strip()
                
                if user_input.lower() == 'exit':
                    print("Goodbye!")
                    break
                elif user_input.lower() == 'help':
                    self.show_help()
                    continue
                elif user_input.lower() == 'clear':
                    if hasattr(self.ai_core, 'clear_history'):
                        self.ai_core.clear_history()
                    print("History cleared.")
                    continue
                
                response = self._process_user_input(user_input)
                print(f"Assistant: {response}")
                
                if self.mode == "voice" and self.speech:
                    self.speech.speak(response)
                    
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {str(e)}")
    
    def _process_user_input(self, user_input):
        ai_response = self.ai_core.process_command(user_input)
        
        if ai_response.startswith('[GET_WEATHER]'):
            city = ai_response.replace('[GET_WEATHER]', '').strip()
            return self.skills.get_weather(city if city else None)
        elif ai_response.startswith('[GET_NEWS]'):
            category = ai_response.replace('[GET_NEWS]', '').strip()
            return self.skills.get_news(category if category else 'general')
        elif ai_response.startswith('[GET_TIME]'):
            return self.skills.get_time_date()
        elif ai_response.startswith('[GET_CALENDAR]'):
            parts = ai_response.replace('[GET_CALENDAR]', '').strip().split()
            count = 5
            if parts and parts[0].isdigit():
                count = int(parts[0])
            return self.skills.get_calendar_events(count)
        elif ai_response.startswith('[ADD_EVENT]'):
            event_data = ai_response.replace('[ADD_EVENT]', '').strip()
            if '|' in event_data:
                summary, time_part = event_data.split('|', 1)
                return self.skills.add_calendar_event(
                    summary.strip(), 
                    time_part.strip() if time_part.strip() else None
                )
            else:
                return self.skills.add_calendar_event(event_data.strip())
        else:
            return ai_response
    
    def show_help(self):
        print("\n" + "-"*40)
        print("Available Commands (you can ask naturally):")
        print("-"*40)
        print("• Ask about time or date")
        print("• Ask about weather in any city")
        print("• Ask for news (general, technology, sports, etc.)")
        print("• Ask about calendar events ('what's on my calendar?')")
        print("• Add calendar events ('add meeting tomorrow at 2pm')")
        print("• Ask any general question or for a calculation")
        print("• 'clear' - Clear conversation history")
        print("• 'exit' - Quit the program")
        print("-"*40)

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--voice":
        mode = "voice"
    else:
        mode = "text"
    
    assistant = PersonalAssistant(mode=mode)
    assistant.run_text_mode()

if __name__ == "__main__":
    main()