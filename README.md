# Voice Chat Assistant

A Python-based voice chat application for macOS that provides OpenAI-powered conversational AI with speech recognition and text-to-speech capabilities, similar to OpenAI's voice chat application.

## Features

### Core Features
- **Voice Activation**: Wake word detection to start conversations
- **Speech Recognition**: Convert speech to text using Google Speech Recognition
- **AI Conversations**: Powered by OpenAI's GPT models for intelligent responses
- **Text-to-Speech**: Natural voice responses using macOS system voices
- **Multiple Interfaces**: Command-line, enhanced CLI, and GUI options
- **Conversation Management**: Reset, summarize, and manage conversation history
- **Voice Controls**: Speed adjustment and sensitivity controls
- **Logging**: Comprehensive error logging and conversation tracking

### 🆕 Enhanced Features
- **Natural Pause Detection**: Automatically detects when you finish speaking instead of using fixed timeouts
- **Voice Activity Detection (VAD)**: Real-time detection of speech vs. silence
- **Dynamic Speech Sensitivity**: Adjustable sensitivity for different environments
- **Audio Level Monitoring**: Visual microphone testing and level indicators
- **Smart Wake Word Detection**: More responsive and accurate wake word recognition
- **Real-time Audio Processing**: Processes speech in chunks for better responsiveness

## Requirements

- macOS (tested on macOS 10.15+)
- Python 3.8 or higher
- OpenAI API key
- Microphone access
- Internet connection

## Installation

1. **Clone or download the project files to your desired directory**

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install system dependencies (if needed):**
   
   For PyAudio (speech recognition), you might need:
   ```bash
   brew install portaudio
   pip install pyaudio
   ```

4. **Set up your OpenAI API key:**
   
   Create a `.env` file in the project directory:
   ```bash
   cp .env.example .env
   ```
   
   Edit the `.env` file and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_actual_api_key_here
   ```

5. **Grant microphone permissions:**
   
   When you first run the application, macOS will request microphone access. Make sure to grant permission.

## Usage

### Command Line Interface

Run the main application:
```bash
python voice_chat_app.py
```

**Basic Usage:**
1. Start the application
2. Wait for the "Voice chat assistant is ready" message
3. Say "hey assistant" to wake up the assistant
4. Have a conversation
5. Say "goodbye", "exit", "quit", or "stop" to end the conversation
6. Press Ctrl+C to quit the application

**Voice Commands:**
- `"hey assistant"` - Wake word to start conversation
- `"goodbye"`, `"exit"`, `"quit"`, `"stop"` - End conversation
- `"reset conversation"` or `"start over"` - Reset conversation history
- `"conversation summary"` - Get conversation statistics
- `"speak slower"` - Decrease speech rate
- `"speak faster"` - Increase speech rate
- `"stop talking"` or `"be quiet"` - Stop current speech

### 🚀 Enhanced Voice Chat (Recommended)

Run the enhanced version with natural pause detection:
```bash
python voice_chat_enhanced.py
```

**Enhanced Features:**
- **Natural Conversation Flow**: Speak normally - the app detects when you're done talking
- **Real-time Voice Activity**: Visual feedback showing speech detection
- **Microphone Testing**: Built-in audio level testing with `"test microphone"`
- **Sensitivity Control**: Adjust with `"high sensitivity"`, `"low sensitivity"`, or `"normal sensitivity"`
- **Smart Wake Word Detection**: More responsive and accurate
- **Enhanced Voice Commands**:
  - `"test microphone"` - Test your microphone with visual levels
  - `"high/low/normal sensitivity"` - Adjust speech detection sensitivity
  - `"help"` - Get list of available commands
  - All standard commands from the basic version

### GUI Interface

Run the GUI version:
```bash
python voice_chat_gui.py
```

**GUI Features:**
- Visual status indicators for app state, conversation, and listening
- Real-time conversation display with timestamps
- Control buttons for start/stop, reset, and clear
- Settings display for wake word and exit commands

## Configuration

Edit `config.py` to customize:

```python
class Config:
    # OpenAI Configuration
    OPENAI_MODEL = "gpt-4o-mini"  # or "gpt-3.5-turbo"
    
    # Speech Recognition Configuration
    SPEECH_TIMEOUT = 5  # seconds to wait for speech
    SPEECH_PHRASE_TIMEOUT = 3  # seconds to wait for phrase completion
    
    # Text-to-Speech Configuration
    TTS_RATE = 200  # words per minute
    TTS_VOLUME = 0.9  # volume level (0.0 to 1.0)
    
    # Application Configuration
    WAKE_WORD = "hey assistant"  # change wake word
    EXIT_WORDS = ["goodbye", "exit", "quit", "stop"]
```

## File Structure

```
voice-chat/
├── voice_chat_app.py           # Main CLI application
├── voice_chat_enhanced.py      # 🆕 Enhanced CLI with pause detection
├── voice_chat_gui.py           # GUI application
├── config.py                   # Configuration settings
├── speech_recognition_handler.py  # Basic speech-to-text functionality
├── advanced_speech_handler.py  # 🆕 Enhanced speech with VAD and pause detection
├── openai_client.py            # OpenAI API integration
├── text_to_speech.py           # Text-to-speech functionality
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── .env                       # Your API keys (create this)
├── setup.sh                   # Automated setup script
├── voice_chat.log             # Application log file
├── voice_chat_enhanced.log     # Enhanced app log file
└── README.md                  # This file
```

## Troubleshooting

### Common Issues

**"No module named 'speech_recognition'"**
- Install dependencies: `pip install -r requirements.txt`

**"OPENAI_API_KEY must be set"**
- Create `.env` file with your OpenAI API key

**Microphone not working**
- Grant microphone permissions in System Preferences > Security & Privacy > Privacy > Microphone
- Check if another application is using the microphone

**PyAudio installation fails**
- Install PortAudio: `brew install portaudio`
- Try: `pip install pyaudio --global-option="build_ext" --global-option="-I/usr/local/include" --global-option="-L/usr/local/lib"`

**Speech recognition not working**
- Check internet connection (Google Speech Recognition requires internet)
- Speak clearly and close to the microphone
- Check microphone levels in System Preferences

**TTS not working**
- macOS system voices should work by default
- Try different voices in the code or system preferences

### Debug Mode

To enable more verbose logging, modify the logging level in the main application files:
```python
logging.basicConfig(level=logging.DEBUG)
```

## API Costs

This application uses OpenAI's API, which charges per token. Costs are typically:
- GPT-4: ~$0.03-0.06 per 1K tokens
- GPT-3.5-turbo: ~$0.001-0.002 per 1K tokens

A typical conversation exchange might use 100-500 tokens.

## Privacy and Security

- Conversations are sent to OpenAI's servers for processing
- Speech recognition uses Google's service
- No conversation data is stored locally except in logs
- API keys are stored in local `.env` file

## License

This project is open source. Feel free to modify and distribute.

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve the application.

## Acknowledgments

- OpenAI for the GPT API
- Google for Speech Recognition service
- Python community for excellent libraries
