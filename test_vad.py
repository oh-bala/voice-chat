#!/usr/bin/env python3
"""
Test script for Voice Activity Detection (VAD) functionality
"""

import sys
import time
from voice_chat.speech.text_to_speech import TextToSpeechHandler
from config import Config

def test_vad():
    """Test VAD functionality"""
    print("🧪 Testing Voice Activity Detection (VAD)")
    print("=" * 50)
    
    # Check configuration
    print(f"VAD Enabled: {Config.VAD_ENABLED}")
    print(f"VAD Silence Threshold: {Config.VAD_SILENCE_THRESHOLD}s")
    print(f"VAD Timeout: {Config.VAD_TIMEOUT}s")
    print(f"VAD Energy Threshold: {Config.VAD_ENERGY_THRESHOLD}")
    print(f"Fallback Cooldown: {Config.ASR_TTS_COOLDOWN}s")
    print()
    
    # Initialize TTS handler
    try:
        tts = TextToSpeechHandler()
        print("✅ TTS Handler initialized successfully")
        
        if tts.microphone and tts.recognizer:
            print("✅ VAD components available")
        else:
            print("⚠️ VAD components not available, will use fallback")
        
    except Exception as e:
        print(f"❌ Failed to initialize TTS Handler: {e}")
        return False
    
    # Test short TTS with VAD
    print("\n🔊 Testing TTS with VAD...")
    print("💡 The system will speak a short message and wait for silence")
    print("💡 You should see VAD messages in the console")
    
    try:
        test_text = "Hello, this is a test of voice activity detection. The system should wait for silence after this message."
        print(f"📝 Speaking: '{test_text}'")
        
        start_time = time.time()
        tts.speak(test_text, blocking=True)
        end_time = time.time()
        
        duration = end_time - start_time
        print(f"⏱️ Total duration: {duration:.2f}s")
        print("✅ VAD test completed successfully")
        
    except Exception as e:
        print(f"❌ VAD test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_vad()
    if success:
        print("\n🎉 VAD test passed!")
        sys.exit(0)
    else:
        print("\n💥 VAD test failed!")
        sys.exit(1)
