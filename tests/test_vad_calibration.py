#!/usr/bin/env python3
"""
Test script for VAD Calibration GUI
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_vad_calibration_gui():
    """Test the VAD calibration GUI"""
    print("🧪 Testing VAD Calibration GUI")
    print("=" * 50)
    
    try:
        from voice_chat.ui.vad_calibration_gui import VADCalibrationGUI
        print("✅ VAD Calibration GUI imported successfully")
        
        # Create and run the GUI
        print("🚀 Launching VAD Calibration GUI...")
        app = VADCalibrationGUI()
        app.run()
        
        print("✅ VAD Calibration GUI test completed")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure all dependencies are installed:")
        print("   .venv/bin/pip install matplotlib pyaudio")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_vad_calibration_gui()
    if success:
        print("\n🎉 VAD Calibration GUI test passed!")
        sys.exit(0)
    else:
        print("\n💥 VAD Calibration GUI test failed!")
        sys.exit(1)
