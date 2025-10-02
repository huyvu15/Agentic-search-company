import os
import google.generativeai as genai
from dotenv import load_dotenv
from typing import Optional, Dict, Any
from datetime import datetime

load_dotenv()

class GeminiChatbot:
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        
        genai.configure(api_key=self.api_key)
        
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        
        self.chat_history = []
        self._chat_session = None
    
    def chat(self, message: str, temperature: float = 0.7, max_tokens: int = 500):
        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        
        response = self.model.generate_content(
            message,
            generation_config=generation_config
        )
        
        self.chat_history.append({
            'user': message,
            'assistant': response.text,
            'timestamp': datetime.now()
        })
        
        return response.text
    
    def chat_with_history(self, message: str, temperature: float = 0.7, max_tokens: int = 500):
        try:
            if self._chat_session is None:
                self._chat_session = self.model.start_chat(history=[])
            
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )
            
            response = self._chat_session.send_message(message, generation_config=generation_config)
            
            self.chat_history.append({
                'user': message,
                'assistant': response.text,
                'timestamp': datetime.now()
            })
            
            return response.text
            
        except Exception as e:
            return f"Lỗi khi gọi Gemini API với lịch sử: {e}"
    
    def clear_history(self):
        self.chat_history = []
        self._chat_session = None
    
    def get_history(self):
        return self.chat_history
    
    def get_model_info(self):
        return {
            'model_name': 'gemini-pro',
            'api_key_set': bool(self.api_key),
            'history_count': len(self.chat_history)
        }


def create_chatbot(api_key: Optional[str] = None):
    return GeminiChatbot(api_key)


