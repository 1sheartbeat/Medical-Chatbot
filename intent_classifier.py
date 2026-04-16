"""
Intent Classifier for Medical Chatbot
"""

import re
from typing import List, Dict, Tuple


class IntentClassifier:
    """Classifies user intents"""
    
    EMERGENCY_KEYWORDS = [
        "chest pain", "heart attack", "difficulty breathing", "can't breathe",
        "severe bleeding", "unconscious", "seizure", "stroke", "choking", "911"
    ]
    
    def __init__(self):
        pass
    
    def classify(self, text: str) -> Tuple[str, float, Dict[str, float]]:
        """Classify user input intent"""
        text_lower = text.lower()
        
        if self.is_emergency(text):
            return "emergency", 1.0, {"emergency": 1.0}
        
        if any(word in text_lower for word in ["symptom", "pain", "fever", "cough", "headache"]):
            return "symptom", 0.7, {"symptom": 0.7}
        
        if any(word in text_lower for word in ["medication", "medicine", "pill", "drug"]):
            return "medication", 0.7, {"medication": 0.7}
        
        if any(word in text_lower for word in ["hello", "hi", "hey"]):
            return "greeting", 0.8, {"greeting": 0.8}
        
        return "general", 0.3, {"general": 0.3}
    
    def is_emergency(self, text: str) -> bool:
        """Check if text indicates emergency"""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.EMERGENCY_KEYWORDS)
    
    def extract_medical_terms(self, text: str) -> List[str]:
        """Extract potential medical terms"""
        return []
    
    def get_urgency_level(self, text: str) -> int:
        """Determine urgency level"""
        return 5 if self.is_emergency(text) else 2


# Global instance
_intent_classifier = None


def get_intent_classifier() -> IntentClassifier:
    """Get or create global intent classifier"""
    global _intent_classifier
    if _intent_classifier is None:
        _intent_classifier = IntentClassifier()
    return _intent_classifier