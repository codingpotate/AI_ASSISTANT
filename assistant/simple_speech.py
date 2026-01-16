"""
Simple text-to-speech module that doesn't require numpy or pyaudio
Uses Windows built-in SAPI for TTS
"""

import subprocess
import tempfile
import os
import threading

class SimpleSpeech:
    def __init__(self):
        self.is_windows = os.name == 'nt'
        
    def speak(self, text: str):
        """Simple text-to-speech using Windows SAPI"""
        if not self.is_windows:
            print(f"[TTS]: {text}")
            return
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
    
    def listen(self) -> str:
        """Simple input - returns empty string since we don't have microphone"""
        print("Microphone not available. Using text input only.")
        return ""