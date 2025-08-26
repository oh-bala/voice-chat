import pyttsx3
import logging
import threading
from config import Config

class TextToSpeechHandler:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.is_speaking = False
        self._setup_voice()
    
    def _setup_voice(self):
        """Configure the TTS engine settings"""
        try:
            # Set speech rate
            self.engine.setProperty('rate', Config.TTS_RATE)
            
            # Set volume
            self.engine.setProperty('volume', Config.TTS_VOLUME)
            
            # Get available voices and prefer a female voice if available
            voices = self.engine.getProperty('voices')
            if voices:
                # On macOS, try to find a nice voice
                preferred_voices = ['Karen', 'Samantha', 'Victoria', 'Alex']
                selected_voice = None
                
                for preferred in preferred_voices:
                    for voice in voices:
                        if preferred.lower() in voice.name.lower():
                            selected_voice = voice
                            break
                    if selected_voice:
                        break
                
                if selected_voice:
                    self.engine.setProperty('voice', selected_voice.id)
                    print(f"Using voice: {selected_voice.name}")
                else:
                    # Use the first available voice
                    self.engine.setProperty('voice', voices[0].id)
                    print(f"Using default voice: {voices[0].name}")
            
        except Exception as e:
            logging.error(f"Error setting up TTS voice: {e}")
            print("Warning: Could not configure voice settings, using defaults")
    
    def speak(self, text, blocking=False):
        """
        Convert text to speech
        
        Args:
            text (str): Text to speak
            blocking (bool): If True, wait for speech to complete. If False, speak asynchronously.
        
        Returns:
            bool: True if speech started successfully
        """
        if not text or not text.strip():
            print("TTS: Empty text, skipping speech")
            return False
        
        # Stop any current speech before starting new one
        self.stop_speaking()
        
        try:
            if blocking:
                self._speak_blocking(text)
            else:
                self._speak_async(text)
            
            return True
            
        except Exception as e:
            logging.error(f"Error in text-to-speech: {e}")
            print(f"TTS Error: {e}")
            self.is_speaking = False
            return False
    
    def _speak_blocking(self, text):
        """Blocking speech synthesis"""
        self.is_speaking = True
        print(f"🔊 Speaking: {text[:100]}{'...' if len(text) > 100 else ''}")
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        finally:
            self.is_speaking = False
    
    def _speak_async(self, text):
        """Asynchronous speech synthesis"""
        def speak_thread():
            self.is_speaking = True
            print(f"🔊 Speaking (async): {text[:100]}{'...' if len(text) > 100 else ''}")
            try:
                self.engine.say(text)
                self.engine.runAndWait()
            except Exception as e:
                logging.error(f"Error in async TTS: {e}")
            finally:
                self.is_speaking = False
        
        thread = threading.Thread(target=speak_thread, name="TTS-Thread")
        thread.daemon = True
        thread.start()
    
    def stop_speaking(self):
        """Stop the current speech"""
        try:
            if self.is_speaking:
                print("🔇 Stopping current speech")
                self.engine.stop()
                # Give a brief moment for the engine to stop
                import time
                time.sleep(0.1)
            self.is_speaking = False
        except Exception as e:
            logging.error(f"Error stopping speech: {e}")
            self.is_speaking = False
    
    def is_currently_speaking(self):
        """Check if TTS is currently speaking"""
        return self.is_speaking
    
    def set_rate(self, rate):
        """Set the speech rate (words per minute)"""
        try:
            self.engine.setProperty('rate', rate)
            print(f"Speech rate set to {rate} WPM")
        except Exception as e:
            logging.error(f"Error setting speech rate: {e}")
    
    def set_volume(self, volume):
        """Set the speech volume (0.0 to 1.0)"""
        try:
            volume = max(0.0, min(1.0, volume))  # Clamp between 0 and 1
            self.engine.setProperty('volume', volume)
            print(f"Speech volume set to {volume}")
        except Exception as e:
            logging.error(f"Error setting speech volume: {e}")
    
    def get_available_voices(self):
        """Get list of available voices"""
        try:
            voices = self.engine.getProperty('voices')
            voice_list = []
            for voice in voices:
                voice_info = {
                    'id': voice.id,
                    'name': voice.name,
                    'age': getattr(voice, 'age', 'Unknown'),
                    'gender': getattr(voice, 'gender', 'Unknown')
                }
                voice_list.append(voice_info)
            return voice_list
        except Exception as e:
            logging.error(f"Error getting available voices: {e}")
            return []
