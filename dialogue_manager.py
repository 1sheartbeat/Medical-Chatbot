"""
Dialogue Manager for Task-Oriented Medical Chatbot
"""

import re
from typing import List, Dict, Optional, Tuple
from collections import deque
from datetime import datetime


class DialogueManager:
    """Manage conversation state"""
    
    INTENT_PATTERNS = {
        "emergency": [
            r'\b(chest pain|heart attack|severe bleeding|difficulty breathing)\b',
            r'\b(emergency|911|ambulance|choking|seizure|stroke)\b'
        ],
        "symptom": [
            r'\b(symptom|pain|ache|fever|cough|headache|nausea|fatigue)\b'
        ],
        "medication": [
            r'\b(medication|drug|pill|dosage|prescription|side effect)\b'
        ],
        "greeting": [
            r'\b(hi|hello|hey|greetings|good morning)\b'
        ]
    }
    
    def __init__(self, session_id: str, max_history: int = 10):
        self.session_id = session_id
        self.max_history = max_history
        self.conversation_history: deque = deque(maxlen=max_history)
        self.current_intent: Optional[str] = None
        self.created_at = datetime.utcnow()
        self.last_activity = datetime.utcnow()
    
    def detect_intent(self, user_message: str) -> Tuple[str, float]:
        """Detect user intent"""
        user_lower = user_message.lower()
        
        for intent, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, user_lower, re.IGNORECASE):
                    return intent, 0.8
        
        return "general", 0.0
    
    def add_turn(self, user_message: str, bot_response: str, intent: str = None,
                 confidence: float = 0.0, tokens_used: int = 0, response_time_ms: int = 0):
        """Add conversation turn"""
        self.conversation_history.append({
            "user": user_message,
            "bot": bot_response,
            "intent": intent or self.current_intent,
            "confidence": confidence,
            "timestamp": datetime.utcnow()
        })
        
        if intent:
            self.current_intent = intent
        self.last_activity = datetime.utcnow()
    
    def get_context(self, n: int = None) -> List[Dict]:
        """Get conversation context"""
        if n is None:
            return list(self.conversation_history)
        return list(self.conversation_history)[-n:]
    
    def reset_session(self):
        """Reset conversation"""
        self.conversation_history.clear()
        self.current_intent = None
        self.last_activity = datetime.utcnow()
    
    def get_state(self) -> Dict:
        """Get session state"""
        return {
            "session_id": self.session_id,
            "current_intent": self.current_intent,
            "history_length": len(self.conversation_history)
        }


# Global session storage
_sessions = {}


def get_dialogue_manager(session_id: str, max_history: int = 10) -> DialogueManager:
    """Get or create dialogue manager for a session"""
    if session_id not in _sessions:
        _sessions[session_id] = DialogueManager(session_id, max_history)
    return _sessions[session_id]