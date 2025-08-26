import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_MODEL = "gpt-4o-mini"
    
    # Speech Recognition Configuration
    SPEECH_TIMEOUT = 5  # seconds to wait for speech
    SPEECH_PHRASE_TIMEOUT = 3  # seconds to wait for phrase completion
    
    # Enhanced Speech Detection Configuration
    PAUSE_THRESHOLD = 0.8  # seconds of silence to consider as natural pause
    MAX_PAUSE_THRESHOLD = 2.0  # maximum pause before stopping
    MIN_SPEECH_DURATION = 0.3  # minimum speech duration to consider valid
    ENERGY_THRESHOLD_MULTIPLIER = 1.0  # multiplier for dynamic energy threshold
    
    # Text-to-Speech Configuration
    TTS_RATE = 200  # words per minute
    TTS_VOLUME = 0.9  # volume level (0.0 to 1.0)
    TTS_PROVIDER = os.getenv('TTS_PROVIDER', 'pyttsx3')  # 'pyttsx3' or 'elevenlabs'
    # ElevenLabs Configuration
    ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
    ELEVENLABS_MODEL_ID = os.getenv('ELEVENLABS_MODEL_ID', 'eleven_multilingual_v2')
    ELEVENLABS_VOICE_ID = os.getenv('ELEVENLABS_VOICE_ID')  # Optional default voice id
    
    # Application Configuration
    WAKE_WORD = "hey assistant"  # wake word to activate voice chat
    EXIT_WORDS = ["goodbye", "exit", "quit", "stop"]
    
    # MCP Configuration
    MCP_ENABLED = True  # Enable MCP functionality
    MCP_CONFIG_FILE = "mcp_config.json"  # MCP configuration file path
    MCP_DEFAULT_TIMEOUT = 30  # Default timeout for MCP operations
    MCP_MAX_CONCURRENT_CONNECTIONS = 5  # Maximum concurrent MCP connections
    
    @classmethod
    def validate(cls):
        """Validate that required configuration is present"""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY must be set in environment or .env file")
        if cls.TTS_PROVIDER == 'elevenlabs' and not cls.ELEVENLABS_API_KEY:
            raise ValueError("ELEVENLABS_API_KEY must be set when TTS_PROVIDER is 'elevenlabs'")
        return True
