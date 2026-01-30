import sys
import os
import json
from datetime import datetime
import hashlib

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from assistant import AICore, SpeechHandler
    from assistant.database import Database
    print("Imported assistant modules")
    print("Database module available")
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
    
    class Database:
        def __init__(self, db_path="assistant.db"):
            print("Warning: Using fallback database (no persistence)")
        
        def save_conversation(self, *args, **kwargs):
            pass
        
        def get_conversation_history(self, *args, **kwargs):
            return []
        
        def update_plugin_stats(self, *args, **kwargs):
            pass
        
        def get_plugin_stats(self):
            return {"plugins": [], "total_plugins": 0, "total_executions": 0}
        
        def get_recent_sessions(self, limit=5):
            return []

def get_user_identifier():
    """Get or create a persistent user identifier."""
    config_file = "user_config.json"
    
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            user_id = config.get("user_id", "default_user")
            print(f"Loaded user ID: {user_id[:8]}...")
            return user_id
        except:
            pass
    
    import getpass
    import socket
    username = getpass.getuser()
    hostname = socket.gethostname()
    combined = f"{username}@{hostname}"
    user_id = f"user_{hashlib.md5(combined.encode()).hexdigest()[:12]}"
    
    config = {
        "user_id": user_id,
        "username": username,
        "hostname": hostname,
        "created": datetime.now().isoformat()
    }
    
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"Created new user ID: {user_id}")
    return user_id

class PersonalAssistant:
    def __init__(self, mode: str = "text"):
        self.mode = mode
        
        user_identifier = get_user_identifier()
        
        self.database = Database()
        
        from assistant.plugin_registry import PluginRegistry
        self.plugin_registry = PluginRegistry(database=self.database)
        self.plugin_registry.auto_discover()
        
        from assistant import AICore
        self.ai_core = AICore(plugin_registry=self.plugin_registry, user_identifier=user_identifier)
        
        if mode == "voice":
            try:
                from assistant import SpeechHandler
                self.speech = SpeechHandler()
                print("Voice mode activated (text-to-speech only)")
            except Exception as e:
                print(f"Voice initialization failed: {e}")
                self.mode = "text"
        else:
            self.speech = None
        
        print("\n" + "="*50)
        print(f"AI Personal Assistant | Session: {self.ai_core.session_id[:12]}...")
        print("="*50)
        print("Type 'help' for commands, 'exit' to quit")
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
                    print("History cleared from memory.")
                    continue
                elif user_input.lower() == 'stats':
                    self.show_stats()
                    continue
                elif user_input.lower() == 'sessions':
                    self.show_recent_sessions()
                    continue
                elif user_input.lower() == 'plugins':
                    self.show_plugins()
                    continue
                
                response = self.ai_core.process_command(user_input)
                print(f"Assistant: {response}")
                
                if self.mode == "voice" and self.speech:
                    self.speech.speak(response)
                    
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {str(e)}")
    
    def show_stats(self):
        if not self.database:
            print("Database not available")
            return
        
        stats = self.database.get_plugin_stats()
        print("\n" + "="*50)
        print("Plugin Statistics")
        print("="*50)
        print(f"Total plugins: {stats['total_plugins']}")
        print(f"Total executions: {stats['total_executions']}")
        
        if stats['plugins']:
            print("\nPlugin usage:")
            for plugin in stats['plugins']:
                print(f"  {plugin['plugin_name']}: {plugin['total_executions']} executions")
        print("="*50)
    
    def show_recent_sessions(self):
        if not self.database:
            print("Database not available")
            return
        
        sessions = self.database.get_recent_sessions(5)
        print("\n" + "="*50)
        print("Recent Sessions")
        print("="*50)
        
        if not sessions:
            print("No sessions found")
        else:
            current_session = self.ai_core.session_id
            for i, session in enumerate(sessions, 1):
                session_id = session['session_id']
                is_current = " (current)" if session_id == current_session else ""
                print(f"{i}. Session: {session_id[:12]}...{is_current}")
                print(f"   Messages: {session['message_count']}")
                print(f"   Last active: {session['last_activity']}")
                print()
        print("="*50)
    
    def show_plugins(self):
        plugins = self.plugin_registry.get_all_plugins()
        print("\n" + "="*50)
        print("Available Plugins")
        print("="*50)
        
        if not plugins:
            print("No plugins loaded")
        else:
            for plugin in plugins:
                print(f"{plugin.get_name()}: {plugin.get_description()}")
                params = plugin.get_parameters()
                if params and 'properties' in params:
                    print(f"  Parameters: {list(params['properties'].keys())}")
                print()
        print("="*50)
    
    def show_help(self):
        print("\n" + "-"*40)
        print("Available Commands:")
        print("-"*40)
        print("General:")
        print("• Ask questions naturally")
        print("• Ask about weather in any city")
        print("• Ask for news (general, technology, sports, etc.)")
        print("• Ask about calendar events")
        print("• Add calendar events")
        print("• Ask for calculations")
        print()
        print("System Commands:")
        print("• help - Show this help")
        print("• clear - Clear conversation history")
        print("• stats - Show plugin statistics")
        print("• sessions - List recent sessions")
        print("• plugins - List available plugins")
        print("• exit - Quit the program")
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