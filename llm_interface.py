"""
Llama 3 8B Model Interface using Ollama
Supports multiple models for medical chatbot
"""

import requests
import time
import logging
from typing import Tuple, Dict, Any, Optional

logger = logging.getLogger(__name__)


class LlamaInterface:
    """
    Interface for Llama model via Ollama with multi-model support
    """
    
    # Available models for medical chatbot
    AVAILABLE_MODELS = {
        "gemma3:4b": {
            "description": "Lightweight, fast response",
            "size": "4B parameters",
            "recommended": "Daily conversations, quick responses"
        },
        "llama3:8b": {
            "description": "Balanced performance",
            "size": "8B parameters", 
            "recommended": "General medical inquiries"
        },
        "deepseek-r1:7b": {
            "description": "Strong reasoning for medical tasks",
            "size": "7B parameters",
            "recommended": "Complex medical reasoning"
        }
    }
    
    def __init__(self, model_path: str = None, use_api: bool = False, 
                 api_url: str = None, model_name: str = None, **kwargs):
        self.ollama_url = "http://localhost:11434/api/generate"
        
        if model_name and model_name in self.AVAILABLE_MODELS:
            self.model_name = model_name
        else:
            self.model_name = "gemma3:4b"
        
        self.default_max_tokens = 256
        self.default_temperature = 0.7
        self.default_top_p = 0.9
        
        logger.info(f"Using Ollama with model: {self.model_name}")
    
    def switch_model(self, model_name: str) -> bool:
        """Switch to a different model"""
        if model_name in self.AVAILABLE_MODELS:
            self.model_name = model_name
            logger.info(f"Switched to model: {model_name}")
            return True
        else:
            logger.error(f"Model {model_name} not available")
            return False
    
    def get_current_model(self) -> str:
        """Get current model name"""
        return self.model_name
    
    def get_available_models(self) -> Dict[str, Dict[str, str]]:
        """Get all available models"""
        return self.AVAILABLE_MODELS
    
    def generate(self, prompt: str, max_tokens: int = None, 
                 temperature: float = None, **kwargs) -> Tuple[str, int, int]:
        """Generate response using current model"""
        max_tokens = max_tokens or self.default_max_tokens
        temperature = temperature or self.default_temperature
        
        start_time = time.time()
        
        try:
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens,
                        "top_p": 0.9
                    }
                },
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "")
                tokens_used = result.get("eval_count", 0)
                elapsed_ms = int((time.time() - start_time) * 1000)
                logger.info(f"Generated {tokens_used} tokens in {elapsed_ms}ms")
                return response_text, elapsed_ms, tokens_used
            else:
                return f"Error: {response.status_code}", 0, 0
                
        except requests.exceptions.ConnectionError:
            return "Cannot connect to Ollama. Please make sure Ollama is running.", 0, 0
        except Exception as e:
            return f"Error: {str(e)}", 0, 0
    
    def health_check(self) -> Dict[str, Any]:
        """Check if Ollama server is available"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                return {"available": True}
            return {"available": False}
        except Exception as e:
            return {"available": False, "error": str(e)}


_llm_instance = None


def get_llm(model_name: str = None) -> LlamaInterface:
    """Get or create global Llama interface instance"""
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = LlamaInterface(model_name=model_name)
    elif model_name and _llm_instance.get_current_model() != model_name:
        _llm_instance.switch_model(model_name)
    return _llm_instance