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
        self.microphone = self._select_best_microphone()
        self.recognizer = sr.Recognizer()
        self._context_active = False
        self.energy_threshold = 150
        self.dynamic_energy_threshold = True
        self.dynamic_energy_adjustment_damping = 0.15
        self.dynamic_energy_ratio = 1.5
        self.pause_threshold = 1.0
        self.max_pause_threshold = 3.0
        self.min_speech_duration = 0.5
        self.audio_buffer = deque(maxlen=50)
        self.is_listening = False
        self.speech_started = False
        self._calibrate_microphone()
    
    def _select_best_microphone(self):
        try:
            microphones = sr.Microphone.list_microphone_names()
            print(f"Available microphones: {len(microphones)}")
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
        print("Calibrating microphone for optimal speech detection...")
        try:
            if not self._context_active:
                with self.microphone as source:
                    self._context_active = True
                    print("Adjusting for ambient noise (please be quiet for 2 seconds)...")
                    self.recognizer.adjust_for_ambient_noise(source, duration=2)
                    base_threshold = self.recognizer.energy_threshold
                    self.energy_threshold = max(150, base_threshold * 0.8)
                    self.recognizer.energy_threshold = self.energy_threshold
                    print(f"Energy threshold set to: {self.energy_threshold}")
                    self.recognizer.dynamic_energy_threshold = self.dynamic_energy_threshold
                    self.recognizer.dynamic_energy_adjustment_damping = self.dynamic_energy_adjustment_damping
                    self.recognizer.dynamic_energy_ratio = self.dynamic_energy_ratio
                    self.recognizer.pause_threshold = 0.8
                    self.recognizer.non_speaking_duration = 0.5
                    self._context_active = False
        except Exception as e:
            print(f"Warning: Microphone calibration failed: {e}")
            self.energy_threshold = 200
            self.recognizer.energy_threshold = self.energy_threshold
            self._context_active = False
        print("✅ Microphone calibrated and ready!")
    
    def _calculate_audio_energy(self, audio_data):
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
            return self.energy_threshold * 0.5
    
    def listen_with_pause_detection(self, initial_timeout=5, max_silence_duration=None):
        if max_silence_duration is None:
            max_silence_duration = self.max_pause_threshold
        print("🎤 Listening for speech (speak naturally, I'll detect when you're done)...")
        try:
            result = self._listen_with_simple_pause_detection(initial_timeout, max_silence_duration)
            if result:
                return result
            print("🔄 Trying advanced chunked detection...")
            return self._listen_with_chunked_detection(initial_timeout, max_silence_duration)
        except Exception as e:
            logging.error(f"Advanced detection failed: {e}")
            return None
    
    def _listen_with_chunked_detection(self, initial_timeout, max_silence_duration):
        audio_chunks = []
        speech_detected = False
        silence_start = None
        last_speech_time = time.time()
        if self._context_active:
            print("⚠️  Context already active, creating new microphone instance for chunked detection")
            temp_mic = self._select_best_microphone()
            source_to_use = temp_mic
        else:
            source_to_use = self.microphone
        try:
            with source_to_use as source:
                self._context_active = True
                start_time = time.time()
                while True:
                    try:
                        audio_chunk = self.recognizer.listen(
                            source,
                            timeout=0.5,
                            phrase_time_limit=1.0
                        )
                        energy = self._calculate_audio_energy(audio_chunk)
                        current_time = time.time()
                        if energy > self.energy_threshold:
                            audio_chunks.append(audio_chunk)
                            if not speech_detected:
                                speech_detected = True
                                print("🗣️  Speech detected, continue speaking...")
                            last_speech_time = current_time
                            silence_start = None
                        else:
                            if speech_detected:
                                if silence_start is None:
                                    silence_start = current_time
                                silence_duration = current_time - silence_start
                                if silence_duration >= self.pause_threshold:
                                    speech_duration = last_speech_time - start_time
                                    if speech_duration >= self.min_speech_duration:
                                        print("✅ Natural pause detected, processing speech...")
                                        break
                                    else:
                                        speech_detected = False
                                        audio_chunks = []
                                        silence_start = None
                                elif silence_duration >= max_silence_duration:
                                    print("⏱️  Maximum silence reached, processing speech...")
                                    break
                            else:
                                if current_time - start_time > initial_timeout:
                                    print("⏱️  No speech detected within timeout period")
                                    return None
                    except sr.WaitTimeoutError:
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
            if not audio_chunks:
                return None
            print("🔄 Processing combined speech...")
            combined_audio = self._combine_audio_chunks(audio_chunks)
            if combined_audio:
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
        print("🎤 Listening with smart pause detection...")
        try:
            if self._context_active:
                print("⚠️  Context already active, creating new microphone instance")
                temp_mic = self._select_best_microphone()
                source_to_use = temp_mic
            else:
                source_to_use = self.microphone
            with source_to_use as source:
                self._context_active = True
                timeout = initial_timeout if initial_timeout else 10
                phrase_limit = max_silence_duration if max_silence_duration else 8
                print(f"⏰ Listening for up to {timeout}s, phrase limit {phrase_limit}s")
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_limit
                )
                print("🤖 Processing speech...")
                try:
                    text = self.recognizer.recognize_google(audio, language='en-US')
                    if text.strip():
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
        try:
            if not audio_chunks:
                return None
            if len(audio_chunks) == 1:
                return audio_chunks[0]
            sample_rate = audio_chunks[0].sample_rate
            sample_width = audio_chunks[0].sample_width
            combined_data = b""
            for chunk in audio_chunks:
                if hasattr(chunk, 'get_raw_data'):
                    combined_data += chunk.get_raw_data()
                else:
                    combined_data += chunk.frame_data
            combined_audio = sr.AudioData(combined_data, sample_rate, sample_width)
            return combined_audio
        except Exception as e:
            logging.error(f"Error combining audio chunks: {e}")
            return None
    
    def listen_for_wake_word_advanced(self):
        print(f"🔊 Listening for wake word: '{Config.WAKE_WORD}'")
        print("💡 Tip: Speak clearly and naturally - I'll detect when you're done speaking")
        while True:
            try:
                text = self.listen_with_pause_detection(
                    initial_timeout=None,
                    max_silence_duration=3.0
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
        if not text:
            return False
        return any(exit_word in text.lower() for exit_word in Config.EXIT_WORDS)
    
    def adjust_sensitivity(self, sensitivity_level="medium"):
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
        self.recognizer.energy_threshold = self.energy_threshold
    
    def get_audio_level_indicator(self, duration=3):
        print(f"🎤 Testing microphone for {duration} seconds...")
        print("📊 Audio levels (speak to see the bars):")
        start_time = time.time()
        with self.microphone as source:
            while time.time() - start_time < duration:
                try:
                    audio = self.recognizer.listen(source, timeout=0.1, phrase_time_limit=0.1)
                    energy = self._calculate_audio_energy(audio)
                    bar_length = min(50, int(energy / 10))
                    bar = "█" * bar_length
                    level_indicator = f"Level: {energy:6.1f} |{bar:<50}|"
                    print(f"\r{level_indicator}", end="", flush=True)
                except sr.WaitTimeoutError:
                    continue
                except KeyboardInterrupt:
                    break
        print("\n✅ Microphone test completed!")
