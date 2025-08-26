import openai
import logging
from config import Config

class OpenAIClient:
    def __init__(self):
        # Validate configuration
        Config.validate()
        
        # Initialize OpenAI client
        self.client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
        
        # Conversation history
        self.conversation_history = [
            {
                "role": "system", 
                "content": "You are a helpful voice assistant. Provide clear, concise responses suitable for voice interaction. Keep responses relatively short and conversational."
            }
        ]
    
    def get_response(self, user_message):
        """
        Get a response from OpenAI for the given user message
        
        Args:
            user_message (str): The user's message
            
        Returns:
            str: The AI's response or None if error occurred
        """
        try:
            # Add user message to conversation history
            self.conversation_history.append({
                "role": "user",
                "content": user_message
            })
            
            # Get response from OpenAI
            response = self.client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=self.conversation_history,
                max_tokens=300,  # Limit response length for voice
                temperature=0.7
            )
            
            # Extract the assistant's response
            assistant_message = response.choices[0].message.content
            
            # Add assistant's response to conversation history
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })
            
            # Keep conversation history manageable (last 10 messages)
            if len(self.conversation_history) > 11:  # 1 system + 10 conversation messages
                self.conversation_history = [self.conversation_history[0]] + self.conversation_history[-10:]
            
            return assistant_message
            
        except openai.RateLimitError:
            logging.error("OpenAI API rate limit exceeded")
            return "I'm sorry, I've reached my rate limit. Please try again later."
        except openai.AuthenticationError:
            logging.error("OpenAI API authentication failed")
            return "I'm sorry, there's an authentication issue. Please check your API key."
        except Exception as e:
            logging.error(f"Error getting OpenAI response: {e}")
            return "I'm sorry, I encountered an error. Please try again."
    
    def reset_conversation(self):
        """Reset the conversation history"""
        self.conversation_history = [
            {
                "role": "system", 
                "content": "You are a helpful voice assistant. Provide clear, concise responses suitable for voice interaction. Keep responses relatively short and conversational."
            }
        ]
        print("Conversation reset!")
    
    def get_conversation_summary(self):
        """Get a summary of the current conversation"""
        user_messages = [msg for msg in self.conversation_history if msg["role"] == "user"]
        assistant_messages = [msg for msg in self.conversation_history if msg["role"] == "assistant"]
        
        return {
            "total_exchanges": min(len(user_messages), len(assistant_messages)),
            "user_messages": len(user_messages),
            "assistant_messages": len(assistant_messages)
        }
