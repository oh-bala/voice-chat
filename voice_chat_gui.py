#!/usr/bin/env python3

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import queue
import sys
import math
import random
from datetime import datetime

from config import Config
from voice_chat.speech.speech_recognition_handler import SpeechRecognitionHandler
from voice_chat.speech.advanced_speech_handler import AdvancedSpeechHandler
from voice_chat.ai.openai_client import OpenAIClient
from voice_chat.speech.text_to_speech import TextToSpeechHandler
from voice_chat.ui.mcp_config_gui import MCPConfigGUI
from voice_chat.ui.app_settings import AppSettings

class VoiceChatGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Voice Chat Assistant - Enhanced with Pause Detection")
        self.root.geometry("800x750")  # Increased height for voice visualization
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Application state
        self.running = False
        self.conversation_active = False
        self.listening_for_wake_word = False
        self.enhanced_mode = tk.BooleanVar(value=True)  # Default to enhanced mode
        
        # Voice visualization state
        self.voice_state = "idle"  # idle, listening, user_speaking, ai_speaking, mic_test
        self.animation_frame = 0
        self.voice_bars = []  # Will hold the voice visualization bars
        self.mic_test_levels = []  # Store microphone test audio levels
        
        # Message queue for thread communication
        self.message_queue = queue.Queue()
        
        # Initialize components
        self.speech_recognizer = None
        self.openai_client = None
        self.tts_handler = None
        self.settings = AppSettings()
        
        self.setup_ui()
        self.setup_components()
        
        # Start message processing and animations
        self.process_messages()
        self.animate_voice_visualization()
    
    def setup_ui(self):
        """Setup the user interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Voice Chat Assistant", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 10))
        
        # Status frame
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding="5")
        status_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        status_frame.columnconfigure(1, weight=1)
        
        ttk.Label(status_frame, text="App Status:").grid(row=0, column=0, sticky=tk.W)
        self.app_status_label = ttk.Label(status_frame, text="Stopped", foreground="red")
        self.app_status_label.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(status_frame, text="Conversation:").grid(row=1, column=0, sticky=tk.W)
        self.conversation_status_label = ttk.Label(status_frame, text="Inactive", foreground="gray")
        self.conversation_status_label.grid(row=1, column=1, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(status_frame, text="Listening:").grid(row=2, column=0, sticky=tk.W)
        self.listening_status_label = ttk.Label(status_frame, text="No", foreground="gray")
        self.listening_status_label.grid(row=2, column=1, sticky=tk.W, padx=(10, 0))
        
        # Conversation display
        conversation_frame = ttk.LabelFrame(main_frame, text="Conversation", padding="5")
        conversation_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        conversation_frame.columnconfigure(0, weight=1)
        conversation_frame.rowconfigure(0, weight=1)
        
        self.conversation_text = scrolledtext.ScrolledText(conversation_frame, wrap=tk.WORD, 
                                                          height=20, state=tk.DISABLED)
        self.conversation_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Control buttons frame
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E))
        
        self.start_button = ttk.Button(control_frame, text="Start Assistant", 
                                      command=self.start_assistant)
        self.start_button.grid(row=0, column=0, padx=(0, 5))
        
        self.stop_button = ttk.Button(control_frame, text="Stop Assistant", 
                                     command=self.stop_assistant, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=1, padx=5)
        
        self.reset_button = ttk.Button(control_frame, text="Reset Conversation", 
                                      command=self.reset_conversation)
        self.reset_button.grid(row=0, column=2, padx=5)
        
        self.clear_button = ttk.Button(control_frame, text="Clear Display", 
                                      command=self.clear_conversation)
        self.clear_button.grid(row=0, column=3, padx=5)
        
        self.mcp_config_button = ttk.Button(control_frame, text="MCP Config", 
                                           command=self.open_mcp_config)
        self.mcp_config_button.grid(row=0, column=4, padx=5)
        
        # Settings frame
        settings_frame = ttk.LabelFrame(main_frame, text="Settings", padding="5")
        settings_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        settings_frame.columnconfigure(2, weight=1)
        
        # Enhanced mode toggle
        enhanced_checkbox = ttk.Checkbutton(
            settings_frame, 
            text="🚀 Enhanced Mode (Natural Pause Detection)", 
            variable=self.enhanced_mode,
            command=self.on_enhanced_mode_changed
        )
        enhanced_checkbox.grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=(0, 5))
        
        # Mode description
        self.mode_description_label = ttk.Label(
            settings_frame, 
            text="Enhanced: Detects natural pauses automatically",
            font=("Arial", 8),
            foreground="green"
        )
        self.mode_description_label.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))
        
        # Enhanced controls frame
        enhanced_controls_frame = ttk.Frame(settings_frame)
        enhanced_controls_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Microphone test button
        self.mic_test_button = ttk.Button(
            enhanced_controls_frame,
            text="🎤 Test Microphone",
            command=self.test_microphone
        )
        self.mic_test_button.grid(row=0, column=0, padx=(0, 10))
        
        # Sensitivity controls
        ttk.Label(enhanced_controls_frame, text="Sensitivity:").grid(row=0, column=1, padx=(10, 5))
        
        sensitivity_frame = ttk.Frame(enhanced_controls_frame)
        sensitivity_frame.grid(row=0, column=2, padx=(5, 0))
        
        self.sensitivity_var = tk.StringVar(value="medium")
        ttk.Radiobutton(sensitivity_frame, text="Low", variable=self.sensitivity_var, 
                       value="low", command=self.on_sensitivity_changed).grid(row=0, column=0, padx=(0, 5))
        ttk.Radiobutton(sensitivity_frame, text="Medium", variable=self.sensitivity_var, 
                       value="medium", command=self.on_sensitivity_changed).grid(row=0, column=1, padx=5)
        ttk.Radiobutton(sensitivity_frame, text="High", variable=self.sensitivity_var, 
                       value="high", command=self.on_sensitivity_changed).grid(row=0, column=2, padx=(5, 0))
        
        # Basic settings
        basic_settings_frame = ttk.Frame(settings_frame)
        basic_settings_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E))
        basic_settings_frame.columnconfigure(1, weight=1)
        
        ttk.Label(basic_settings_frame, text="Wake Word:").grid(row=0, column=0, sticky=tk.W)
        self.wake_word_label = ttk.Label(basic_settings_frame, text=Config.WAKE_WORD, 
                                        font=("Arial", 9, "italic"))
        self.wake_word_label.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(basic_settings_frame, text="Exit Words:").grid(row=1, column=0, sticky=tk.W)
        self.exit_words_label = ttk.Label(basic_settings_frame, text=", ".join(Config.EXIT_WORDS), 
                                         font=("Arial", 9, "italic"))
        self.exit_words_label.grid(row=1, column=1, sticky=tk.W, padx=(10, 0))

        # TTS Provider and Voice selection
        tts_frame = ttk.LabelFrame(settings_frame, text="Text-to-Speech", padding="5")
        tts_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        tts_frame.columnconfigure(1, weight=1)

        ttk.Label(tts_frame, text="Provider:").grid(row=0, column=0, sticky=tk.W)
        self.tts_provider_var = tk.StringVar(value=self.settings.get_tts_provider())
        self.tts_provider_combo = ttk.Combobox(tts_frame, textvariable=self.tts_provider_var, state="readonly",
                                              values=["pyttsx3", "elevenlabs"])
        self.tts_provider_combo.grid(row=0, column=1, sticky=(tk.W, tk.E))
        self.tts_provider_combo.bind("<<ComboboxSelected>>", self.on_tts_provider_changed)

        ttk.Label(tts_frame, text="Voice:").grid(row=1, column=0, sticky=tk.W)
        self.tts_voice_var = tk.StringVar(value=self.settings.get_elevenlabs_voice_id() or "")
        self.tts_voice_combo = ttk.Combobox(tts_frame, textvariable=self.tts_voice_var, state="readonly")
        self.tts_voice_combo.grid(row=1, column=1, sticky=(tk.W, tk.E))
        ttk.Button(tts_frame, text="Refresh Voices", command=self.refresh_tts_voices).grid(row=1, column=2, padx=5)
        
        # Voice Visualization
        self.setup_voice_visualization(main_frame)
    
    def setup_voice_visualization(self, parent_frame):
        """Setup the voice visualization at the bottom of the window"""
        # Voice visualization frame
        viz_frame = ttk.LabelFrame(parent_frame, text="Voice Activity", padding="10")
        viz_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Status label
        self.voice_status_label = ttk.Label(viz_frame, text="🔇 Idle", font=("Arial", 10, "bold"))
        self.voice_status_label.grid(row=0, column=0, pady=(0, 10))
        
        # Canvas for voice bars
        self.voice_canvas = tk.Canvas(viz_frame, height=80, bg="#1a1a1a", highlightthickness=0)
        self.voice_canvas.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        viz_frame.columnconfigure(0, weight=1)
        
        # Initialize voice bars
        self.create_voice_bars()
    
    def create_voice_bars(self):
        """Create the animated voice bars"""
        self.voice_bars = []
        num_bars = 20
        
        # Calculate bar dimensions
        canvas_width = 760  # Approximate width
        bar_width = (canvas_width - (num_bars - 1) * 4) // num_bars  # 4px spacing
        
        for i in range(num_bars):
            x = i * (bar_width + 4) + 10
            bar_id = self.voice_canvas.create_rectangle(
                x, 70, x + bar_width, 75,
                fill="#333333", outline="#333333"
            )
            self.voice_bars.append({
                'id': bar_id,
                'x': x,
                'width': bar_width,
                'base_height': 5,
                'current_height': 5
            })
    
    def animate_voice_visualization(self):
        """Animate the voice visualization based on current state"""
        if not hasattr(self, 'voice_canvas') or not self.voice_bars:
            self.root.after(100, self.animate_voice_visualization)
            return
        
        self.animation_frame += 1
        
        # Update voice state based on application state
        if not self.running:
            self.voice_state = "idle"
        elif self.listening_for_wake_word and not self.conversation_active:
            self.voice_state = "listening"
        elif self.conversation_active:
            if hasattr(self.tts_handler, 'is_currently_speaking') and self.tts_handler.is_currently_speaking():
                self.voice_state = "ai_speaking"
            else:
                self.voice_state = "user_speaking"  # Assume user is speaking during conversation
        
        # Update status label
        status_texts = {
            "idle": "🔇 Idle",
            "listening": "👂 Listening for wake word...",
            "user_speaking": "🗣️ You are speaking...",
            "ai_speaking": "🤖 AI Assistant speaking...",
            "mic_test": "🎤 Testing microphone - Speak now!"
        }
        
        status_colors = {
            "idle": "gray",
            "listening": "blue",
            "user_speaking": "#4CAF50",  # Green
            "ai_speaking": "#FF5722",   # Orange/Red
            "mic_test": "#9C27B0"       # Purple
        }
        
        self.voice_status_label.config(
            text=status_texts.get(self.voice_state, "🔇 Idle"),
            foreground=status_colors.get(self.voice_state, "gray")
        )
        
        # Animate bars based on state
        self.update_voice_bars()
        
        # Schedule next animation frame
        self.root.after(50, self.animate_voice_visualization)  # 20 FPS
    
    def update_voice_bars(self):
        """Update the visual appearance of voice bars based on current state"""
        for i, bar in enumerate(self.voice_bars):
            if self.voice_state == "idle":
                # Static low bars
                target_height = bar['base_height']
                color = "#333333"
                
            elif self.voice_state == "listening":
                # Gentle pulsing animation
                pulse = math.sin(self.animation_frame * 0.1 + i * 0.3) * 0.5 + 0.5
                target_height = bar['base_height'] + pulse * 15
                color = f"#{int(100 + pulse * 155):02x}{int(150 + pulse * 105):02x}ff"  # Blue gradient
                
            elif self.voice_state == "user_speaking":
                # Random animated bars simulating user speech
                intensity = (math.sin(self.animation_frame * 0.15 + i * 0.8) * 0.5 + 0.5) * random.uniform(0.7, 1.3)
                target_height = bar['base_height'] + intensity * 30
                green_val = int(76 + intensity * 100)  # Varying green
                color = f"#{int(intensity * 100):02x}{green_val:02x}{int(80 + intensity * 50):02x}"  # Green tones
                
            elif self.voice_state == "ai_speaking":
                # Smooth wave animation for AI speech
                wave = math.sin(self.animation_frame * 0.2 + i * 0.4) * 0.5 + 0.5
                secondary_wave = math.cos(self.animation_frame * 0.15 + i * 0.2) * 0.3 + 0.7
                combined_intensity = (wave * 0.7 + secondary_wave * 0.3)
                target_height = bar['base_height'] + combined_intensity * 35
                red_val = int(255 * combined_intensity)
                orange_val = int(87 + combined_intensity * 100)
                color = f"#{red_val:02x}{orange_val:02x}22"  # Orange/Red gradient
                
            elif self.voice_state == "mic_test":
                # Real microphone level visualization during test
                if len(self.mic_test_levels) > i:
                    level = self.mic_test_levels[i]
                    normalized_level = min(level / 1000, 1.0)  # Normalize to 0-1
                    target_height = bar['base_height'] + normalized_level * 50
                    purple_intensity = int(156 + normalized_level * 99)  # Varying purple
                    color = f"#{purple_intensity:02x}27{purple_intensity:02x}"  # Purple tones
                else:
                    # Default animation while waiting for mic data
                    pulse = math.sin(self.animation_frame * 0.2 + i * 0.5) * 0.5 + 0.5
                    target_height = bar['base_height'] + pulse * 20
                    color = f"#9C27{int(180 + pulse * 75):02x}"  # Purple gradient
            
            else:
                target_height = bar['base_height']
                color = "#333333"
            
            # Smooth height transition
            bar['current_height'] += (target_height - bar['current_height']) * 0.3
            
            # Update bar appearance
            y_top = 75 - bar['current_height']
            self.voice_canvas.coords(
                bar['id'],
                bar['x'], y_top,
                bar['x'] + bar['width'], 75
            )
            self.voice_canvas.itemconfig(bar['id'], fill=color, outline=color)
    
    def set_voice_state(self, state):
        """Manually set the voice state for testing or external control"""
        if state in ["idle", "listening", "user_speaking", "ai_speaking", "mic_test"]:
            self.voice_state = state
    
    def run_gui_microphone_test(self, duration=5):
        """Run microphone test with GUI visualization"""
        print(f"🎤 Testing microphone for {duration} seconds...")
        print("📊 Audio levels will be shown in the GUI visualization")
        
        import speech_recognition as sr
        import time
        
        start_time = time.time()
        
        with self.speech_recognizer.microphone as source:
            while time.time() - start_time < duration:
                try:
                    audio = self.speech_recognizer.recognizer.listen(source, timeout=0.1, phrase_time_limit=0.1)
                    energy = self.speech_recognizer._calculate_audio_energy(audio)
                    
                    # Update mic test levels for visualization
                    # Create levels for each bar with some variation
                    base_level = max(0, energy - 100)  # Adjust baseline
                    levels = []
                    for i in range(20):  # 20 bars
                        # Add some variation and simulate frequency distribution
                        variation = random.uniform(0.7, 1.3)
                        frequency_factor = 1.0 - abs(i - 10) * 0.05  # Peak in middle
                        bar_level = base_level * variation * frequency_factor
                        levels.append(max(0, bar_level))
                    
                    self.mic_test_levels = levels
                    
                    # Print level indicator to console as backup
                    bar_length = min(50, int(energy / 20))
                    bar = "█" * bar_length
                    level_indicator = f"Level: {energy:6.1f} |{bar:<50}|"
                    print(f"\r{level_indicator}", end="", flush=True)
                    
                except sr.WaitTimeoutError:
                    # No audio detected, gradually reduce levels
                    self.mic_test_levels = [max(0, level * 0.8) for level in self.mic_test_levels] if self.mic_test_levels else [0] * 20
                    continue
                except KeyboardInterrupt:
                    break
        
        print("\n✅ Microphone test completed!")
        # Clear mic test levels
        self.mic_test_levels = [0] * 20
    
    def setup_components(self):
        """Initialize the voice chat components"""
        try:
            self.add_message("Initializing components...", "system")
            # Initialize based on enhanced mode setting
            self._initialize_speech_recognizer()
            self.openai_client = OpenAIClient()
            self.tts_handler = TextToSpeechHandler()
            # Apply persisted provider
            try:
                self.tts_handler.set_provider(self.settings.get_tts_provider())
            except Exception as e:
                self.add_message(f"TTS provider setup failed: {e}", "error")
            # Load voices into dropdown
            self.refresh_tts_voices()
            self.add_message("All components initialized successfully!", "system")
        except Exception as e:
            self.add_message(f"Error initializing components: {e}", "error")
            messagebox.showerror("Initialization Error", f"Failed to initialize: {e}")
    
    def _initialize_speech_recognizer(self):
        """Initialize the appropriate speech recognizer based on mode"""
        # Clean up existing recognizer first
        self._cleanup_speech_recognizer()
        
        try:
            if self.enhanced_mode.get():
                self.speech_recognizer = AdvancedSpeechHandler()
                self.add_message("Using enhanced speech recognition with pause detection", "system")
            else:
                self.speech_recognizer = SpeechRecognitionHandler()
                self.add_message("Using basic speech recognition", "system")
        except Exception as e:
            self.add_message(f"Error initializing speech recognizer: {e}", "error")
            # Fallback to basic speech handler
            try:
                self.speech_recognizer = SpeechRecognitionHandler()
                self.add_message("Fallback to basic speech recognition", "system")
            except Exception as fallback_error:
                self.add_message(f"Critical: Failed to initialize any speech recognizer: {fallback_error}", "error")
                self.speech_recognizer = None
    
    def _cleanup_speech_recognizer(self):
        """Clean up speech recognizer resources"""
        if hasattr(self, 'speech_recognizer') and self.speech_recognizer:
            # Reset context state if available
            if hasattr(self.speech_recognizer, '_context_active'):
                self.speech_recognizer._context_active = False
            
            # Give threads time to finish
            import time
            time.sleep(0.1)
            
            self.speech_recognizer = None
    
    def on_enhanced_mode_changed(self):
        """Handle enhanced mode toggle"""
        if self.running:
            messagebox.showwarning(
                "Mode Change", 
                "Please stop the assistant before changing modes."
            )
            # Revert the checkbox
            self.enhanced_mode.set(not self.enhanced_mode.get())
            return
        
        # Update UI description
        if self.enhanced_mode.get():
            self.mode_description_label.config(
                text="Enhanced: Detects natural pauses automatically",
                foreground="green"
            )
            self.add_message("Switched to Enhanced Mode - Natural pause detection enabled", "system")
        else:
            self.mode_description_label.config(
                text="Basic: Uses fixed timeout for speech detection",
                foreground="blue"
            )
            self.add_message("Switched to Basic Mode - Fixed timeout speech detection", "system")
        
        # Re-initialize speech recognizer
        try:
            self._initialize_speech_recognizer()
        except Exception as e:
            self.add_message(f"Error switching modes: {e}", "error")
    
    def on_sensitivity_changed(self):
        """Handle sensitivity change"""
        if self.enhanced_mode.get() and hasattr(self.speech_recognizer, 'adjust_sensitivity'):
            sensitivity = self.sensitivity_var.get()
            try:
                self.speech_recognizer.adjust_sensitivity(sensitivity)
                self.add_message(f"Speech sensitivity set to {sensitivity}", "system")
            except Exception as e:
                self.add_message(f"Error adjusting sensitivity: {e}", "error")
        else:
            self.add_message("Sensitivity control is only available in Enhanced Mode", "system")
    
    def test_microphone(self):
        """Test microphone levels with GUI visualization"""
        if self.enhanced_mode.get() and hasattr(self.speech_recognizer, 'get_audio_level_indicator'):
            if self.running:
                messagebox.showwarning(
                    "Microphone Test", 
                    "Please stop the assistant before testing the microphone."
                )
                return
            
            self.add_message("🎤 Starting microphone test for 5 seconds...", "system")
            self.add_message("💬 Speak now to see the audio levels!", "system")
            
            def run_mic_test():
                try:
                    self.run_gui_microphone_test(5)
                    self.message_queue.put(("message", "✅ Microphone test completed!", "system"))
                    self.message_queue.put(("voice_state", "idle"))
                except Exception as e:
                    self.message_queue.put(("message", f"❌ Microphone test failed: {e}", "error"))
                    self.message_queue.put(("voice_state", "idle"))
            
            # Set voice state to show microphone activity
            self.message_queue.put(("voice_state", "mic_test"))
            threading.Thread(target=run_mic_test, daemon=True).start()
        else:
            messagebox.showinfo(
                "Microphone Test", 
                "Microphone testing is only available in Enhanced Mode."
            )
    
    def add_message(self, message, message_type="info"):
        """Add a message to the conversation display"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Configure text tags for different message types
        self.conversation_text.config(state=tk.NORMAL)
        
        if message_type == "user":
            self.conversation_text.insert(tk.END, f"[{timestamp}] You: {message}\n", "user")
        elif message_type == "assistant":
            self.conversation_text.insert(tk.END, f"[{timestamp}] Assistant: {message}\n", "assistant")
        elif message_type == "system":
            self.conversation_text.insert(tk.END, f"[{timestamp}] System: {message}\n", "system")
        elif message_type == "error":
            self.conversation_text.insert(tk.END, f"[{timestamp}] Error: {message}\n", "error")
        else:
            self.conversation_text.insert(tk.END, f"[{timestamp}] {message}\n")
        
        self.conversation_text.config(state=tk.DISABLED)
        self.conversation_text.see(tk.END)
        
        # Configure text tags
        self.conversation_text.tag_config("user", foreground="blue")
        self.conversation_text.tag_config("assistant", foreground="green")
        self.conversation_text.tag_config("system", foreground="purple")
        self.conversation_text.tag_config("error", foreground="red")
    
    def start_assistant(self):
        """Start the voice assistant"""
        if not self.running:
            # Ensure speech recognizer is properly initialized before starting
            if not self.speech_recognizer:
                try:
                    self._initialize_speech_recognizer()
                except Exception as e:
                    self.add_message(f"Failed to initialize speech recognizer: {e}", "error")
                    return
            
            # Check if speech recognizer is still None after initialization attempt
            if not self.speech_recognizer:
                self.add_message("Cannot start assistant: Speech recognizer initialization failed", "error")
                return
            
            self.running = True
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            
            self.app_status_label.config(text="Running", foreground="green")
            self.add_message("Voice Chat Assistant started!", "system")
            
            # Start listening thread
            threading.Thread(target=self.listen_for_wake_word, daemon=True).start()
    
    def stop_assistant(self):
        """Stop the voice assistant"""
        self.running = False
        self.conversation_active = False
        self.listening_for_wake_word = False
        
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        
        self.app_status_label.config(text="Stopped", foreground="red")
        self.conversation_status_label.config(text="Inactive", foreground="gray")
        self.listening_status_label.config(text="No", foreground="gray")
        
        # Stop TTS
        if self.tts_handler:
            self.tts_handler.stop_speaking()
        
        # Clean up speech recognizer resources
        self._cleanup_speech_recognizer()
        
        self.add_message("Voice Chat Assistant stopped.", "system")
    
    def reset_conversation(self):
        """Reset the conversation history"""
        if self.openai_client:
            self.openai_client.reset_conversation()
            self.add_message("Conversation history reset.", "system")
    
    def clear_conversation(self):
        """Clear the conversation display"""
        self.conversation_text.config(state=tk.NORMAL)
        self.conversation_text.delete(1.0, tk.END)
        self.conversation_text.config(state=tk.DISABLED)
    
    def listen_for_wake_word(self):
        """Listen for wake word in background thread"""
        self.listening_for_wake_word = True
        self.message_queue.put(("status", "listening", "Yes", "blue"))
        
        mode_text = "Enhanced" if self.enhanced_mode.get() else "Basic"
        self.message_queue.put(("message", f"Listening for wake word: '{Config.WAKE_WORD}' ({mode_text} mode)", "system"))
        
        while self.running and self.listening_for_wake_word:
            try:
                # Use appropriate detection method based on mode
                if self.enhanced_mode.get() and hasattr(self.speech_recognizer, 'listen_with_pause_detection'):
                    # For enhanced mode, use longer timeout and be more patient
                    text = self.speech_recognizer.listen_with_pause_detection(initial_timeout=10, max_silence_duration=3)
                else:
                    # For basic mode, use the standard method
                    text = self.speech_recognizer.listen_for_speech(timeout=5, phrase_time_limit=8)
                
                if text and Config.WAKE_WORD.lower() in text:
                    self.message_queue.put(("message", "🎉 Wake word detected!", "system"))
                    self.message_queue.put(("wake_word_detected",))
                    break
                elif text:
                    if self.enhanced_mode.get():
                        self.message_queue.put(("message", f"💭 Heard: '{text}' (Try saying '{Config.WAKE_WORD}')", "system"))
                    else:
                        self.message_queue.put(("message", f"Heard: '{text}' (not wake word)", "system"))
                else:
                    # No text detected, continue listening
                    if self.enhanced_mode.get():
                        self.message_queue.put(("message", "🔄 Still listening... (enhanced mode)", "system"))
                    
            except Exception as e:
                self.message_queue.put(("message", f"Error in wake word detection: {e}", "error"))
                # Don't break on error, try to recover
                import time
                time.sleep(1)  # Brief pause before retrying
                continue
        
        self.listening_for_wake_word = False
        if self.running:
            self.message_queue.put(("status", "listening", "No", "gray"))
    
    def start_conversation(self):
        """Start a conversation session"""
        self.conversation_active = True
        self.message_queue.put(("status", "conversation", "Active", "green"))
        self.message_queue.put(("message", "Conversation started!", "system"))
        
        # Queue TTS message instead of calling directly
        self.message_queue.put(("tts", "Hello! How can I help you today?"))
        
        # Start conversation thread
        threading.Thread(target=self.conversation_loop, daemon=True).start()
    
    def conversation_loop(self):
        """Main conversation loop"""
        while self.conversation_active and self.running:
            try:
                # Set voice state to user speaking during input
                self.message_queue.put(("voice_state", "user_speaking"))
                
                # Listen for user input with appropriate method
                if self.enhanced_mode.get() and hasattr(self.speech_recognizer, 'listen_with_pause_detection'):
                    self.message_queue.put(("message", "🎤 Listening (speak naturally, I'll detect pauses)...", "system"))
                    user_input = self.speech_recognizer.listen_with_pause_detection()
                else:
                    self.message_queue.put(("message", "🎤 Listening...", "system"))
                    user_input = self.speech_recognizer.listen_for_speech()
                
                if not user_input:
                    if self.enhanced_mode.get():
                        self.message_queue.put(("message", "No speech detected. Speak closer to the microphone.", "system"))
                    continue
                
                self.message_queue.put(("message", user_input, "user"))
                
                # Check for exit commands
                if self.speech_recognizer.is_exit_command(user_input):
                    self.message_queue.put(("end_conversation",))
                    break
                
                # Handle special enhanced commands
                if self.enhanced_mode.get() and self._handle_enhanced_commands(user_input):
                    continue
                
                # Get AI response
                self.message_queue.put(("message", "🤖 Thinking...", "system"))
                response = self.openai_client.get_response_sync(user_input)
                
                if response:
                    self.message_queue.put(("message", response, "assistant"))
                    # Queue TTS message for reliable delivery
                    self.message_queue.put(("tts", response))
                
            except Exception as e:
                self.message_queue.put(("message", f"Error in conversation: {e}", "error"))
        
        # End conversation
        self.conversation_active = False
        self.message_queue.put(("status", "conversation", "Inactive", "gray"))
        
        if self.running:
            # Restart wake word detection
            threading.Thread(target=self.listen_for_wake_word, daemon=True).start()
    
    def _handle_enhanced_commands(self, user_input):
        """Handle enhanced voice commands during conversation"""
        user_input_lower = user_input.lower().strip()
        
        # Microphone test during conversation
        if "test microphone" in user_input_lower:
            self.message_queue.put(("message", "Starting quick microphone test...", "system"))
            
            def quick_mic_test():
                try:
                    self.speech_recognizer.get_audio_level_indicator(3)  # Shorter test during conversation
                    self.message_queue.put(("message", "Microphone test completed!", "system"))
                except Exception as e:
                    self.message_queue.put(("message", f"Microphone test failed: {e}", "error"))
            
            threading.Thread(target=quick_mic_test, daemon=True).start()
            return True
        
        # Sensitivity adjustment during conversation
        if "low sensitivity" in user_input_lower or "less sensitive" in user_input_lower:
            self.speech_recognizer.adjust_sensitivity("low")
            self.message_queue.put(("message", "Speech sensitivity set to low", "system"))
            return True
        
        if "high sensitivity" in user_input_lower or "more sensitive" in user_input_lower:
            self.speech_recognizer.adjust_sensitivity("high")
            self.message_queue.put(("message", "Speech sensitivity set to high", "system"))
            return True
        
        if "normal sensitivity" in user_input_lower or "medium sensitivity" in user_input_lower:
            self.speech_recognizer.adjust_sensitivity("medium")
            self.message_queue.put(("message", "Speech sensitivity set to normal", "system"))
            return True
        
        return False
    
    def process_messages(self):
        """Process messages from background threads"""
        try:
            while True:
                message = self.message_queue.get_nowait()
                
                if message[0] == "message":
                    self.add_message(message[1], message[2] if len(message) > 2 else "info")
                elif message[0] == "status":
                    status_type, text, color = message[1], message[2], message[3]
                    if status_type == "listening":
                        self.listening_status_label.config(text=text, foreground=color)
                    elif status_type == "conversation":
                        self.conversation_status_label.config(text=text, foreground=color)
                elif message[0] == "wake_word_detected":
                    self.start_conversation()
                elif message[0] == "tts":
                    # Handle TTS messages in main thread
                    tts_text = message[1]
                    if self.tts_handler and tts_text:
                        print(f"TTS Queue: Processing '{tts_text[:50]}{'...' if len(tts_text) > 50 else ''}'")
                        # Use async speech to avoid blocking GUI
                        eleven_voice_id = self.settings.get_elevenlabs_voice_id()
                        success = self.tts_handler.speak(tts_text, blocking=False, voice_id=eleven_voice_id)
                        if not success:
                            print(f"TTS Failed for: {tts_text[:50]}")
                elif message[0] == "voice_state":
                    # Handle manual voice state changes
                    self.set_voice_state(message[1])
                elif message[0] == "end_conversation":
                    self.conversation_active = False
                    # Queue TTS message for reliable delivery
                    self.message_queue.put(("tts", "Goodbye! Say the wake word to start again."))
                
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self.process_messages)
    
    def open_mcp_config(self):
        """Open the MCP configuration window"""
        try:
            mcp_config_window = MCPConfigGUI(self.root)
            # The window will handle its own lifecycle
        except Exception as e:
            messagebox.showerror("MCP Config Error", f"Failed to open MCP configuration: {e}")
    
    def on_closing(self):
        """Handle window closing"""
        self.stop_assistant()
        self.root.destroy()

    def on_tts_provider_changed(self, event=None):
        provider = self.tts_provider_var.get()
        self.settings.set_tts_provider(provider)
        try:
            if self.tts_handler:
                self.tts_handler.set_provider(provider)
            self.refresh_tts_voices()
            self.add_message(f"TTS provider set to {provider}", "system")
        except Exception as e:
            self.add_message(f"Failed to switch TTS provider: {e}", "error")

    def refresh_tts_voices(self):
        try:
            if not self.tts_handler:
                return
            voices = self.tts_handler.get_available_voices() or []
            names = []
            id_by_name = {}
            for v in voices:
                name = v.get('name') or v.get('id')
                display = f"{name}"
                names.append(display)
                id_by_name[display] = v.get('id')
            self.tts_voice_combo['values'] = names
            # Try to reselect the persisted voice
            current_id = self.settings.get_elevenlabs_voice_id()
            if current_id:
                for display, vid in id_by_name.items():
                    if vid == current_id:
                        self.tts_voice_var.set(display)
                        break
            # Bind selection to persist id
            def on_voice_selected(event=None):
                display = self.tts_voice_var.get()
                selected_id = id_by_name.get(display)
                self.settings.set_elevenlabs_voice_id(selected_id)
                self.add_message(f"Selected voice: {display}", "system")
            self.tts_voice_combo.bind("<<ComboboxSelected>>", on_voice_selected)
        except Exception as e:
            self.add_message(f"Failed to load voices: {e}", "error")
    
    def run(self):
        """Start the GUI application"""
        self.root.mainloop()


def main():
    """Main entry point for GUI version"""
    try:
        app = VoiceChatGUI()
        app.run()
    except Exception as e:
        messagebox.showerror("Application Error", f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
