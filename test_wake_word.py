#!/usr/bin/env python3

from advanced_speech_handler import AdvancedSpeechHandler
from speech_recognition_handler import SpeechRecognitionHandler
from config import Config

def test_wake_word_basic():
    """Test basic wake word detection"""
    print("=== Testing Basic Wake Word Detection ===")
    print(f"Wake word: '{Config.WAKE_WORD}'")
    print("Say the wake word to test...")
    
    handler = SpeechRecognitionHandler()
    
    # Listen for wake word
    try:
        text = handler.listen_for_speech(timeout=10, phrase_time_limit=8)
        if text and Config.WAKE_WORD.lower() in text.lower():
            print("✅ WAKE WORD DETECTED!")
            return True
        elif text:
            print(f"❌ Heard '{text}' but that's not the wake word")
            return False
        else:
            print("❌ No speech detected")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_wake_word_enhanced():
    """Test enhanced wake word detection"""
    print("\n=== Testing Enhanced Wake Word Detection ===")
    print(f"Wake word: '{Config.WAKE_WORD}'")
    print("Say the wake word to test...")
    
    handler = AdvancedSpeechHandler()
    
    # Listen for wake word
    try:
        text = handler.listen_with_pause_detection(initial_timeout=10, max_silence_duration=5)
        if text and Config.WAKE_WORD.lower() in text.lower():
            print("✅ WAKE WORD DETECTED!")
            return True
        elif text:
            print(f"❌ Heard '{text}' but that's not the wake word")
            return False
        else:
            print("❌ No speech detected")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_conversation():
    """Test a simple conversation"""
    print("\n=== Testing Conversation ===")
    print("Say something for a conversation test...")
    
    handler = AdvancedSpeechHandler()
    
    try:
        text = handler.listen_with_pause_detection()
        if text:
            print(f"✅ Conversation input detected: '{text}'")
            return True
        else:
            print("❌ No conversation input detected")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("Wake Word Detection Test")
    print("=" * 40)
    
    results = {}
    
    # Test both modes
    results['basic_wake_word'] = test_wake_word_basic()
    results['enhanced_wake_word'] = test_wake_word_enhanced()
    results['conversation'] = test_conversation()
    
    print("\n" + "=" * 40)
    print("TEST RESULTS:")
    print("=" * 40)
    
    for test, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test.replace('_', ' ').title()}: {status}")
    
    if all(results.values()):
        print("\n🎉 All tests passed! Voice chat should work!")
    else:
        print("\n⚠️  Some tests failed, but basic functionality should work.")

if __name__ == "__main__":
    main()
