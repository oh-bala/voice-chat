# VAD Calibration Guide

## Overview

The Voice Activity Detection (VAD) Calibration tool provides real-time audio analysis and parameter adjustment to optimize voice capture, enhance human voice detection, and filter background noise. This tool includes advanced visualizations showing frequency content, pitch analysis, and harmonic information.

## Features

### 🎤 Real-time Audio Analysis
- **Energy Level Monitoring**: Real-time display of audio energy levels
- **Speech/Silence Detection**: Automatic detection of speech vs. silence periods
- **Frequency Analysis**: Dominant frequency and pitch estimation
- **Harmonic Analysis**: Harmonic ratio calculation for voice quality assessment

### 📊 Advanced Visualizations

#### 1. Energy Plot
- Shows real-time audio energy over time
- Displays the current energy threshold (red dashed line)
- Helps identify optimal threshold settings

#### 2. Energy Distribution Histogram
- Shows the distribution of energy levels
- Helps understand the range of audio levels in your environment
- Useful for setting appropriate energy thresholds

#### 3. Spectrogram (Frequency vs Time)
- **Color-coded frequency representation over time**
- Shows how frequency content changes during speech
- Helps identify:
  - Speech patterns and formants
  - Background noise characteristics
  - Voice quality and clarity
- **Frequency range**: 0-4000 Hz (optimized for speech)

#### 4. Frequency Spectrum
- **Real-time FFT analysis** of current audio
- Shows magnitude vs. frequency
- **Dominant frequency marker** (red dashed line)
- **Pitch estimate marker** (green dashed line)
- Helps identify:
  - Fundamental frequency of voice
  - Harmonic structure
  - Noise characteristics

### ⚙️ Adjustable Parameters

#### Energy Threshold (50-1000)
- **Purpose**: Determines the minimum energy level to consider as speech
- **Lower values**: More sensitive, may pick up background noise
- **Higher values**: Less sensitive, may miss quiet speech
- **Recommended**: Start with 200, adjust based on your environment

#### Silence Threshold (0.1-2.0 seconds)
- **Purpose**: How long to wait in silence before considering speech ended
- **Lower values**: Faster response, may cut off speech
- **Higher values**: Slower response, more natural pauses
- **Recommended**: 0.5-0.8 seconds for most environments

#### Pause Threshold (0.3-2.0 seconds)
- **Purpose**: Natural pause detection for enhanced mode
- **Lower values**: More aggressive pause detection
- **Higher values**: More tolerant of natural speech pauses
- **Recommended**: 0.8-1.2 seconds

#### Dynamic Energy Threshold
- **Purpose**: Automatically adjusts energy threshold based on ambient noise
- **Enabled**: Recommended for variable environments
- **Disabled**: Fixed threshold, better for consistent environments

## How to Use

### 1. Launch the Calibration Tool
- Click the **"🎤 VAD Calibration"** button in the main GUI
- Or run directly: `python test_vad_calibration.py`

### 2. Start Recording
- Click **"🔴 Start Recording"** to begin audio analysis
- The visualizations will start updating in real-time

### 3. Test Your Environment
- **Speak normally** into your microphone
- **Observe the visualizations**:
  - Energy plot should show clear peaks during speech
  - Spectrogram should show speech formants (typically 200-2000 Hz)
  - Frequency spectrum should show clear peaks for voice frequencies

### 4. Adjust Parameters
- **Energy Threshold**: Adjust until speech is clearly detected above the red line
- **Silence Threshold**: Set based on your natural speaking rhythm
- **Pause Threshold**: Adjust for comfortable conversation flow

### 5. Apply Settings
- Click **"✅ Apply Settings"** to save your configuration
- The new settings will be used by the voice chat system

### 6. Test VAD
- Click **"🧪 Test VAD"** to verify your settings work well
- Speak and observe the detection accuracy

## Understanding the Visualizations

### Spectrogram Colors
- **Bright colors (yellow/white)**: High energy at that frequency/time
- **Dark colors (blue/purple)**: Low energy
- **Speech patterns**: Horizontal bands (formants) that change over time
- **Background noise**: Usually appears as vertical lines or scattered patterns

### Frequency Analysis
- **Dominant Frequency**: The frequency with the highest energy
- **Pitch Estimate**: Estimated fundamental frequency of voice
- **Harmonic Ratio**: Measure of voice quality (higher = more harmonic content)

### Energy Patterns
- **Speech**: Clear peaks above threshold
- **Silence**: Low, consistent levels below threshold
- **Background noise**: Irregular patterns, may be above threshold

## Troubleshooting

### High Background Noise
1. **Increase Energy Threshold** to filter out noise
2. **Check microphone placement** and environment
3. **Consider using noise-canceling microphone**

### Speech Not Detected
1. **Decrease Energy Threshold** to be more sensitive
2. **Check microphone volume** and permissions
3. **Speak closer to microphone**

### False Speech Detection
1. **Increase Energy Threshold** to be less sensitive
2. **Increase Silence Threshold** to require longer silence
3. **Check for background noise sources**

### Poor Voice Quality
1. **Check microphone quality** and positioning
2. **Reduce background noise** in environment
3. **Adjust microphone gain** if available

## Technical Details

### Audio Processing
- **Sample Rate**: 16 kHz
- **Buffer Size**: 1024 samples
- **FFT Size**: 1024 points for frequency analysis
- **Spectrogram**: 512-point windows with 256-point overlap

### Frequency Analysis
- **Window Function**: Hann window for spectral analysis
- **Peak Detection**: Automatic peak finding for pitch estimation
- **Harmonic Analysis**: Ratio of harmonic energy to total energy

### Real-time Updates
- **Plot Updates**: 100ms intervals
- **Statistics Updates**: 100ms intervals
- **Audio Buffer**: 1 second of audio data maintained

## Integration with Voice Chat

The VAD calibration settings directly affect:
- **Wake word detection** sensitivity
- **Speech recognition** accuracy
- **Natural pause detection** in enhanced mode
- **TTS timing** and response speed

Settings are applied immediately and persist for the current session. For permanent changes, the settings are saved to the configuration system.

## Advanced Tips

### For Different Environments
- **Quiet office**: Lower energy threshold, shorter silence threshold
- **Noisy environment**: Higher energy threshold, longer silence threshold
- **Multiple speakers**: Higher energy threshold, dynamic threshold enabled
- **Distance speaking**: Higher energy threshold, longer pause threshold

### For Different Voice Types
- **High-pitched voices**: May need lower energy threshold
- **Low-pitched voices**: May need higher energy threshold
- **Soft speakers**: Lower energy threshold, longer silence threshold
- **Loud speakers**: Higher energy threshold, shorter silence threshold

### Performance Optimization
- **Close other audio applications** during calibration
- **Use wired microphone** for better quality
- **Calibrate in your normal speaking environment**
- **Test with different speaking volumes and distances**
