#!/usr/bin/env python3

import logging
import signal
import sys
from datetime import datetime

from config import Config
from speech_recognition_handler import SpeechRecognitionHandler
from advanced_speech_handler import AdvancedSpeechHandler
from openai_client import OpenAIClient
from text_to_speech import TextToSpeechHandler

class VoiceChatApp:
    def __init__(self):
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('voice_chat.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.running = True
        self.conversation_active = False
        
        # Initialize components
        try:
            print("Initializing Voice Chat Assistant...")
            print("=" * 50)
            
            self.speech_recognizer = SpeechRecognitionHandler()
            self.openai_client = OpenAIClient()
            self.tts_handler = TextToSpeechHandler()
            
            print("All components initialized successfully!")
            print("=" * 50)
            
        except Exception as e:
            logging.error(f"Failed to initialize components: {e}")
            print(f"Error: {e}")
            sys.exit(1)
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        print("\nShutting down Voice Chat Assistant...")
        self.running = False
        self.tts_handler.stop_speaking()
    
    def start(self):
        """Start the voice chat application"""
        try:
            print("Voice Chat Assistant is ready!")
            print(f"Say '{Config.WAKE_WORD}' to start a conversation")
            print("Say any of these words to exit: " + ", ".join(Config.EXIT_WORDS))
            print("Press Ctrl+C to quit the application")
            print("-" * 50)
            
            self.tts_handler.speak("Voice chat assistant is ready. " + 
                                 f"Say {Config.WAKE_WORD} to start a conversation.")
            
            while self.running:
                try:
                    # Listen for wake word
                    if self.speech_recognizer.listen_for_wake_word():
                        self._start_conversation()
                    
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    logging.error(f"Error in main loop: {e}")
                    print(f"An error occurred: {e}")
                    print("Continuing to listen...")
            
        except Exception as e:
            logging.error(f"Fatal error in voice chat app: {e}")
            print(f"Fatal error: {e}")
        finally:
            self._cleanup()
    
    def _start_conversation(self):
        """Start a conversation session"""
        self.conversation_active = True
        
        self.tts_handler.speak("Hello! How can I help you today?")
        
        print("\n" + "=" * 50)
        print("CONVERSATION STARTED")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)
        
        while self.conversation_active and self.running:
            try:
                # Listen for user input
                user_input = self.speech_recognizer.listen_for_speech()
                
                if not user_input:
                    print("No speech detected. Say something or say 'goodbye' to end conversation.")
                    continue
                
                # Check for exit commands
                if self.speech_recognizer.is_exit_command(user_input):
                    self._end_conversation()
                    break
                
                # Check for special commands
                if self._handle_special_commands(user_input):
                    continue
                
                # Get AI response
                print(f"\nYou: {user_input}")
                response = self.openai_client.get_response(user_input)
                
                if response:
                    print(f"Assistant: {response}")
                    self.tts_handler.speak(response)
                else:
                    error_msg = "I'm sorry, I couldn't process that request."
                    print(f"Assistant: {error_msg}")
                    self.tts_handler.speak(error_msg)
                
                print("-" * 30)
                
            except KeyboardInterrupt:
                self._end_conversation()
                break
            except Exception as e:
                logging.error(f"Error in conversation: {e}")
                error_msg = "I encountered an error. Let's continue our conversation."
                print(f"Error: {error_msg}")
                self.tts_handler.speak(error_msg)
    
    def _handle_special_commands(self, user_input):
        """Handle special voice commands"""
        user_input = user_input.lower().strip()
        
        # Reset conversation
        if "reset conversation" in user_input or "start over" in user_input:
            self.openai_client.reset_conversation()
            self.tts_handler.speak("Conversation reset. What would you like to talk about?")
            return True
        
        # Show conversation summary
        if "conversation summary" in user_input or "how many messages" in user_input:
            summary = self.openai_client.get_conversation_summary()
            summary_text = f"We've had {summary['total_exchanges']} exchanges in this conversation."
            print(f"Summary: {summary_text}")
            self.tts_handler.speak(summary_text)
            return True
        
        # Stop speaking
        if "stop talking" in user_input or "be quiet" in user_input:
            self.tts_handler.stop_speaking()
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
        
        return False
    
    def _end_conversation(self):
        """End the current conversation"""
        self.conversation_active = False
        
        goodbye_messages = [
            "Goodbye! Say my wake word when you want to chat again.",
            "See you later! I'll be listening for the wake word.",
            "Take care! Just say my wake word to start another conversation."
        ]
        
        import random
        goodbye_msg = random.choice(goodbye_messages)
        
        print(f"\nAssistant: {goodbye_msg}")
        self.tts_handler.speak(goodbye_msg)
        
        print("=" * 50)
        print("CONVERSATION ENDED")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Show conversation summary
        summary = self.openai_client.get_conversation_summary()
        print(f"Total exchanges: {summary['total_exchanges']}")
        print("=" * 50)
    
    def _cleanup(self):
        """Cleanup resources"""
        print("\nCleaning up...")
        self.tts_handler.stop_speaking()
        print("Voice Chat Assistant stopped.")

def main():
    """Main entry point"""
    try:
        app = VoiceChatApp()
        app.start()
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
