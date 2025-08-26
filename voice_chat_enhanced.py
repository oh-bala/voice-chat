#!/usr/bin/env python3

import logging
import signal
import sys
from datetime import datetime

from config import Config
from voice_chat.speech.advanced_speech_handler import AdvancedSpeechHandler
from voice_chat.ai.openai_client import OpenAIClient
from voice_chat.speech.text_to_speech import TextToSpeechHandler

class EnhancedVoiceChatApp:
    def __init__(self):
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('voice_chat_enhanced.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.running = True
        self.conversation_active = False
        
        # Initialize components
        try:
            print("🚀 Initializing Enhanced Voice Chat Assistant...")
            print("=" * 60)
            
            # Use advanced speech handler with pause detection
            print("🎤 Setting up advanced speech recognition...")
            self.speech_recognizer = AdvancedSpeechHandler()
            
            print("🤖 Connecting to OpenAI...")
            self.openai_client = OpenAIClient()
            
            print("🗣️  Initializing text-to-speech...")
            self.tts_handler = TextToSpeechHandler()
            
            print("✅ All components initialized successfully!")
            print("=" * 60)
            
        except Exception as e:
            logging.error(f"Failed to initialize components: {e}")
            print(f"❌ Error: {e}")
            sys.exit(1)
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        print("\n👋 Shutting down Enhanced Voice Chat Assistant...")
        self.running = False
        self.tts_handler.stop_speaking()
    
    def start(self):
        """Start the enhanced voice chat application"""
        try:
            print("🎉 Enhanced Voice Chat Assistant is ready!")
            print(f"🔊 Wake word: '{Config.WAKE_WORD}'")
            print(f"🚪 Exit words: {', '.join(Config.EXIT_WORDS)}")
            print("⚙️  Features: Natural pause detection, voice activity detection")
            print("💡 Tip: Speak naturally - I'll detect when you're finished speaking")
            print("🔧 Press Ctrl+C to quit the application")
            print("-" * 60)
            
            # Offer microphone test
            print("🎤 Would you like to test your microphone first? (Recommended)")
            print("   Say 'test microphone' or just start with the wake word")
            
            self.tts_handler.speak("Enhanced voice chat assistant is ready! " + 
                                 f"Say {Config.WAKE_WORD} to start, or say test microphone to check your audio levels.")
            
            while self.running:
                try:
                    # Listen for wake word with advanced detection
                    if self.speech_recognizer.listen_for_wake_word_advanced():
                        self._start_conversation()
                    
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    logging.error(f"Error in main loop: {e}")
                    print(f"⚠️  An error occurred: {e}")
                    print("🔄 Continuing to listen...")
            
        except Exception as e:
            logging.error(f"Fatal error in enhanced voice chat app: {e}")
            print(f"💥 Fatal error: {e}")
        finally:
            self._cleanup()
    
    def _start_conversation(self):
        """Start a conversation session with enhanced features"""
        self.conversation_active = True
        
        self.tts_handler.speak("Hello! I'm ready to chat. Speak naturally and I'll detect when you're finished.")
        
        print("\n" + "🎬 " + "=" * 58)
        print("🗣️  ENHANCED CONVERSATION STARTED")
        print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("💡 Features: Natural pause detection, real-time voice activity")
        print("=" * 60)
        
        while self.conversation_active and self.running:
            try:
                # Listen for user input with pause detection
                user_input = self.speech_recognizer.listen_with_pause_detection()
                
                if not user_input:
                    print("🤔 No speech detected. Try speaking a bit louder or closer to the microphone.")
                    print("💬 Say something or say 'goodbye' to end the conversation.")
                    continue
                
                # Check for exit commands
                if self.speech_recognizer.is_exit_command(user_input):
                    self._end_conversation()
                    break
                
                # Check for special commands
                if self._handle_special_commands(user_input):
                    continue
                
                # Get AI response
                print(f"\n👤 You: {user_input}")
                
                # Show thinking indicator
                print("🤖 Assistant: Thinking...")
                response = self.openai_client.get_response_sync(user_input)
                
                if response:
                    # Clear thinking indicator and show response
                    print(f"\r🤖 Assistant: {response}")
                    self.tts_handler.speak(response)
                else:
                    error_msg = "I'm sorry, I couldn't process that request. Could you try rephrasing?"
                    print(f"\r🤖 Assistant: {error_msg}")
                    self.tts_handler.speak(error_msg)
                
                print("-" * 40)
                
            except KeyboardInterrupt:
                self._end_conversation()
                break
            except Exception as e:
                logging.error(f"Error in conversation: {e}")
                error_msg = "I encountered an error. Let's continue our conversation."
                print(f"⚠️  Error: {error_msg}")
                self.tts_handler.speak(error_msg)
    
    def _handle_special_commands(self, user_input):
        """Handle special voice commands with enhanced features"""
        user_input = user_input.lower().strip()
        
        # Microphone test
        if "test microphone" in user_input:
            self.speech_recognizer.get_audio_level_indicator(5)
            self.tts_handler.speak("Microphone test completed. How did the levels look?")
            return True
        
        # Sensitivity adjustment
        if "low sensitivity" in user_input or "less sensitive" in user_input:
            self.speech_recognizer.adjust_sensitivity("low")
            self.tts_handler.speak("Speech sensitivity set to low. I'll be less responsive to background noise.")
            return True
        
        if "high sensitivity" in user_input or "more sensitive" in user_input:
            self.speech_recognizer.adjust_sensitivity("high")
            self.tts_handler.speak("Speech sensitivity set to high. I'll pick up quieter speech.")
            return True
        
        if "normal sensitivity" in user_input or "medium sensitivity" in user_input:
            self.speech_recognizer.adjust_sensitivity("medium")
            self.tts_handler.speak("Speech sensitivity set to normal.")
            return True
        
        # Reset conversation
        if "reset conversation" in user_input or "start over" in user_input:
            self.openai_client.reset_conversation()
            self.tts_handler.speak("Conversation reset. What would you like to talk about?")
            return True
        
        # Show conversation summary
        if "conversation summary" in user_input or "how many messages" in user_input:
            summary = self.openai_client.get_conversation_summary()
            summary_text = f"We've had {summary['total_exchanges']} exchanges in this conversation."
            print(f"📊 Summary: {summary_text}")
            self.tts_handler.speak(summary_text)
            return True
        
        # Stop speaking
        if "stop talking" in user_input or "be quiet" in user_input:
            self.tts_handler.stop_speaking()
            print("🤫 Stopping speech...")
            return True
        
        # Voice settings
        if "speak slower" in user_input:
            new_rate = max(100, Config.TTS_RATE - 50)
            self.tts_handler.set_rate(new_rate)
            Config.TTS_RATE = new_rate
            self.tts_handler.speak("I'll speak slower now.")
            return True
        
        if "speak faster" in user_input:
            new_rate = min(300, Config.TTS_RATE + 50)
            self.tts_handler.set_rate(new_rate)
            Config.TTS_RATE = new_rate
            self.tts_handler.speak("I'll speak faster now.")
            return True
        
        # Help command
        if "help" in user_input or "what can you do" in user_input:
            help_text = ("I can have natural conversations with you! "
                        "Special commands include: test microphone, adjust sensitivity, "
                        "speak faster or slower, reset conversation, conversation summary, "
                        "and help. Just speak naturally - I'll detect when you're done!")
            print(f"💬 {help_text}")
            self.tts_handler.speak(help_text)
            return True
        
        return False
    
    def _end_conversation(self):
        """End the current conversation with enhanced feedback"""
        self.conversation_active = False
        
        goodbye_messages = [
            "Goodbye! It was great chatting with you. Say the wake word anytime to talk again!",
            "See you later! I'll be listening for the wake word with my enhanced detection.",
            "Take care! Thanks for the conversation. Just say the wake word when you're ready to chat again.",
            "Farewell! I enjoyed our natural conversation. The wake word will bring me back anytime!"
        ]
        
        import random
        goodbye_msg = random.choice(goodbye_messages)
        
        print(f"\n🤖 Assistant: {goodbye_msg}")
        self.tts_handler.speak(goodbye_msg)
        
        print("🎬 " + "=" * 58)
        print("👋 ENHANCED CONVERSATION ENDED")
        print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Show detailed conversation summary
        summary = self.openai_client.get_conversation_summary()
        print(f"📊 Total exchanges: {summary['total_exchanges']}")
        print(f"💬 User messages: {summary['user_messages']}")
        print(f"🤖 Assistant responses: {summary['assistant_messages']}")
        print("=" * 60)
    
    def _cleanup(self):
        """Cleanup resources"""
        print("\n🧹 Cleaning up...")
        self.tts_handler.stop_speaking()
        print("✅ Enhanced Voice Chat Assistant stopped.")

def main():
    """Main entry point"""
    try:
        app = EnhancedVoiceChatApp()
        app.start()
    except KeyboardInterrupt:
        print("\n👋 Exiting...")
    except Exception as e:
        print(f"💥 Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
