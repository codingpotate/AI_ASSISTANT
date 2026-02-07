# assistant/simple_speech.py
import subprocess
import tempfile
import os
import threading

class SimpleSpeech:
    def __init__(self):
        self.is_windows = os.name == 'nt'
        self.listening = False
        
    def speak(self, text):
        """Text-to-speech output"""
        if not self.is_windows:
            print(f"[Assistant]: {text}")
            return
        
        # Windows SAPI TTS (your existing code - works)
        def _speak():
            try:
                script = f'''
Dim speech
Set speech = CreateObject("SAPI.SpVoice")
speech.Speak "{text.replace('"', '')}"
'''
                with tempfile.NamedTemporaryFile(mode='w', suffix='.vbs', delete=False) as f:
                    f.write(script)
                    temp_file = f.name

                subprocess.run(['cscript', '//Nologo', temp_file], capture_output=True)
                os.unlink(temp_file)
                
            except Exception as e:
                print(f"Speech error: {e}")
                print(f"[Assistant said]: {text}")
        
        thread = threading.Thread(target=_speak)
        thread.start()
    
    def listen(self):
        """Listen for input - text mode for now"""
        return input("You: ")
    
    def start_continuous_listen(self, callback, wake_word="jarvis"):
        """Start continuous 'listening' - actually text input"""
        self.listening = True
        
        print("\n" + "="*50)
        print("VOICE MODE ACTIVATED (Text Input Simulation)")
        print("="*50)
        print(f"Type commands as if you're speaking to '{wake_word}'")
        print(f"Example: '{wake_word} what time is it'")
        print("Commands will be processed with voice-like responses")
        print("Type 'exit voice' to return to normal mode")
        print("-"*50)
        
        def input_loop():
            while self.listening:
                try:
                    user_input = input(f"\nSay something to {wake_word}: ").strip()
                    
                    if not user_input:
                        continue
                    
                    # Check for exit command
                    if user_input.lower() == 'exit voice':
                        print("Exiting voice mode...")
                        self.listening = False
                        break
                    
                    # Process the command
                    callback(user_input)
                    
                except KeyboardInterrupt:
                    print("\nExiting voice mode...")
                    self.listening = False
                    break
                except Exception as e:
                    print(f"Error: {e}")
        
        # Run in background thread
        thread = threading.Thread(target=input_loop, daemon=True)
        thread.start()
    
    def stop_listening(self):
        """Stop continuous listening"""
        self.listening = False