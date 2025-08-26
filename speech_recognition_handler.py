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
        self._context_active = False  # Track context manager state
        
        # Adjust for ambient noise and optimize settings
        self._calibrate_microphone()
    
    def _select_best_microphone(self):
        """Select the best available microphone"""
        try:
            microphones = sr.Microphone.list_microphone_names()
            
            # Prefer built-in microphones over external ones
            preferred_names = ["MacBook", "Built-in", "Internal", "Default"]
            
            for i, name in enumerate(microphones):
                for preferred in preferred_names:
                    if preferred.lower() in name.lower():
                        print(f"Selected microphone: {name}")
                        return sr.Microphone(device_index=i)
            
            # Fallback to default microphone
            print("Using default microphone")
            return sr.Microphone()
            
        except Exception as e:
            print(f"Error selecting microphone, using default: {e}")
            return sr.Microphone()
    
    def _calibrate_microphone(self):
        """Calibrate microphone for optimal performance"""
        try:
            if not self._context_active:
                with self.microphone as source:
                    self._context_active = True
                    print("Adjusting for ambient noise... Please wait.")
                    self.recognizer.adjust_for_ambient_noise(source, duration=2)
                    
                    # Optimize recognizer settings
                    self.recognizer.energy_threshold = max(150, self.recognizer.energy_threshold * 0.8)
                    self.recognizer.dynamic_energy_threshold = True
                    self.recognizer.pause_threshold = 0.8
                    self.recognizer.non_speaking_duration = 0.5
                    
                    print(f"Energy threshold: {self.recognizer.energy_threshold}")
                    print("Ready for speech recognition!")
                    
                    self._context_active = False
                
                
        except Exception as e:
            print(f"Warning: Microphone calibration failed: {e}")
            # Use fallback settings
            self.recognizer.energy_threshold = 200
            self._context_active = False
    
    def listen_for_speech(self, timeout=None, phrase_time_limit=None):
        """
        Listen for speech input from the microphone
        
        Args:
            timeout: Maximum time to wait for speech to start
            phrase_time_limit: Maximum time to wait for phrase completion
            
        Returns:
            str: Recognized speech text or None if recognition failed
        """
        try:
            # Check if already in context and handle appropriately
            if self._context_active:
                print("⚠️  Context already active, creating new microphone instance")
                temp_mic = self._select_best_microphone()
                source_to_use = temp_mic
            else:
                source_to_use = self.microphone
            
            with source_to_use as source:
                self._context_active = True
                # Use more generous default timeouts
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
        """
        Continuously listen for the wake word
        
        Returns:
            bool: True if wake word detected, False otherwise
        """
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
        """
        Fallback method for compatibility with enhanced handler
        Just uses the regular listen_for_speech method
        
        Args:
            initial_timeout: Time to wait for speech to start
            max_silence_duration: Maximum time to wait for phrase completion
            
        Returns:
            str: Recognized speech text or None
        """
        return self.listen_for_speech(
            timeout=initial_timeout,
            phrase_time_limit=max_silence_duration or Config.SPEECH_PHRASE_TIMEOUT
        )
    
    def is_exit_command(self, text):
        """
        Check if the text contains an exit command
        
        Args:
            text (str): The text to check
            
        Returns:
            bool: True if text contains exit command
        """
        if not text:
            return False
            
        return any(exit_word in text.lower() for exit_word in Config.EXIT_WORDS)
