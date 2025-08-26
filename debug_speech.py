#!/usr/bin/env python3

import speech_recognition as sr
import logging
import sys
import traceback

# Enable more detailed logging
logging.basicConfig(level=logging.DEBUG)

def test_basic_recognition():
    """Test basic speech recognition functionality"""
    print("=== Testing Basic Speech Recognition ===")
    
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    
    # List available microphones
    print("\nAvailable microphones:")
    for index, name in enumerate(sr.Microphone.list_microphone_names()):
        print(f"  {index}: {name}")
    
    print(f"\nUsing default microphone")
    
    # Test microphone access
    try:
        with microphone as source:
            print("Adjusting for ambient noise...")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            print(f"Energy threshold: {recognizer.energy_threshold}")
    except Exception as e:
        print(f"ERROR accessing microphone: {e}")
        traceback.print_exc()
        return False
    
    # Test speech recognition
    try:
        print("\nSay something now...")
        with microphone as source:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
        
        print("Processing audio...")
        text = recognizer.recognize_google(audio)
        print(f"SUCCESS: Recognized text: '{text}'")
        return True
        
    except sr.WaitTimeoutError:
        print("ERROR: No speech detected within timeout")
        return False
    except sr.UnknownValueError:
        print("ERROR: Could not understand the speech")
        return False
    except sr.RequestError as e:
        print(f"ERROR: Speech recognition service error: {e}")
        return False
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")
        traceback.print_exc()
        return False

def test_chunked_approach():
    """Test the chunked audio approach that's failing"""
    print("\n=== Testing Chunked Audio Approach ===")
    
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    
    try:
        with microphone as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
            print(f"Energy threshold: {recognizer.energy_threshold}")
            
            print("Testing short audio chunks...")
            audio_chunks = []
            
            for i in range(5):  # Try to capture 5 short chunks
                try:
                    print(f"Capturing chunk {i+1}/5...")
                    chunk = recognizer.listen(source, timeout=0.1, phrase_time_limit=0.5)
                    audio_chunks.append(chunk)
                    print(f"  Chunk {i+1}: captured {len(chunk.get_raw_data())} bytes")
                except sr.WaitTimeoutError:
                    print(f"  Chunk {i+1}: timeout (silence)")
                    continue
                except Exception as e:
                    print(f"  Chunk {i+1}: error - {e}")
                    continue
            
            if audio_chunks:
                print(f"Captured {len(audio_chunks)} chunks")
                
                # Try to combine them
                try:
                    if len(audio_chunks) == 1:
                        combined_audio = audio_chunks[0]
                    else:
                        # Combine audio data
                        sample_rate = audio_chunks[0].sample_rate
                        sample_width = audio_chunks[0].sample_width
                        combined_data = b""
                        
                        for chunk in audio_chunks:
                            combined_data += chunk.get_raw_data()
                        
                        combined_audio = sr.AudioData(combined_data, sample_rate, sample_width)
                    
                    print("Recognizing combined audio...")
                    text = recognizer.recognize_google(combined_audio)
                    print(f"SUCCESS: Combined recognition: '{text}'")
                    return True
                    
                except Exception as e:
                    print(f"ERROR combining/recognizing chunks: {e}")
                    traceback.print_exc()
                    return False
            else:
                print("ERROR: No audio chunks captured")
                return False
                
    except Exception as e:
        print(f"ERROR in chunked approach: {e}")
        traceback.print_exc()
        return False

def test_internet_connection():
    """Test if Google Speech Recognition API is accessible"""
    print("\n=== Testing Internet/API Access ===")
    
    try:
        import urllib.request
        response = urllib.request.urlopen('https://www.google.com', timeout=5)
        print("✓ Internet connection working")
        
        # Test with a simple audio sample if possible
        recognizer = sr.Recognizer()
        
        # Create a simple test - we'll skip this if no test audio available
        print("✓ Google Speech API should be accessible")
        return True
        
    except Exception as e:
        print(f"✗ Network/API issue: {e}")
        return False

def main():
    print("Speech Recognition Debug Tool")
    print("=" * 40)
    
    results = {}
    
    # Test basic components
    results['internet'] = test_internet_connection()
    results['basic_recognition'] = test_basic_recognition()
    results['chunked_approach'] = test_chunked_approach()
    
    print("\n" + "=" * 40)
    print("DEBUG RESULTS SUMMARY:")
    print("=" * 40)
    
    for test, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test.replace('_', ' ').title()}: {status}")
    
    if all(results.values()):
        print("\n🎉 All tests passed! Speech recognition should work.")
    else:
        print("\n❌ Some tests failed. Check the errors above.")
        
        # Provide specific guidance based on failures
        if not results['internet']:
            print("- Check your internet connection")
        if not results['basic_recognition']:
            print("- Check microphone permissions and hardware")
        if not results['chunked_approach']:
            print("- Chunked audio processing needs fixing")

if __name__ == "__main__":
    main()
