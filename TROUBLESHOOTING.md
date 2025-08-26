# Troubleshooting Guide

## Audio Energy Calculation Errors

### Issue: `len() of unsized object` Error
**Symptoms:** 
- Error message: `ERROR:root:Error calculating audio energy: len() of unsized object`
- App continues to listen but may not detect speech properly

**Cause:** 
- The audio data format from the microphone isn't compatible with the numpy array conversion
- Different audio drivers or microphone types may return different data formats

**Solution:**
✅ **Fixed in v2.1**: The enhanced speech handler now includes robust audio data handling with multiple fallback methods.

The system now:
1. Tries to get samples using `get_array_of_samples()`
2. Falls back to `get_raw_data()` and converts from raw bytes
3. Has a final fallback that returns a safe default energy value
4. If chunked detection fails, automatically switches to simpler pause detection

### Issue: Enhanced Mode Not Working
**Symptoms:**
- Enhanced mode checkbox is checked but speech detection doesn't seem improved
- Falls back to basic timeout-based detection

**Solutions:**
1. **Check Microphone Permissions**: Ensure the app has microphone access
2. **Test Microphone**: Use the "Test Microphone" button in Enhanced mode
3. **Adjust Sensitivity**: Try different sensitivity levels (Low/Medium/High)
4. **Check Background Noise**: High background noise can interfere with detection

### Issue: No Speech Detection
**Symptoms:**
- Consistently shows "No speech detected within timeout period"
- Microphone test shows no audio levels

**Solutions:**
1. **Microphone Selection**: 
   ```bash
   # Check available microphones
   python -c "import speech_recognition as sr; print([m.name for m in sr.Microphone.list_microphone_names()])"
   ```

2. **Audio Permissions**: 
   - Go to System Preferences → Security & Privacy → Privacy → Microphone
   - Ensure Terminal/Python has microphone access

3. **Audio Levels**:
   - Check System Preferences → Sound → Input
   - Ensure input volume is adequate
   - Test microphone in other apps

### Issue: Speech Recognition Accuracy
**Symptoms:**
- Speech is detected but transcription is poor
- Frequent "Could not understand the speech" messages

**Solutions:**
1. **Speak Clearly**: Speak slowly and clearly
2. **Reduce Background Noise**: Use in a quiet environment
3. **Microphone Distance**: Speak closer to the microphone
4. **Internet Connection**: Google Speech Recognition requires internet

## Performance Issues

### Issue: Slow Response Time
**Symptoms:**
- Long delays between speech and recognition
- "Processing speech..." takes a long time

**Solutions:**
1. **Internet Speed**: Check your internet connection
2. **Switch to Basic Mode**: Use basic mode if enhanced mode is too slow
3. **Reduce Audio Quality**: Lower microphone sample rate in system settings

### Issue: High CPU Usage
**Symptoms:**
- Fan spinning up during use
- System becomes sluggish

**Solutions:**
1. **Use Basic Mode**: Enhanced mode requires more CPU for real-time processing
2. **Close Other Audio Apps**: Stop other apps using the microphone
3. **Reduce Sensitivity**: Lower sensitivity reduces processing overhead

## API and Configuration Issues

### Issue: OpenAI API Errors
**Symptoms:**
- "Could not request results" errors
- Authentication failures

**Solutions:**
1. **Check API Key**: Ensure `.env` file has correct `OPENAI_API_KEY`
2. **API Limits**: Check if you've exceeded API rate limits
3. **Internet Connection**: Ensure stable internet connection

### Issue: Import Errors
**Symptoms:**
- `ModuleNotFoundError` for required packages

**Solutions:**
1. **Install Dependencies**: `pip install -r requirements.txt`
2. **Virtual Environment**: Ensure you're in the correct virtual environment
3. **Python Version**: Ensure Python 3.8+ is being used

## Mode Switching

### When to Use Enhanced Mode
✅ **Use Enhanced Mode when:**
- You want natural conversation flow
- You speak in longer sentences
- You pause naturally between thoughts
- You want real-time feedback

### When to Use Basic Mode  
✅ **Use Basic Mode when:**
- Enhanced mode is having issues
- You prefer predictable timeout behavior
- You're in a very noisy environment
- You want maximum compatibility

## Getting Help

If you continue to experience issues:

1. **Check Logs**: Look at the console output for specific error messages
2. **Try Different Modes**: Switch between Enhanced and Basic modes
3. **Test Components**: Use the microphone test feature
4. **Restart**: Close and restart the application
5. **System Restart**: Sometimes audio drivers need a system restart

## Debug Mode

To enable detailed logging, modify the logging level in any of the main files:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

This will show much more detailed information about what's happening during speech recognition.
