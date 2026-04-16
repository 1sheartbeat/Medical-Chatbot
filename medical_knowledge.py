"""
Medical Knowledge Base for Medical Chatbot
"""

from typing import Dict, List, Optional


class MedicalKnowledge:
    """Knowledge base for common medical conditions"""
    
    COMMON_CONDITIONS = {
        "flu": {
            "symptoms": ["fever", "cough", "sore throat", "body aches", "headache"],
            "self_care": ["Rest", "Stay hydrated", "OTC pain relievers"],
            "when_to_see_doctor": "Fever over 103°F, difficulty breathing"
        },
        "cold": {
            "symptoms": ["runny nose", "sneezing", "cough", "mild fever"],
            "self_care": ["Rest", "Drink warm fluids", "Saline spray"],
            "when_to_see_doctor": "Fever over 101°F, symptoms > 10 days"
        }
    }
    
    def __init__(self):
        self.conditions = self.COMMON_CONDITIONS
    
    def get_condition_info(self, condition: str) -> Optional[Dict]:
        """Get information about a condition"""
        condition_lower = condition.lower()
        for key in self.conditions:
            if key in condition_lower or condition_lower in key:
                return self.conditions[key]
        return None
    
    def suggest_red_flags(self, symptoms: List[str]) -> List[str]:
        """Suggest red flags based on symptoms"""
        red_flags = []
        symptom_text = " ".join(symptoms).lower()
        
        if "chest" in symptom_text and "pain" in symptom_text:
            red_flags.append("Chest pain may indicate a heart condition - seek immediate medical attention")
        
        return red_flags


_knowledge_base = None


def get_medical_knowledge() -> MedicalKnowledge:
    """Get global medical knowledge"""
    global _knowledge_base
    if _knowledge_base is None:
        _knowledge_base = MedicalKnowledge()
    return _knowledge_base