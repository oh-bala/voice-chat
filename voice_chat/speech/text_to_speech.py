import pyttsx3
import logging
import threading
import tempfile
import os
import subprocess
import time
import speech_recognition as sr
import numpy as np
from config import Config
from .elevenlabs_client import ElevenLabsClient

class TextToSpeechHandler:
    def __init__(self):
        self.engine = pyttsx3.init() if Config.TTS_PROVIDER == 'pyttsx3' else None
        self.is_speaking = False
        self.provider = Config.TTS_PROVIDER
        self.eleven = None
        self.microphone = None
        self.recognizer = None
        self._setup_vad_components()
        if self.provider == 'pyttsx3':
            self._setup_voice()
        elif self.provider == 'elevenlabs':
            try:
                self.eleven = ElevenLabsClient()
            except Exception as e:
                logging.error(f"Failed to init ElevenLabs client, falling back to pyttsx3: {e}")
                self.provider = 'pyttsx3'
                self.engine = pyttsx3.init()
                self._setup_voice()
    
    def _setup_vad_components(self):
        """Setup microphone and recognizer for VAD"""
        if not Config.VAD_ENABLED:
            print("VAD disabled in configuration")
            return
            
        try:
            self.microphone = sr.Microphone()
            self.recognizer = sr.Recognizer()
            self.recognizer.energy_threshold = Config.VAD_ENERGY_THRESHOLD
            self.recognizer.dynamic_energy_threshold = True
            print("VAD components initialized")
        except Exception as e:
            logging.error(f"Failed to setup VAD components: {e}")
            self.microphone = None
            self.recognizer = None
    
    def _calculate_audio_energy(self, audio_data):
        """Calculate audio energy level for VAD"""
        try:
            if hasattr(audio_data, 'get_array_of_samples'):
                samples = audio_data.get_array_of_samples()
                samples = np.array(samples, dtype=np.float32)
            elif hasattr(audio_data, 'get_raw_data'):
                raw_data = audio_data.get_raw_data()
                samples = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32)
            else:
                samples = np.array(audio_data, dtype=np.float32)
            if len(samples) > 0:
                rms = np.sqrt(np.mean(samples ** 2))
                return rms
            return 0
        except Exception as e:
            logging.error(f"Error calculating audio energy: {e}")
            return 200
    
    def _wait_for_silence_after_tts(self, timeout=None, silence_threshold=None):
        """Wait for silence after TTS finishes using VAD"""
        if not Config.VAD_ENABLED:
            # VAD disabled, use fallback cooldown
            time.sleep(Config.ASR_TTS_COOLDOWN)
            return
            
        if not self.microphone or not self.recognizer:
            # Fallback to fixed cooldown if VAD not available
            time.sleep(Config.ASR_TTS_COOLDOWN)
            return
        
        # Use config values if not specified
        timeout = timeout or Config.VAD_TIMEOUT
        silence_threshold = silence_threshold or Config.VAD_SILENCE_THRESHOLD
        
        print("🔇 Waiting for TTS to finish...")
        start_time = time.time()
        silence_start = None
        consecutive_silence_samples = 0
        required_silence_samples = int(silence_threshold / 0.1)  # 0.1s per sample
        
        try:
            with self.microphone as source:
                while time.time() - start_time < timeout:
                    try:
                        # Listen for a short duration to check audio level
                        audio = self.recognizer.listen(source, timeout=0.1, phrase_time_limit=0.1)
                        energy = self._calculate_audio_energy(audio)
                        
                        if energy < self.recognizer.energy_threshold:
                            # Silence detected
                            if silence_start is None:
                                silence_start = time.time()
                            consecutive_silence_samples += 1
                            
                            if consecutive_silence_samples >= required_silence_samples:
                                silence_duration = time.time() - silence_start
                                print(f"✅ TTS finished, {silence_duration:.1f}s of silence detected")
                                # Small safety buffer
                                time.sleep(0.1)
                                return
                        else:
                            # Audio detected, reset silence counter
                            silence_start = None
                            consecutive_silence_samples = 0
                            
                    except sr.WaitTimeoutError:
                        # No audio detected, count as silence
                        if silence_start is None:
                            silence_start = time.time()
                        consecutive_silence_samples += 1
                        
                        if consecutive_silence_samples >= required_silence_samples:
                            silence_duration = time.time() - silence_start
                            print(f"✅ TTS finished, {silence_duration:.1f}s of silence detected")
                            time.sleep(0.1)
                            return
                            
        except Exception as e:
            logging.error(f"VAD error: {e}")
            # Fallback to fixed cooldown
            time.sleep(Config.ASR_TTS_COOLDOWN)
        
        # Timeout reached, use fallback
        print(f"⚠️ VAD timeout, using fallback cooldown")
        time.sleep(Config.ASR_TTS_COOLDOWN)
    
    def _setup_voice(self):
        try:
            self.engine.setProperty('rate', Config.TTS_RATE)
            self.engine.setProperty('volume', Config.TTS_VOLUME)
            voices = self.engine.getProperty('voices')
            if voices:
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
                    self.engine.setProperty('voice', voices[0].id)
                    print(f"Using default voice: {voices[0].name}")
        except Exception as e:
            logging.error(f"Error setting up TTS voice: {e}")
            print("Warning: Could not configure voice settings, using defaults")
    
    def speak(self, text, blocking=False, voice_id=None):
        if not text or not text.strip():
            print("TTS: Empty text, skipping speech")
            return False
        self.stop_speaking()
        try:
            if self.provider == 'elevenlabs' and self.eleven:
                if blocking:
                    self._speak_blocking_elevenlabs(text, voice_id)
                    self._wait_for_silence_after_tts()
                else:
                    self._speak_async_elevenlabs(text, voice_id)
            else:
                if blocking:
                    self._speak_blocking(text)
                    self._wait_for_silence_after_tts()
                else:
                    self._speak_async(text)
            return True
        except Exception as e:
            logging.error(f"Error in text-to-speech: {e}")
            print(f"TTS Error: {e}")
            self.is_speaking = False
            return False
    
    def _speak_blocking(self, text):
        self.is_speaking = True
        print(f"🔊 Speaking: {text[:100]}{'...' if len(text) > 100 else ''}")
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        finally:
            self.is_speaking = False
    
    def _speak_async(self, text):
        def speak_thread():
            self.is_speaking = True
            print(f"🔊 Speaking (async): {text[:100]}{'...' if len(text) > 100 else ''}")
            try:
                self.engine.say(text)
                self.engine.runAndWait()
                self._wait_for_silence_after_tts()
            except Exception as e:
                logging.error(f"Error in async TTS: {e}")
            finally:
                self.is_speaking = False
        thread = threading.Thread(target=speak_thread, name="TTS-Thread")
        thread.daemon = True
        thread.start()

    def _play_audio_bytes(self, audio_bytes: bytes):
        """Write bytes to a temp mp3 and play using afplay (macOS)."""
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
                f.write(audio_bytes)
                temp_path = f.name
            # macOS default player
            subprocess.run(["afplay", temp_path], check=False)
        finally:
            try:
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception:
                pass

    def _speak_blocking_elevenlabs(self, text, voice_id=None):
        self.is_speaking = True
        print(f"🔊 Speaking (ElevenLabs): {text[:100]}{'...' if len(text) > 100 else ''}")
        try:
            audio = self.eleven.text_to_speech(text, voice_id=voice_id)
            if audio:
                self._play_audio_bytes(audio)
        finally:
            self.is_speaking = False

    def _speak_async_elevenlabs(self, text, voice_id=None):
        def speak_thread():
            self.is_speaking = True
            print(f"🔊 Speaking (ElevenLabs async): {text[:100]}{'...' if len(text) > 100 else ''}")
            try:
                audio = self.eleven.text_to_speech(text, voice_id=voice_id)
                if audio:
                    self._play_audio_bytes(audio)
                    self._wait_for_silence_after_tts()
            except Exception as e:
                logging.error(f"Error in async ElevenLabs TTS: {e}")
            finally:
                self.is_speaking = False
        thread = threading.Thread(target=speak_thread, name="TTS-Thread-ElevenLabs")
        thread.daemon = True
        thread.start()
    
    def stop_speaking(self):
        try:
            if self.is_speaking:
                print("🔇 Stopping current speech")
                self.engine.stop()
                import time
                time.sleep(0.1)
            self.is_speaking = False
        except Exception as e:
            logging.error(f"Error stopping speech: {e}")
            self.is_speaking = False
    
    def is_currently_speaking(self):
        return self.is_speaking
    
    def set_rate(self, rate):
        try:
            self.engine.setProperty('rate', rate)
            print(f"Speech rate set to {rate} WPM")
        except Exception as e:
            logging.error(f"Error setting speech rate: {e}")
    
    def set_volume(self, volume):
        try:
            volume = max(0.0, min(1.0, volume))
            self.engine.setProperty('volume', volume)
            print(f"Speech volume set to {volume}")
        except Exception as e:
            logging.error(f"Error setting speech volume: {e}")
    
    def get_available_voices(self):
        if self.provider == 'elevenlabs' and self.eleven:
            return self.eleven.list_voices()
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

    def set_provider(self, provider: str):
        """Switch TTS provider at runtime."""
        if provider == self.provider:
            return
        self.stop_speaking()
        if provider == 'elevenlabs':
            try:
                self.eleven = ElevenLabsClient()
                self.engine = None
                self.provider = 'elevenlabs'
            except Exception as e:
                logging.error(f"Failed to switch to ElevenLabs: {e}")
        else:
            self.engine = pyttsx3.init()
            self.eleven = None
            self.provider = 'pyttsx3'
            self._setup_voice()
