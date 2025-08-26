#!/usr/bin/env python3

from text_to_speech import TextToSpeechHandler
import time

def test_tts():
    """Test TTS functionality"""
    print("Testing Text-to-Speech...")
    
    tts = TextToSpeechHandler()
    
    # Test basic speech
    test_messages = [
        "Hello! This is a test of the text-to-speech system.",
        "Can you hear me clearly?",
        "Testing async speech functionality.",
        "Goodbye!"
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\nTest {i}: '{message}'")
        
        # Test async speech (non-blocking)
        success = tts.speak(message, blocking=False)
        if success:
            print("✅ TTS started successfully (async)")
        else:
            print("❌ TTS failed to start")
        
        # Wait for speech to complete
        time.sleep(3)
        
        # Check if still speaking
        if tts.is_currently_speaking():
            print("⏳ Still speaking, waiting...")
            time.sleep(2)
    
    print("\nTesting blocking speech...")
    success = tts.speak("This is a blocking speech test.", blocking=True)
    if success:
        print("✅ Blocking TTS completed successfully")
    else:
        print("❌ Blocking TTS failed")
    
    print("\nTesting voice settings...")
    available_voices = tts.get_available_voices()
    print(f"Available voices: {len(available_voices)}")
    for voice in available_voices[:3]:  # Show first 3
        print(f"  - {voice['name']} (ID: {voice['id'][:30]}...)")
    
    print("\nTTS test completed!")

if __name__ == "__main__":
    test_tts()
