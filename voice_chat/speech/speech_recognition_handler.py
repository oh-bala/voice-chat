import speech_recognition as sr
import logging
import numpy as np
import time
import threading
from collections import deque
from config import Config

class SpeechRecognitionHandler:
    def __init__(self):
        self.microphone = self._select_best_microphone()
        self.recognizer = sr.Recognizer()
        self._context_active = False
        self._calibrate_microphone()
    
    def _select_best_microphone(self):
        try:
            microphones = sr.Microphone.list_microphone_names()
            preferred_names = ["MacBook", "Built-in", "Internal", "Default"]
            for i, name in enumerate(microphones):
                for preferred in preferred_names:
                    if preferred.lower() in name.lower():
                        print(f"Selected microphone: {name}")
                        return sr.Microphone(device_index=i)
            print("Using default microphone")
            return sr.Microphone()
        except Exception as e:
            print(f"Error selecting microphone, using default: {e}")
            return sr.Microphone()
    
    def _calibrate_microphone(self):
        try:
            if not self._context_active:
                with self.microphone as source:
                    self._context_active = True
                    print("Adjusting for ambient noise... Please wait.")
                    self.recognizer.adjust_for_ambient_noise(source, duration=2)
                    self.recognizer.energy_threshold = max(150, self.recognizer.energy_threshold * 0.8)
                    self.recognizer.dynamic_energy_threshold = True
                    self.recognizer.pause_threshold = 0.8
                    self.recognizer.non_speaking_duration = 0.5
                    print(f"Energy threshold: {self.recognizer.energy_threshold}")
                    print("Ready for speech recognition!")
                    self._context_active = False
        except Exception as e:
            print(f"Warning: Microphone calibration failed: {e}")
            self.recognizer.energy_threshold = 200
            self._context_active = False
    
    def _calculate_audio_energy(self, audio_data):
        """Calculate the RMS energy of audio data"""
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
            return 200  # Default energy threshold
    
    def listen_for_speech(self, timeout=None, phrase_time_limit=None):
        try:
            if self._context_active:
                print("⚠️  Context already active, creating new microphone instance")
                temp_mic = self._select_best_microphone()
                source_to_use = temp_mic
            else:
                source_to_use = self.microphone
            with source_to_use as source:
                self._context_active = True
                effective_timeout = timeout or 10
                effective_phrase_limit = phrase_time_limit or 8
                print(f"🎤 Listening for up to {effective_timeout}s...")
                audio = self.recognizer.listen(
                    source,
                    timeout=effective_timeout,
                    phrase_time_limit=effective_phrase_limit
                )
            print("🤖 Processing speech...")
            text = self.recognizer.recognize_google(audio, language='en-US')
            if text.strip():
                print(f"✅ You said: '{text}'")
                return text.lower()
            else:
                print("❌ Empty recognition result")
                return None
        except sr.WaitTimeoutError:
            print("⏱️  No speech detected - try speaking closer to the microphone")
            return None
        except sr.UnknownValueError:
            print("❌ Could not understand the speech - try speaking more clearly")
            return None
        except sr.RequestError as e:
            logging.error(f"Could not request results from speech recognition service: {e}")
            print(f"❌ Speech recognition service error: {e}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error in speech recognition: {e}")
            print(f"❌ Unexpected error: {e}")
            return None
        finally:
            self._context_active = False
    
    def listen_for_wake_word(self):
        while True:
            try:
                print(f"Say '{Config.WAKE_WORD}' to start...")
                text = self.listen_for_speech(timeout=None, phrase_time_limit=5)
                if text and Config.WAKE_WORD.lower() in text:
                    print("Wake word detected!")
                    return True
            except KeyboardInterrupt:
                print("\nStopping wake word detection...")
                return False
    
    def listen_with_pause_detection(self, initial_timeout=5, max_silence_duration=None):
        return self.listen_for_speech(
            timeout=initial_timeout,
            phrase_time_limit=max_silence_duration or Config.SPEECH_PHRASE_TIMEOUT
        )
    
    def is_exit_command(self, text):
        if not text:
            return False
        return any(exit_word in text.lower() for exit_word in Config.EXIT_WORDS)
