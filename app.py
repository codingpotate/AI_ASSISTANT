import sys
import os
import json
from datetime import datetime
import hashlib
try:
    from assistant.voice_text_only import VoiceTextOnly as SpeechHandler
    print("Using text-only voice mode for Python 3.14")
except ImportError as e:
    print(f"Voice import error: {e}")
    
    class FallbackVoice:
        def __init__(self):
            self.listening = False
        
        def speak(self, text):
            print(f"[Assistant]: {text}")
        
        def start_continuous_listen(self, callback, wake_word="jarvis"):
            self.listening = True
            print(f"\nVoice mode: Type commands with '{wake_word}' prefix")
            
            def simple_loop():
                while self.listening:
                    try:
                        cmd = input(f"{wake_word}> ").strip()
                        if cmd.lower() == 'exit':
                            self.listening = False
                            break
                        callback(cmd)
                    except:
                        break
            
            import threading
            thread = threading.Thread(target=simple_loop, daemon=True)
            thread.start()
        
        def stop_listening(self):
            self.listening = False
        
        def test_microphone(self):
            return True
    
    SpeechHandler = FallbackVoice
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
    def __init__(self, mode: str = "text", reminder_callback=None):
        self.mode = mode
        self.reminder_callback = reminder_callback
        user_identifier = get_user_identifier()
        session_id = hashlib.md5(user_identifier.encode()).hexdigest()[:16]
        
        self.database = Database()
        
        from assistant.plugin_registry import PluginRegistry
        self.plugin_registry = PluginRegistry(database=self.database)
        self.plugin_registry.auto_discover()
        
        from assistant.skills import Skills
        self.skills = Skills(database=self.database, session_id=session_id)
        
        from assistant import AICore
        self.ai_core = AICore(
            plugin_registry=self.plugin_registry, 
            user_identifier=user_identifier,
            skills=self.skills,
            session_id=session_id
        )
        
        self._register_skill_plugins()
        
        if mode == "voice":
            try:
                from assistant import SpeechHandler
                self.speech = SpeechHandler()
                print("Voice mode activated")
            except Exception as e:
                print(f"Voice initialization failed: {e}")
                self.mode = "text"
        else:
            self.speech = None
        
        self.start_reminder_checker()
        
        print("\n" + "="*50)
        print(f"AI Personal Assistant | Session: {session_id[:12]}...")
        print("="*50)
        print("Type 'help' for commands, 'exit' to quit")
        print("-"*50)
    
    def start_reminder_checker(self):
        if not hasattr(self, 'skills') or not self.skills:
            return
        
        import threading
        import time
        
        def check_loop():
            while True:
                try:
                    if self.skills and self.skills.database:
                        session_id = getattr(self.skills, 'session_id', 'default_session')
                        overdue = self.skills.database.get_due_reminders(session_id)
                        
                        if overdue:
                            for reminder in overdue:
                                reminder_text = reminder.get('reminder_text', 'Unknown reminder')
                                
                                if self.reminder_callback:
                                    self.reminder_callback(reminder_text)
                                elif self.mode == "voice" and self.speech:
                                    self.speech.speak(f"Reminder: {reminder_text}")
                                elif self.mode == "text":
                                    print(f"\nREMINDER: {reminder_text}\n")
                                
                                if 'id' in reminder:
                                    self.skills.database.mark_reminder_completed(reminder['id'])
                except Exception as e:
                    print(f"Reminder checker error: {e}")
                
                time.sleep(5)
        
        thread = threading.Thread(target=check_loop, daemon=True)
        thread.start()
        print("Background reminder checker started")
    
    def _register_skill_plugins(self):
        try:
            from assistant.plugins.reminder_plugin import ReminderPlugin, CheckRemindersPlugin
            from assistant.plugins.time_plugin import TimePlugin
            
            reminder_plugin = ReminderPlugin()
            check_plugin = CheckRemindersPlugin()
            time_plugin = TimePlugin()
            
            self.plugin_registry.register(reminder_plugin)
            self.plugin_registry.register(check_plugin)
            self.plugin_registry.register(time_plugin)
            
            print(f"Registered skill-based plugins")
        except ImportError as e:
            print(f"Could not register skill plugins: {e}")
    
    def run_text_mode(self):
        if self.mode == "voice" and self.speech:
            print("Starting voice assistant in simulation mode...")
            print("You can type commands as if speaking to the assistant")
            print("The assistant will respond with voice output")
            print("-" * 50)
            
            self.speech.start_continuous_listen(
                callback=self.handle_voice_command,
                wake_word="jarvis"
            )
            
            try:
                while self.speech.listening:
                    import time
                    time.sleep(0.1)
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                if self.speech:
                    self.speech.stop_listening()
        else:
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

    def handle_voice_command(self, command):
        print(f"\nProcessing: {command}")
        
        if command.lower().startswith("jarvis"):
            command = command[6:].strip()
        
        response = self.ai_core.process_command(command)
        print(f"Assistant: {response}")
        
        if self.speech:
            self.speech.speak(response)
    
    def show_stats(self, return_text=False):
        if not self.database:
            if return_text:
                return "Database not available"
            else:
                print("Database not available")
                return
        
        stats = self.database.get_plugin_stats()
        stats_text = f"""
Plugin Statistics:
-----------------
Total plugins: {stats['total_plugins']}
Total executions: {stats['total_executions']}

Plugin usage:
"""
        if stats['plugins']:
            for plugin in stats['plugins']:
                stats_text += f"  {plugin['plugin_name']}: {plugin['total_executions']} executions\n"
        
        if return_text:
            return stats_text
        else:
            print(stats_text)
            return None
    
    def show_recent_sessions(self, return_text=False):
        if not self.database:
            if return_text:
                return "Database not available"
            else:
                print("Database not available")
                return
        
        sessions = self.database.get_recent_sessions(5)
        sessions_text = "Recent Sessions:\n----------------\n"
        
        if not sessions:
            sessions_text += "No sessions found\n"
        else:
            current_session = self.ai_core.session_id
            for i, session in enumerate(sessions, 1):
                session_id = session['session_id']
                is_current = " (current)" if session_id == current_session else ""
                sessions_text += f"{i}. Session: {session_id[:12]}...{is_current}\n"
                sessions_text += f"   Messages: {session['message_count']}\n"
                sessions_text += f"   Last active: {session['last_activity']}\n\n"
        
        if return_text:
            return sessions_text
        else:
            print(sessions_text)
            return None
    
    def show_plugins(self, return_text=False):
        plugins = self.plugin_registry.get_all_plugins()
        plugins_text = "Available Plugins:\n-----------------\n"
        
        if not plugins:
            plugins_text += "No plugins loaded\n"
        else:
            for plugin in plugins:
                plugins_text += f"{plugin.get_name()}: {plugin.get_description()}\n"
                params = plugin.get_parameters()
                if params and 'properties' in params:
                    plugins_text += f"  Parameters: {list(params['properties'].keys())}\n"
                plugins_text += "\n"
        
        if return_text:
            return plugins_text
        else:
            print(plugins_text)
            return None
    
    def show_help(self, return_text=False):
        help_text = """
Available Commands:
------------------
General:
• Ask questions naturally
• Ask about weather in any city
• Ask for news (general, technology, sports, etc.)
• Ask about calendar events
• Add calendar events
• Ask for calculations

System Commands:
• help - Show this help
• clear - Clear conversation history
• stats - Show plugin statistics
• sessions - List recent sessions
• plugins - List available plugins
• exit - Quit the program
"""
        if return_text:
            return help_text
        else:
            print(help_text)
            return None

def main():
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--gui":
            try:
                from gui.tkinter_gui import AssistantGUI
            except ImportError as e:
                print(f"GUI Import Error: {e}")
                print("Make sure the 'gui' folder exists with tkinter_gui.py")
                print("Falling back to text mode...")
                mode = "text"
            else:
                assistant = PersonalAssistant(mode="text", reminder_callback=None)
                print("Launching GUI...")
                gui = AssistantGUI(assistant)
                gui.run()
                return
        elif sys.argv[1] == "--voice":
            mode = "voice"
        elif sys.argv[1] == "--text":
            mode = "text"
        elif sys.argv[1] == "--help":
            print("Usage:")
            print("  python app.py              # Text mode")
            print("  python app.py --text      # Text mode")
            print("  python app.py --voice     # Voice mode")
            print("  python app.py --gui       # GUI mode")
            print("  python app.py --help      # Show this help")
            sys.exit(0)
        else:
            print(f"Unknown argument: {sys.argv[1]}")
            print("Using text mode")
            mode = "text"
    else:
        mode = "text"
    
    assistant = PersonalAssistant(mode=mode, reminder_callback=None)
    assistant.run_text_mode()

if __name__ == "__main__":
    main()