#!/usr/bin/env python3
"""
VAD Calibration GUI for Voice Activity Detection
Provides real-time audio visualization and parameter adjustment
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import numpy as np
import pyaudio
import struct
from collections import deque
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.animation as animation
from scipy import signal
from scipy.fft import fft, fftfreq
from config import Config

class VADCalibrationGUI:
    def __init__(self, parent=None):
        self.parent = parent
        self.root = tk.Toplevel(parent) if parent else tk.Tk()
        self.root.title("VAD Calibration - Voice Activity Detection")
        self.root.geometry("1400x1000")
        self.root.minsize(1200, 800)
        
        # Audio processing
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.is_recording = False
        self.audio_data = deque(maxlen=16000)  # Store 1 second of audio at 16kHz
        self.energy_history = deque(maxlen=200)  # Store energy levels for visualization
        self.spectrogram_data = deque(maxlen=100)  # Store spectrogram frames
        
        # VAD parameters (will be updated from config)
        self.vad_params = {
            'energy_threshold': Config.VAD_ENERGY_THRESHOLD,
            'silence_threshold': Config.VAD_SILENCE_THRESHOLD,
            'timeout': Config.VAD_TIMEOUT,
            'pause_threshold': Config.PAUSE_THRESHOLD,
            'dynamic_energy_threshold': True
        }
        
        # Statistics
        self.stats = {
            'peak_energy': 0,
            'avg_energy': 0,
            'min_energy': float('inf'),
            'max_energy': 0,
            'silence_detected': 0,
            'speech_detected': 0,
            'dominant_frequency': 0,
            'pitch_estimate': 0,
            'harmonic_ratio': 0
        }
        
        self.setup_ui()
        self.setup_audio()
        self.setup_visualization()
        
        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def setup_ui(self):
        """Setup the user interface"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)  # Give more weight to visualization area
        
        # Title
        title_label = ttk.Label(main_frame, text="🎤 VAD Calibration Tool", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, pady=(0, 10))
        
        # Controls panel - placed above graphics
        controls_frame = ttk.LabelFrame(main_frame, text="Controls & Parameters", padding="10")
        controls_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        controls_frame.columnconfigure(0, weight=1)
        

        
        # Create a horizontal layout for controls
        controls_horizontal_frame = ttk.Frame(controls_frame)
        controls_horizontal_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        controls_horizontal_frame.columnconfigure(0, weight=1)
        controls_horizontal_frame.columnconfigure(2, weight=1)
        controls_horizontal_frame.columnconfigure(4, weight=1)
        
        # VAD Parameters
        params_frame = ttk.LabelFrame(controls_horizontal_frame, text="VAD Parameters", padding="5")
        params_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        params_frame.columnconfigure(1, weight=1)
        
        # Energy Threshold
        ttk.Label(params_frame, text="Energy Threshold:").grid(row=0, column=0, sticky=tk.W)
        self.energy_threshold_var = tk.DoubleVar(value=self.vad_params['energy_threshold'])
        self.energy_threshold_scale = ttk.Scale(params_frame, from_=50, to=1000, 
                                               variable=self.energy_threshold_var, 
                                               orient=tk.HORIZONTAL,
                                               command=self.on_energy_threshold_changed)
        self.energy_threshold_scale.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0))
        self.energy_threshold_label = ttk.Label(params_frame, text=f"{self.vad_params['energy_threshold']}")
        self.energy_threshold_label.grid(row=0, column=2, padx=(5, 0))
        
        # Silence Threshold
        ttk.Label(params_frame, text="Silence Threshold (s):").grid(row=1, column=0, sticky=tk.W)
        self.silence_threshold_var = tk.DoubleVar(value=self.vad_params['silence_threshold'])
        self.silence_threshold_scale = ttk.Scale(params_frame, from_=0.1, to=2.0, 
                                                variable=self.silence_threshold_var, 
                                                orient=tk.HORIZONTAL,
                                                command=self.on_silence_threshold_changed)
        self.silence_threshold_scale.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 0))
        self.silence_threshold_label = ttk.Label(params_frame, text=f"{self.vad_params['silence_threshold']:.1f}")
        self.silence_threshold_label.grid(row=1, column=2, padx=(5, 0))
        
        # Pause Threshold
        ttk.Label(params_frame, text="Pause Threshold (s):").grid(row=2, column=0, sticky=tk.W)
        self.pause_threshold_var = tk.DoubleVar(value=self.vad_params['pause_threshold'])
        self.pause_threshold_scale = ttk.Scale(params_frame, from_=0.3, to=2.0, 
                                              variable=self.pause_threshold_var, 
                                              orient=tk.HORIZONTAL,
                                              command=self.on_pause_threshold_changed)
        self.pause_threshold_scale.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(10, 0))
        self.pause_threshold_label = ttk.Label(params_frame, text=f"{self.vad_params['pause_threshold']:.1f}")
        self.pause_threshold_label.grid(row=2, column=2, padx=(5, 0))
        
        # Dynamic Energy Threshold
        self.dynamic_energy_var = tk.BooleanVar(value=self.vad_params['dynamic_energy_threshold'])
        dynamic_check = ttk.Checkbutton(params_frame, text="Dynamic Energy Threshold", 
                                       variable=self.dynamic_energy_var,
                                       command=self.on_dynamic_energy_changed)
        dynamic_check.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=(10, 0))
        
        # Statistics
        stats_frame = ttk.LabelFrame(controls_horizontal_frame, text="Real-time Statistics", padding="5")
        stats_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        stats_frame.columnconfigure(1, weight=1)
        
        # Recording Status
        recording_status_frame = ttk.LabelFrame(controls_horizontal_frame, text="Recording Status", padding="5")
        recording_status_frame.grid(row=0, column=2, sticky=(tk.W, tk.E), padx=(5, 0))
        recording_status_frame.columnconfigure(1, weight=1)
        
        self.record_button = ttk.Button(recording_status_frame, text="🔴 Start Recording", 
                                       command=self.toggle_recording)
        self.record_button.grid(row=0, column=0, columnspan=2, pady=5)
        
        self.status_label = ttk.Label(recording_status_frame, text="⏸️ Ready to record", 
                                     font=("Arial", 10, "bold"))
        self.status_label.grid(row=1, column=0, columnspan=2, pady=5)
        
        self.peak_energy_label = ttk.Label(stats_frame, text="Peak Energy: 0")
        self.peak_energy_label.grid(row=0, column=0, sticky=tk.W)
        
        self.avg_energy_label = ttk.Label(stats_frame, text="Avg Energy: 0")
        self.avg_energy_label.grid(row=1, column=0, sticky=tk.W)
        
        self.speech_detected_label = ttk.Label(stats_frame, text="Speech Detected: 0")
        self.speech_detected_label.grid(row=2, column=0, sticky=tk.W)
        
        self.silence_detected_label = ttk.Label(stats_frame, text="Silence Detected: 0")
        self.silence_detected_label.grid(row=3, column=0, sticky=tk.W)
        
        self.dominant_freq_label = ttk.Label(stats_frame, text="Dominant Freq: 0 Hz")
        self.dominant_freq_label.grid(row=4, column=0, sticky=tk.W)
        
        self.pitch_label = ttk.Label(stats_frame, text="Pitch Estimate: 0 Hz")
        self.pitch_label.grid(row=5, column=0, sticky=tk.W)
        
        self.harmonic_ratio_label = ttk.Label(stats_frame, text="Harmonic Ratio: 0.0")
        self.harmonic_ratio_label.grid(row=6, column=0, sticky=tk.W)
        
        # Action buttons
        actions_frame = ttk.Frame(controls_frame)
        actions_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.apply_button = ttk.Button(actions_frame, text="✅ Apply Settings", 
                                      command=self.apply_settings)
        self.apply_button.grid(row=0, column=0, padx=(0, 5))
        
        self.reset_button = ttk.Button(actions_frame, text="🔄 Reset to Defaults", 
                                      command=self.reset_to_defaults)
        self.reset_button.grid(row=0, column=1, padx=5)
        
        self.test_button = ttk.Button(actions_frame, text="🧪 Test VAD", 
                                     command=self.test_vad)
        self.test_button.grid(row=0, column=2, padx=(5, 0))
        
        # Visualization panel at bottom - line by line layout
        viz_frame = ttk.LabelFrame(main_frame, text="Real-time Audio Visualization", padding="10")
        viz_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        viz_frame.columnconfigure(0, weight=1)
        viz_frame.rowconfigure(0, weight=1)
        viz_frame.rowconfigure(1, weight=1)
        viz_frame.rowconfigure(2, weight=1)
        viz_frame.rowconfigure(3, weight=1)
        
        # Create matplotlib figure for visualization with larger size for line-by-line layout
        self.fig = Figure(figsize=(14, 12), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, viz_frame)
        self.canvas.get_tk_widget().grid(row=0, column=0, rowspan=4, sticky=(tk.W, tk.E, tk.N, tk.S))
        
    def setup_audio(self):
        """Setup audio stream for recording"""
        try:
            self.stream = self.audio.open(
                format=pyaudio.paFloat32,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=1024,
                stream_callback=self.audio_callback
            )
            self.stream.stop_stream()
        except Exception as e:
            messagebox.showerror("Audio Error", f"Failed to initialize audio: {e}")
            
    def audio_callback(self, in_data, frame_count, time_info, status):
        """Callback for audio processing"""
        if self.is_recording:
            # Convert audio data to numpy array
            audio_data = struct.unpack('f' * frame_count, in_data)
            audio_array = np.array(audio_data)
            
            # Store audio data for spectrogram
            self.audio_data.extend(audio_array)
            
            # Calculate energy
            energy = np.sqrt(np.mean(audio_array ** 2))
            self.energy_history.append(energy)
            
            # Update statistics
            self.stats['peak_energy'] = max(self.stats['peak_energy'], energy)
            self.stats['avg_energy'] = np.mean(list(self.energy_history))
            self.stats['min_energy'] = min(self.stats['min_energy'], energy)
            self.stats['max_energy'] = max(self.stats['max_energy'], energy)
            
            # Detect speech/silence
            if energy > self.vad_params['energy_threshold']:
                self.stats['speech_detected'] += 1
            else:
                self.stats['silence_detected'] += 1
                
        return (in_data, pyaudio.paContinue)
        
    def setup_visualization(self):
        """Setup matplotlib visualization"""
        # Create a 4-row layout of subplots (one chart per row)
        self.ax1 = self.fig.add_subplot(411)  # Energy plot (top)
        self.ax2 = self.fig.add_subplot(412)  # Histogram (second)
        self.ax3 = self.fig.add_subplot(413)  # Spectrogram (third)
        self.ax4 = self.fig.add_subplot(414)  # Frequency spectrum (bottom)
        
        self.ax1.set_title("Real-time Audio Energy", fontsize=12, fontweight='bold')
        self.ax1.set_ylabel("Energy Level")
        self.ax1.grid(True, alpha=0.3)
        
        self.ax2.set_title("Energy Distribution", fontsize=12, fontweight='bold')
        self.ax2.set_xlabel("Energy Level")
        self.ax2.set_ylabel("Frequency")
        self.ax2.grid(True, alpha=0.3)
        
        self.ax3.set_title("Spectrogram (Frequency vs Time)", fontsize=12, fontweight='bold')
        self.ax3.set_xlabel("Time (s)")
        self.ax3.set_ylabel("Frequency (Hz)")
        
        self.ax4.set_title("Frequency Spectrum", fontsize=12, fontweight='bold')
        self.ax4.set_xlabel("Frequency (Hz)")
        self.ax4.set_ylabel("Magnitude")
        self.ax4.grid(True, alpha=0.3)
        
        self.fig.tight_layout()
        
        # Start animation
        self.ani = animation.FuncAnimation(self.fig, self.update_plot, interval=100, blit=False, cache_frame_data=False)
        
    def analyze_frequency(self, audio_data, sample_rate=16000):
        """Analyze frequency content of audio data"""
        if len(audio_data) < 1024:
            return 0, 0, 0
            
        # Apply window function to reduce spectral leakage
        window = signal.windows.hann(len(audio_data))
        windowed_data = audio_data * window
        
        # Compute FFT
        fft_result = fft(windowed_data)
        freqs = fftfreq(len(audio_data), 1/sample_rate)
        
        # Get positive frequencies only
        positive_freqs = freqs[:len(freqs)//2]
        magnitude = np.abs(fft_result[:len(freqs)//2])
        
        # Find dominant frequency (peak magnitude)
        if len(magnitude) > 0:
            dominant_idx = np.argmax(magnitude)
            dominant_freq = positive_freqs[dominant_idx]
            
            # Estimate pitch (fundamental frequency)
            # Look for peaks in the frequency domain
            peaks, _ = signal.find_peaks(magnitude, height=np.max(magnitude)*0.1)
            if len(peaks) > 0:
                # Find the lowest frequency peak (fundamental)
                fundamental_idx = peaks[np.argmin(positive_freqs[peaks])]
                pitch_estimate = positive_freqs[fundamental_idx]
            else:
                pitch_estimate = dominant_freq
                
            # Calculate harmonic ratio (ratio of harmonic energy to total energy)
            # This is a simplified calculation
            harmonic_ratio = np.sum(magnitude[peaks]) / np.sum(magnitude) if len(peaks) > 0 else 0
            
            return dominant_freq, pitch_estimate, harmonic_ratio
        
        return 0, 0, 0
        
    def compute_spectrogram(self, audio_data, sample_rate=16000):
        """Compute spectrogram of audio data"""
        if len(audio_data) < 512:
            return None, None, None
            
        # Use scipy's spectrogram function
        f, t, Sxx = signal.spectrogram(
            audio_data, 
            sample_rate, 
            nperseg=512, 
            noverlap=256,
            window=signal.windows.hann(512)
        )
        
        return f, t, Sxx
        
    def update_plot(self, frame):
        """Update the visualization plots"""
        if not self.is_recording or len(self.energy_history) < 10:
            return
            
        # Clear previous plots
        self.ax1.clear()
        self.ax2.clear()
        self.ax3.clear()
        self.ax4.clear()
        
        # Energy plot
        energy_data = list(self.energy_history)
        time_data = list(range(len(energy_data)))
        
        self.ax1.plot(time_data, energy_data, 'b-', linewidth=1, alpha=0.7)
        self.ax1.axhline(y=self.vad_params['energy_threshold'], color='r', linestyle='--', 
                        label=f'Threshold: {self.vad_params["energy_threshold"]:.1f}')
        self.ax1.set_title("Real-time Audio Energy")
        self.ax1.set_ylabel("Energy Level")
        self.ax1.grid(True, alpha=0.3)
        self.ax1.legend()
        
        # Histogram
        if len(energy_data) > 0:
            self.ax2.hist(energy_data, bins=20, alpha=0.7, color='green', edgecolor='black')
            self.ax2.axvline(x=self.vad_params['energy_threshold'], color='r', linestyle='--', 
                           label=f'Threshold: {self.vad_params["energy_threshold"]:.1f}')
            self.ax2.set_title("Energy Distribution")
            self.ax2.set_xlabel("Energy Level")
            self.ax2.set_ylabel("Frequency")
            self.ax2.grid(True, alpha=0.3)
            self.ax2.legend()
        
        # Spectrogram
        if len(self.audio_data) >= 1024:
            audio_array = np.array(list(self.audio_data))
            f, t, Sxx = self.compute_spectrogram(audio_array)
            if f is not None and t is not None and Sxx is not None:
                # Convert to dB scale for better visualization
                Sxx_db = 10 * np.log10(Sxx + 1e-10)
                im = self.ax3.pcolormesh(t, f, Sxx_db, shading='gouraud', cmap='viridis')
                self.ax3.set_title("Spectrogram (Frequency vs Time)")
                self.ax3.set_xlabel("Time (s)")
                self.ax3.set_ylabel("Frequency (Hz)")
                self.ax3.set_ylim(0, 4000)  # Focus on speech frequencies
                
                # Add colorbar
                self.fig.colorbar(im, ax=self.ax3, label='Power (dB)')
        
        # Frequency spectrum
        if len(self.audio_data) >= 1024:
            audio_array = np.array(list(self.audio_data))
            dominant_freq, pitch_estimate, harmonic_ratio = self.analyze_frequency(audio_array)
            
            # Update statistics
            self.stats['dominant_frequency'] = dominant_freq
            self.stats['pitch_estimate'] = pitch_estimate
            self.stats['harmonic_ratio'] = harmonic_ratio
            
            # Plot frequency spectrum
            window = signal.windows.hann(len(audio_array))
            windowed_data = audio_array * window
            fft_result = fft(windowed_data)
            freqs = fftfreq(len(audio_array), 1/16000)
            
            # Get positive frequencies only
            positive_freqs = freqs[:len(freqs)//2]
            magnitude = np.abs(fft_result[:len(freqs)//2])
            
            self.ax4.plot(positive_freqs, magnitude, 'b-', linewidth=1, alpha=0.7)
            self.ax4.set_title("Frequency Spectrum")
            self.ax4.set_xlabel("Frequency (Hz)")
            self.ax4.set_ylabel("Magnitude")
            self.ax4.grid(True, alpha=0.3)
            self.ax4.set_xlim(0, 4000)  # Focus on speech frequencies
            
            # Mark dominant frequency and pitch
            if dominant_freq > 0:
                self.ax4.axvline(x=dominant_freq, color='r', linestyle='--', 
                               label=f'Dominant: {dominant_freq:.1f} Hz')
            if pitch_estimate > 0 and pitch_estimate != dominant_freq:
                self.ax4.axvline(x=pitch_estimate, color='g', linestyle='--', 
                               label=f'Pitch: {pitch_estimate:.1f} Hz')
            self.ax4.legend()
            
        self.fig.tight_layout()
        
    def toggle_recording(self):
        """Toggle audio recording"""
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()
            
    def start_recording(self):
        """Start audio recording"""
        try:
            self.stream.start_stream()
            self.is_recording = True
            self.record_button.config(text="⏸️ Stop Recording")
            self.status_label.config(text="🔴 Recording...", foreground="red")
            
            # Reset statistics
            self.stats = {
                'peak_energy': 0,
                'avg_energy': 0,
                'min_energy': float('inf'),
                'max_energy': 0,
                'silence_detected': 0,
                'speech_detected': 0,
                'dominant_frequency': 0,
                'pitch_estimate': 0,
                'harmonic_ratio': 0
            }
            
        except Exception as e:
            messagebox.showerror("Recording Error", f"Failed to start recording: {e}")
            
    def stop_recording(self):
        """Stop audio recording"""
        try:
            self.stream.stop_stream()
            self.is_recording = False
            self.record_button.config(text="🔴 Start Recording")
            self.status_label.config(text="⏸️ Ready to record", foreground="black")
        except Exception as e:
            messagebox.showerror("Recording Error", f"Failed to stop recording: {e}")
            
    def update_statistics_display(self):
        """Update the statistics display"""
        self.peak_energy_label.config(text=f"Peak Energy: {self.stats['peak_energy']:.1f}")
        self.avg_energy_label.config(text=f"Avg Energy: {self.stats['avg_energy']:.1f}")
        self.speech_detected_label.config(text=f"Speech Detected: {self.stats['speech_detected']}")
        self.silence_detected_label.config(text=f"Silence Detected: {self.stats['silence_detected']}")
        self.dominant_freq_label.config(text=f"Dominant Freq: {self.stats['dominant_frequency']:.1f} Hz")
        self.pitch_label.config(text=f"Pitch Estimate: {self.stats['pitch_estimate']:.1f} Hz")
        self.harmonic_ratio_label.config(text=f"Harmonic Ratio: {self.stats['harmonic_ratio']:.2f}")
        
        # Schedule next update
        self.root.after(100, self.update_statistics_display)
        
    def on_energy_threshold_changed(self, value):
        """Handle energy threshold slider change"""
        threshold = float(value)
        self.vad_params['energy_threshold'] = threshold
        self.energy_threshold_label.config(text=f"{threshold:.1f}")
        
    def on_silence_threshold_changed(self, value):
        """Handle silence threshold slider change"""
        threshold = float(value)
        self.vad_params['silence_threshold'] = threshold
        self.silence_threshold_label.config(text=f"{threshold:.1f}")
        
    def on_pause_threshold_changed(self, value):
        """Handle pause threshold slider change"""
        threshold = float(value)
        self.vad_params['pause_threshold'] = threshold
        self.pause_threshold_label.config(text=f"{threshold:.1f}")
        
    def on_dynamic_energy_changed(self):
        """Handle dynamic energy threshold checkbox change"""
        self.vad_params['dynamic_energy_threshold'] = self.dynamic_energy_var.get()
        
    def apply_settings(self):
        """Apply current VAD settings to the configuration"""
        try:
            # Update Config class attributes
            Config.VAD_ENERGY_THRESHOLD = self.vad_params['energy_threshold']
            Config.VAD_SILENCE_THRESHOLD = self.vad_params['silence_threshold']
            Config.VAD_TIMEOUT = self.vad_params['timeout']
            Config.PAUSE_THRESHOLD = self.vad_params['pause_threshold']
            
            messagebox.showinfo("Success", "VAD settings applied successfully!\n\n"
                               "The new settings will be used for voice activity detection.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply settings: {e}")
            
    def reset_to_defaults(self):
        """Reset VAD parameters to default values"""
        self.vad_params = {
            'energy_threshold': 200,
            'silence_threshold': 0.5,
            'timeout': 10.0,
            'pause_threshold': 0.8,
            'dynamic_energy_threshold': True
        }
        
        # Update UI
        self.energy_threshold_var.set(self.vad_params['energy_threshold'])
        self.silence_threshold_var.set(self.vad_params['silence_threshold'])
        self.pause_threshold_var.set(self.vad_params['pause_threshold'])
        self.dynamic_energy_var.set(self.vad_params['dynamic_energy_threshold'])
        
        self.energy_threshold_label.config(text=f"{self.vad_params['energy_threshold']}")
        self.silence_threshold_label.config(text=f"{self.vad_params['silence_threshold']:.1f}")
        self.pause_threshold_label.config(text=f"{self.vad_params['pause_threshold']:.1f}")
        
    def test_vad(self):
        """Test VAD functionality with current settings"""
        if not self.is_recording:
            messagebox.showwarning("Warning", "Please start recording first to test VAD.")
            return
            
        # Create a simple VAD test
        test_window = tk.Toplevel(self.root)
        test_window.title("VAD Test")
        test_window.geometry("400x300")
        
        test_label = ttk.Label(test_window, text="🎤 VAD Test Active\n\n"
                               "Speak into your microphone and watch the visualization.\n"
                               "The red line shows the energy threshold.\n"
                               "Speech should be detected above the threshold.",
                               font=("Arial", 12), justify=tk.CENTER)
        test_label.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
        
        # Auto-close after 10 seconds
        test_window.after(10000, test_window.destroy)
        
    def on_closing(self):
        """Handle window closing"""
        if self.is_recording:
            self.stop_recording()
        if self.stream:
            self.stream.close()
        if self.audio:
            self.audio.terminate()
        self.root.destroy()
        
    def run(self):
        """Run the calibration GUI"""
        # Start statistics update
        self.update_statistics_display()
        
        if not self.parent:
            self.root.mainloop()
        else:
            self.root.grab_set()  # Make window modal
            self.root.wait_window()

if __name__ == "__main__":
    app = VADCalibrationGUI()
    app.run()
