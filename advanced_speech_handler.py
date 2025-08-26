import speech_recognition as sr
import logging
import numpy as np
import time
import threading
import queue
from collections import deque
from config import Config

class AdvancedSpeechHandler:
    def __init__(self):
        # Select the best microphone (prefer built-in over others)
        self.microphone = self._select_best_microphone()
        self.recognizer = sr.Recognizer()
        self._context_active = False  # Track context manager state
        
        # Voice Activity Detection parameters - start with lower threshold
        self.energy_threshold = 150  # Lower initial threshold
        self.dynamic_energy_threshold = True
        self.dynamic_energy_adjustment_damping = 0.15
        self.dynamic_energy_ratio = 1.5
        
        # Pause detection parameters
        self.pause_threshold = 1.0  # Slightly longer pause to ensure natural speech
        self.max_pause_threshold = 3.0  # Longer max pause
        self.min_speech_duration = 0.5  # Slightly longer minimum speech duration
        
        # Audio buffer for real-time processing
        self.audio_buffer = deque(maxlen=50)  # Store last 50 audio chunks
        self.is_listening = False
        self.speech_started = False
        
        # Initialize and calibrate
        self._calibrate_microphone()
        
    def _select_best_microphone(self):
        """Select the best available microphone"""
        try:
            microphones = sr.Microphone.list_microphone_names()
            print(f"Available microphones: {len(microphones)}")
            
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
        """Calibrate microphone and set optimal thresholds"""
        print("Calibrating microphone for optimal speech detection...")
        
        try:
            # Ensure we're not already in a context
            if not self._context_active:
                with self.microphone as source:
                    self._context_active = True
                    print("Adjusting for ambient noise (please be quiet for 2 seconds)...")
                    # Adjust for ambient noise with longer duration
                    self.recognizer.adjust_for_ambient_noise(source, duration=2)
                    
                    # Use a more conservative energy threshold
                    base_threshold = self.recognizer.energy_threshold
                    self.energy_threshold = max(150, base_threshold * 0.8)  # Lower threshold for better sensitivity
                    self.recognizer.energy_threshold = self.energy_threshold
                    
                    print(f"Energy threshold set to: {self.energy_threshold}")
                    
                    # Fine-tune recognition settings for better performance
                    self.recognizer.dynamic_energy_threshold = self.dynamic_energy_threshold
                    self.recognizer.dynamic_energy_adjustment_damping = self.dynamic_energy_adjustment_damping
                    self.recognizer.dynamic_energy_ratio = self.dynamic_energy_ratio
                    
                    # Set more permissive timeout settings
                    self.recognizer.pause_threshold = 0.8  # How long to wait before considering phrase complete
                    self.recognizer.non_speaking_duration = 0.5  # How much silence before giving up
                    
                    self._context_active = False
                
                
        except Exception as e:
            print(f"Warning: Microphone calibration failed: {e}")
            # Use fallback settings
            self.energy_threshold = 200
            self.recognizer.energy_threshold = self.energy_threshold
            self._context_active = False
            
        print("✅ Microphone calibrated and ready!")
    
    def _calculate_audio_energy(self, audio_data):
        """Calculate RMS energy of audio data"""
        try:
            # Handle different audio data types
            if hasattr(audio_data, 'get_array_of_samples'):
                samples = audio_data.get_array_of_samples()
                # Convert to numpy array
                samples = np.array(samples, dtype=np.float32)
            elif hasattr(audio_data, 'get_raw_data'):
                # Get raw audio data and convert to samples
                raw_data = audio_data.get_raw_data()
                # Convert raw bytes to numpy array (assuming 16-bit samples)
                samples = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32)
            else:
                # Fallback: try to convert directly
                samples = np.array(audio_data, dtype=np.float32)
            
            # Calculate RMS energy
            if len(samples) > 0:
                rms = np.sqrt(np.mean(samples ** 2))
                return rms
            return 0
            
        except Exception as e:
            logging.error(f"Error calculating audio energy: {e}")
            # Return a default energy value to keep the system working
            return self.energy_threshold * 0.5  # Return half the threshold as default
    
    def listen_with_pause_detection(self, initial_timeout=5, max_silence_duration=None):
        """
        Advanced listening with natural pause detection
        
        Args:
            initial_timeout: Time to wait for speech to start
            max_silence_duration: Maximum silence before stopping (uses config if None)
            
        Returns:
            str: Recognized speech text or None
        """
        if max_silence_duration is None:
            max_silence_duration = self.max_pause_threshold
            
        print("🎤 Listening for speech (speak naturally, I'll detect when you're done)...")
        
        try:
            # Use simple detection first as it's more reliable
            result = self._listen_with_simple_pause_detection(initial_timeout, max_silence_duration)
            if result:
                return result
            
            # If simple detection returns None, try chunked approach as fallback
            print("🔄 Trying advanced chunked detection...")
            return self._listen_with_chunked_detection(initial_timeout, max_silence_duration)
            
        except Exception as e:
            logging.error(f"Advanced detection failed: {e}")
            return None
    
    def _listen_with_chunked_detection(self, initial_timeout, max_silence_duration):
        """Advanced chunked pause detection"""
        audio_chunks = []
        speech_detected = False
        silence_start = None
        last_speech_time = time.time()
        
        # Check if already in context and handle appropriately
        if self._context_active:
            print("⚠️  Context already active, creating new microphone instance for chunked detection")
            temp_mic = self._select_best_microphone()
            source_to_use = temp_mic
        else:
            source_to_use = self.microphone
        
        try:
            with source_to_use as source:
                self._context_active = True
                # Wait for initial speech with timeout
                start_time = time.time()
            
                while True:
                    try:
                        # Listen for short chunks to enable real-time processing
                        audio_chunk = self.recognizer.listen(
                            source, 
                            timeout=0.5,  # Longer timeout for better chunk capture
                            phrase_time_limit=1.0  # Longer chunks for better quality
                        )
                        
                        # Calculate energy level of this chunk
                        energy = self._calculate_audio_energy(audio_chunk)
                        current_time = time.time()
                        
                        # Check if this chunk contains speech
                        if energy > self.energy_threshold:
                            # Speech detected
                            audio_chunks.append(audio_chunk)
                            
                            if not speech_detected:
                                speech_detected = True
                                print("🗣️  Speech detected, continue speaking...")
                                
                            last_speech_time = current_time
                            silence_start = None
                            
                        else:
                            # Silence detected
                            if speech_detected:
                                if silence_start is None:
                                    silence_start = current_time
                                    
                                # Check if we've had enough silence to stop
                                silence_duration = current_time - silence_start
                                
                                if silence_duration >= self.pause_threshold:
                                    # Natural pause detected
                                    speech_duration = last_speech_time - start_time
                                    
                                    if speech_duration >= self.min_speech_duration:
                                        print("✅ Natural pause detected, processing speech...")
                                        break
                                    else:
                                        # Speech was too short, keep listening
                                        speech_detected = False
                                        audio_chunks = []
                                        silence_start = None
                                        
                                elif silence_duration >= max_silence_duration:
                                    print("⏱️  Maximum silence reached, processing speech...")
                                    break
                            else:
                                # No speech detected yet, check timeout
                                if current_time - start_time > initial_timeout:
                                    print("⏱️  No speech detected within timeout period")
                                    return None
                                    
                    except sr.WaitTimeoutError:
                        # Timeout on this chunk, continue listening
                        current_time = time.time()
                        
                        if speech_detected and silence_start:
                            silence_duration = current_time - silence_start
                            if silence_duration >= self.pause_threshold:
                                speech_duration = last_speech_time - start_time
                                if speech_duration >= self.min_speech_duration:
                                    print("✅ Natural pause detected (timeout), processing speech...")
                                    break
                        elif not speech_detected and current_time - start_time > initial_timeout:
                            print("⏱️  No speech detected within timeout period")
                            return None
                        
                        continue
            
            # Combine all audio chunks
            if not audio_chunks:
                return None
                
            print("🔄 Processing combined speech...")
            
            # Combine audio chunks into single audio object
            combined_audio = self._combine_audio_chunks(audio_chunks)
            
            if combined_audio:
                # Recognize the combined audio
                text = self.recognizer.recognize_google(combined_audio)
                print(f"✅ You said: {text}")
                return text.lower()
            else:
                print("❌ Failed to combine audio chunks")
                return None
        
        except Exception as e:
            logging.error(f"Error in chunked detection: {e}")
            return None
        finally:
            self._context_active = False
    
    def _listen_with_simple_pause_detection(self, initial_timeout, max_silence_duration):
        """Simpler pause detection fallback method"""
        print("🎤 Listening with smart pause detection...")
        
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
                # Use more generous timeouts for natural speech
                timeout = initial_timeout if initial_timeout else 10
                phrase_limit = max_silence_duration if max_silence_duration else 8
                
                print(f"⏰ Listening for up to {timeout}s, phrase limit {phrase_limit}s")
                
                # Listen with optimized settings
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_limit
                )
                
                print("🤖 Processing speech...")
                
                # Try to recognize the speech with error handling
                try:
                    text = self.recognizer.recognize_google(audio, language='en-US')
                    if text.strip():  # Make sure we got actual text
                        print(f"✅ You said: '{text}'")
                        return text.lower()
                    else:
                        print("❌ Empty recognition result")
                        return None
                        
                except sr.UnknownValueError:
                    print("❌ Could not understand the speech - try speaking more clearly")
                    return None
                except sr.RequestError as e:
                    print(f"❌ Speech recognition service error: {e}")
                    return None
                
        except sr.WaitTimeoutError:
            print("⏱️  No speech detected - try speaking closer to the microphone")
            return None
        except Exception as e:
            logging.error(f"Error in simple pause detection: {e}")
            print(f"❌ Unexpected error: {e}")
            return None
        finally:
            self._context_active = False
    
    def _combine_audio_chunks(self, audio_chunks):
        """Combine multiple AudioData objects into one"""
        try:
            if not audio_chunks:
                return None
                
            if len(audio_chunks) == 1:
                return audio_chunks[0]
            
            # Get the sample rate and width from the first chunk
            sample_rate = audio_chunks[0].sample_rate
            sample_width = audio_chunks[0].sample_width
            
            # Combine all audio data
            combined_data = b""
            for chunk in audio_chunks:
                if hasattr(chunk, 'get_raw_data'):
                    combined_data += chunk.get_raw_data()
                else:
                    combined_data += chunk.frame_data
            
            # Create new AudioData object
            combined_audio = sr.AudioData(combined_data, sample_rate, sample_width)
            return combined_audio
            
        except Exception as e:
            logging.error(f"Error combining audio chunks: {e}")
            return None
    
    def listen_for_wake_word_advanced(self):
        """
        Advanced wake word detection with better responsiveness
        
        Returns:
            bool: True if wake word detected, False otherwise
        """
        print(f"🔊 Listening for wake word: '{Config.WAKE_WORD}'")
        print("💡 Tip: Speak clearly and naturally - I'll detect when you're done speaking")
        
        while True:
            try:
                # Use advanced pause detection for wake word too
                text = self.listen_with_pause_detection(
                    initial_timeout=None,  # No timeout for wake word
                    max_silence_duration=3.0  # Shorter max silence for wake word
                )
                
                if text and Config.WAKE_WORD.lower() in text:
                    print("🎉 Wake word detected!")
                    return True
                elif text:
                    print(f"💭 I heard '{text}' but that's not the wake word. Try saying '{Config.WAKE_WORD}'")
                    
            except KeyboardInterrupt:
                print("\n👋 Stopping wake word detection...")
                return False
    
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
    
    def adjust_sensitivity(self, sensitivity_level="medium"):
        """
        Adjust speech detection sensitivity
        
        Args:
            sensitivity_level: "low", "medium", "high"
        """
        base_threshold = self.energy_threshold
        
        if sensitivity_level == "low":
            self.energy_threshold = base_threshold * 1.5
            self.pause_threshold = 1.2
            print("🔇 Speech sensitivity set to LOW")
        elif sensitivity_level == "medium":
            self.energy_threshold = base_threshold
            self.pause_threshold = 0.8
            print("🔊 Speech sensitivity set to MEDIUM")
        elif sensitivity_level == "high":
            self.energy_threshold = base_threshold * 0.7
            self.pause_threshold = 0.6
            print("🔊 Speech sensitivity set to HIGH")
        
        # Update recognizer settings
        self.recognizer.energy_threshold = self.energy_threshold
    
    def get_audio_level_indicator(self, duration=3):
        """
        Show real-time audio level for testing microphone
        
        Args:
            duration: Duration to show audio levels
        """
        print(f"🎤 Testing microphone for {duration} seconds...")
        print("📊 Audio levels (speak to see the bars):")
        
        start_time = time.time()
        
        with self.microphone as source:
            while time.time() - start_time < duration:
                try:
                    audio = self.recognizer.listen(source, timeout=0.1, phrase_time_limit=0.1)
                    energy = self._calculate_audio_energy(audio)
                    
                    # Create visual indicator
                    bar_length = min(50, int(energy / 10))
                    bar = "█" * bar_length
                    level_indicator = f"Level: {energy:6.1f} |{bar:<50}|"
                    
                    print(f"\r{level_indicator}", end="", flush=True)
                    
                except sr.WaitTimeoutError:
                    continue
                except KeyboardInterrupt:
                    break
        
        print("\n✅ Microphone test completed!")
