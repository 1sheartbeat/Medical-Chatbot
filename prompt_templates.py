"""
Prompt templates for Medical Chatbot
"""

from typing import List, Dict, Optional

SYSTEM_PROMPT = """You are MediAssist, a professional medical assistant. Provide helpful, accurate, and safe health information.

CRITICAL RULES:
1. NEVER provide a medical diagnosis - always recommend consulting a doctor
2. Identify emergencies and urge immediate medical care
3. Be empathetic, clear, and concise
4. Always include the safety disclaimer

Remember: You are a supportive tool, not a replacement for doctors.
"""

EMERGENCY_RESPONSE = """🚨 **URGENT MEDICAL ALERT** 🚨

Please take immediate action:
1. Call Emergency Services (911) immediately
2. Go to the nearest emergency room
3. Do not wait

I am an AI assistant and cannot provide emergency medical care.
"""


class PromptBuilder:
    def __init__(self):
        self.system_prompt = SYSTEM_PROMPT
    
    def build_prompt(self, user_message: str, context_history: Optional[List[Dict]] = None,
                     intent: str = "general", include_history: bool = True) -> str:
        prompt_parts = [self.system_prompt, ""]
        
        if include_history and context_history:
            prompt_parts.append("Previous conversation:")
            for turn in context_history[-3:]:
                prompt_parts.append(f"User: {turn['user']}")
                prompt_parts.append(f"Assistant: {turn['bot']}")
            prompt_parts.append("")
        
        prompt_parts.append(f"User: {user_message}")
        prompt_parts.append("Assistant: ")
        
        return "\n".join(prompt_parts)
    
    def get_emergency_response(self) -> str:
        return EMERGENCY_RESPONSE
    
    def format_response(self, response: str, intent: str = "general") -> str:
        return response.strip()


_prompt_builder = None


def get_prompt_builder() -> PromptBuilder:
    global _prompt_builder
    if _prompt_builder is None:
        _prompt_builder = PromptBuilder()
    return _prompt_builder


def is_emergency_query(message: str) -> bool:
    from chatbot.intent_classifier import get_intent_classifier
    return get_intent_classifier().is_emergency(message)