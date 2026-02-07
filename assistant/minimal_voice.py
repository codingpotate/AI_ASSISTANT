import threading
import time

class MinimalVoiceRecognizer:
    """Minimal voice recognizer that uses text input as fallback"""
    
    def __init__(self):
        self.listening = False
        self.callback = None
        self.wake_word = None
        print("Voice recognition: Using text input fallback")
    
    def listen_once(self):
        """Get voice input (text fallback)"""
        print("\n[Voice Mode] Type your command (or say it out loud and then type it):")
        try:
            text = input("You: ")
            return text.strip()
        except:
            return None
    
    def continuous_listen(self, callback, wake_word=None):
        """Start continuous listening (text fallback)"""
        self.callback = callback
        self.wake_word = wake_word
        self.listening = True
        
        def listen_loop():
            print(f"\n=== Voice Assistant Active ===")
            print(f"Wake word: '{wake_word}'")
            print(f"Type commands starting with '{wake_word}'")
            print(f"Example: '{wake_word} what time is it'")
            print(f"Type 'exit' to quit")
            print("=" * 30)
            
            while self.listening:
                try:
                    text = self.listen_once()
                    if text:
                        text_lower = text.lower()
                        
                        if text_lower == 'exit':
                            print("Exiting voice mode...")
                            self.listening = False
                            break
                        
                        if self.wake_word:
                            wake_lower = self.wake_word.lower()
                            if wake_lower in text_lower:
                                # Remove wake word
                                command = text_lower.replace(wake_lower, '', 1).strip()
                                if command:
                                    self.callback(command)
                            else:
                                print(f"Tip: Start your command with '{wake_word}'")
                        else:
                            self.callback(text)
                            
                except KeyboardInterrupt:
                    print("\nStopping voice mode...")
                    self.listening = False
                    break
                except Exception as e:
                    print(f"Error: {e}")
                    time.sleep(1)
        
        thread = threading.Thread(target=listen_loop, daemon=True)
        thread.start()
    
    def stop_listening(self):
        """Stop continuous listening"""
        self.listening = False