import threading
import time
import numpy as np
import sounddevice as sd
import wave
import tempfile
import os

class VoiceRecognizer:
    def __init__(self):
        self.is_listening = False
        self.sample_rate = 16000
        self.duration = 5  # seconds
        self.recording = None
        
    def record_audio(self):
        """Record audio from microphone"""
        try:
            print("Recording... (speak now)")
            self.recording = sd.rec(
                int(self.duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=1,
                dtype='float32'
            )
            sd.wait()
            print("Recording finished")
            return self.recording
        except Exception as e:
            print(f"Recording error: {e}")
            return None
    
    def save_temp_wav(self, audio_data):
        """Save audio to temporary WAV file"""
        try:
            # Normalize audio
            audio_data = audio_data / np.max(np.abs(audio_data))
            
            temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            
            with wave.open(temp_file.name, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(self.sample_rate)
                wf.writeframes((audio_data * 32767).astype(np.int16).tobytes())
            
            return temp_file.name
        except Exception as e:
            print(f"Error saving audio: {e}")
            return None
    
    def listen(self):
        """Listen for voice input and convert to text"""
        try:
            # Record audio
            audio = self.record_audio()
            if audio is None:
                return None
            
            # Save to temp file
            temp_file = self.save_temp_wav(audio)
            if not temp_file:
                return None
            
            # Try using Google Speech Recognition with the audio file
            try:
                import speech_recognition as sr
                recognizer = sr.Recognizer()
                
                with sr.AudioFile(temp_file) as source:
                    audio_data = recognizer.record(source)
                    text = recognizer.recognize_google(audio_data)
                    print(f"Heard: {text}")
                    return text
            except ImportError:
                print("SpeechRecognition not installed. Install with: pip install SpeechRecognition")
                return None
            except Exception as e:
                print(f"Speech recognition error: {e}")
                return None
            finally:
                # Clean up temp file
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                    
        except Exception as e:
            print(f"Voice recognition error: {e}")
            return None
    
    def continuous_listen(self, callback, wake_word=None):
        """Continuously listen for commands"""
        self.is_listening = True
        
        def listen_loop():
            while self.is_listening:
                try:
                    text = self.listen()
                    if text:
                        if wake_word:
                            text_lower = text.lower()
                            wake_lower = wake_word.lower()
                            if wake_lower in text_lower:
                                # Remove wake word from command
                                command = text_lower.replace(wake_lower, '', 1).strip()
                                if command:  # Only process if there's something after wake word
                                    callback(command)
                        else:
                            callback(text)
                    time.sleep(0.5)  # Small delay
                except Exception as e:
                    print(f"Error in listen loop: {e}")
                    time.sleep(1)
        
        thread = threading.Thread(target=listen_loop, daemon=True)
        thread.start()
        print("Continuous listening started")
    
    def stop_listening(self):
        """Stop continuous listening"""
        self.is_listening = False