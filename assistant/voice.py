import threading

class VoiceTextOnly:
    def __init__(self):
        self.is_listening = False
    
    def speak(self, text):
        print(f"[Assistant]: {text}")
    
    def start_continuous_listen(self, callback, wake_word="jarvis"):
        self.is_listening = True
        
        print(f"\n=== VOICE MODE (Text Input) ===")
        print(f"Wake word: '{wake_word}'")
        print(f"Type commands starting with '{wake_word}'")
        print("Example: jarvis what time is it")
        print("Type 'exit' to quit voice mode")
        print("=" * 35)
        
        def input_loop():
            while self.is_listening:
                try:
                    user_input = input(f"\nSay to {wake_word}: ").strip()
                    
                    if not user_input:
                        continue
                    
                    if user_input.lower() == 'exit':
                        print("Exiting voice mode...")
                        self.is_listening = False
                        break
                    
                    text_lower = user_input.lower()
                    if wake_word in text_lower:
                        command = text_lower.replace(wake_word, '', 1).strip()
                        if command:
                            callback(command)
                    else:
                        print(f"Didn't catch that. Start with '{wake_word}'")
                        
                except KeyboardInterrupt:
                    print("\nExiting voice mode...")
                    self.is_listening = False
                    break
                except Exception as e:
                    print(f"Error: {e}")
        
        thread = threading.Thread(target=input_loop, daemon=True)
        thread.start()
    
    def stop_listening(self):
        self.is_listening = False
    
    def test_microphone(self):
        return True