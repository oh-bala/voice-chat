import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_MODEL = "gpt-4o-mini"
    
    # Language Configuration
    SUPPORTED_LANGUAGES = {
        "en": {
            "name": "English",
            "code": "en-US",
            "wake_word": "hey assistant",
            "exit_words": ["goodbye", "exit", "quit", "stop"]
        },
        "zh": {
            "name": "中文 (Chinese)",
            "code": "zh-CN",
            "wake_word": "你好助手",
            "exit_words": ["再见", "退出", "停止", "结束"]
        }
    }
    DEFAULT_LANGUAGE = "en"
    
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
    # Prevent ASR from picking up TTS: small delay after TTS ends before listening
    ASR_TTS_COOLDOWN = 0.3  # seconds (fallback if VAD fails)
    
    # Voice Activity Detection (VAD) Configuration
    VAD_ENABLED = True  # Enable VAD for precise TTS timing
    VAD_SILENCE_THRESHOLD = 0.5  # seconds of silence to consider TTS finished
    VAD_TIMEOUT = 10.0  # maximum seconds to wait for silence
    VAD_ENERGY_THRESHOLD = 200  # audio energy threshold for silence detection
    
    # MCP Configuration
    MCP_ENABLED = True  # Enable MCP functionality
    MCP_CONFIG_FILE = "mcp_config.json"  # MCP configuration file path
    MCP_DEFAULT_TIMEOUT = 30  # Default timeout for MCP operations
    MCP_MAX_CONCURRENT_CONNECTIONS = 5  # Maximum concurrent MCP connections
    
    @classmethod
    def get_language_config(cls, language_code: str = None):
        """Get configuration for a specific language"""
        if language_code is None:
            language_code = cls.DEFAULT_LANGUAGE
        return cls.SUPPORTED_LANGUAGES.get(language_code, cls.SUPPORTED_LANGUAGES[cls.DEFAULT_LANGUAGE])
    
    @classmethod
    def get_wake_word(cls, language_code: str = None):
        """Get wake word for a specific language"""
        return cls.get_language_config(language_code)["wake_word"]
    
    @classmethod
    def get_exit_words(cls, language_code: str = None):
        """Get exit words for a specific language"""
        return cls.get_language_config(language_code)["exit_words"]
    
    @classmethod
    def get_speech_language_code(cls, language_code: str = None):
        """Get speech recognition language code for a specific language"""
        return cls.get_language_config(language_code)["code"]
    
    @classmethod
    def validate(cls):
        """Validate that required configuration is present"""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY must be set in environment or .env file")
        if cls.TTS_PROVIDER == 'elevenlabs' and not cls.ELEVENLABS_API_KEY:
            raise ValueError("ELEVENLABS_API_KEY must be set when TTS_PROVIDER is 'elevenlabs'")
        return True
