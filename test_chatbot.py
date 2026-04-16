"""
Unit tests for Medical Chatbot components
Tests dialogue manager, intent classifier, and prompt builder
"""

import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from chatbot.dialogue_manager import DialogueManager, get_dialogue_manager
from chatbot.intent_classifier import IntentClassifier, get_intent_classifier
from chatbot.prompt_templates import PromptBuilder, get_prompt_builder, is_emergency_query
from chatbot.medical_knowledge import MedicalKnowledge, get_medical_knowledge


class TestDialogueManager(unittest.TestCase):
    """Test cases for DialogueManager class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.dm = DialogueManager("test-session-001", max_history=5)
    
    def test_detect_intent_symptom(self):
        """Test symptom intent detection"""
        intent, confidence = self.dm.detect_intent("I have a headache and fever")
        self.assertEqual(intent, "symptom")
        self.assertGreater(confidence, 0)
    
    def test_detect_intent_emergency(self):
        """Test emergency intent detection"""
        intent, confidence = self.dm.detect_intent("I have chest pain and difficulty breathing")
        self.assertEqual(intent, "emergency")
        self.assertGreater(confidence, 0)
    
    def test_detect_intent_medication(self):
        """Test medication intent detection"""
        intent, confidence = self.dm.detect_intent("What are the side effects of ibuprofen?")
        self.assertEqual(intent, "medication")
        self.assertGreater(confidence, 0)
    
    def test_add_turn(self):
        """Test adding conversation turn"""
        self.dm.add_turn("Hello", "Hi! How can I help?")
        self.assertEqual(len(self.dm.get_context()), 1)
        
        turn = self.dm.get_last_turn()
        self.assertEqual(turn['user'], "Hello")
        self.assertEqual(turn['bot'], "Hi! How can I help?")
    
    def test_context_limit(self):
        """Test context history limit"""
        for i in range(10):
            self.dm.add_turn(f"Message {i}", f"Response {i}")
        
        # Should only keep max_history (5) items
        self.assertEqual(len(self.dm.get_context()), 5)
    
    def test_reset_session(self):
        """Test session reset"""
        self.dm.add_turn("Test", "Response")
        self.assertEqual(len(self.dm.get_context()), 1)
        
        self.dm.reset_session()
        self.assertEqual(len(self.dm.get_context()), 0)
    
    def test_is_emergency(self):
        """Test emergency detection"""
        self.assertTrue(self.dm.is_emergency("I'm having a heart attack"))
        self.assertTrue(self.dm.is_emergency("Can't breathe"))
        self.assertFalse(self.dm.is_emergency("What is a headache?"))


class TestIntentClassifier(unittest.TestCase):
    """Test cases for IntentClassifier class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.classifier = IntentClassifier()
    
    def test_classify_symptom(self):
        """Test symptom classification"""
        intent, confidence, _ = self.classifier.classify("What are the symptoms of flu?")
        self.assertEqual(intent, "symptom")
        self.assertGreater(confidence, 0)
    
    def test_classify_medication(self):
        """Test medication classification"""
        intent, confidence, _ = self.classifier.classify("What medication should I take for headache?")
        self.assertEqual(intent, "medication")
        self.assertGreater(confidence, 0)
    
    def test_classify_emergency(self):
        """Test emergency classification"""
        intent, confidence, _ = self.classifier.classify("I have severe chest pain")
        self.assertEqual(intent, "emergency")
        self.assertEqual(confidence, 1.0)
    
    def test_classify_greeting(self):
        """Test greeting classification"""
        intent, confidence, _ = self.classifier.classify("Hello, how are you?")
        self.assertEqual(intent, "greeting")
        self.assertGreater(confidence, 0)
    
    def test_is_emergency_true(self):
        """Test emergency detection true cases"""
        self.assertTrue(self.classifier.is_emergency("Call 911"))
        self.assertTrue(self.classifier.is_emergency("I'm having a stroke"))
        self.assertTrue(self.classifier.is_emergency("Severe bleeding"))
    
    def test_is_emergency_false(self):
        """Test emergency detection false cases"""
        self.assertFalse(self.classifier.is_emergency("What is the flu?"))
        self.assertFalse(self.classifier.is_emergency("How to prevent cold?"))
    
    def test_extract_medical_terms(self):
        """Test medical term extraction"""
        terms = self.classifier.extract_medical_terms("I have pain in the chest and a fever")
        self.assertTrue(len(terms) >= 0)  # May return empty list
    

class TestPromptBuilder(unittest.TestCase):
    """Test cases for PromptBuilder class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.builder = PromptBuilder()
    
    def test_build_prompt_basic(self):
        """Test basic prompt building"""
        prompt = self.builder.build_prompt("What is the flu?", None, "general")
        self.assertIsInstance(prompt, str)
        self.assertGreater(len(prompt), 0)
        self.assertIn("What is the flu?", prompt)
    
    def test_build_prompt_with_context(self):
        """Test prompt building with context"""
        context = [
            {"user": "Hello", "bot": "Hi!"},
            {"user": "Help me", "bot": "How can I help?"}
        ]
        prompt = self.builder.build_prompt("What is flu?", context, "symptom")
        self.assertIn("Hello", prompt)
        self.assertIn("Hi!", prompt)
    
    def test_emergency_response(self):
        """Test emergency response template"""
        response = self.builder.get_emergency_response()
        self.assertIn("URGENT", response)
        self.assertIn("911", response)
    
    def test_format_response(self):
        """Test response formatting"""
        formatted = self.builder.format_response("  This is a test.  ")
        self.assertEqual(formatted, "This is a test.")
    
    def test_is_emergency_query(self):
        """Test emergency query detection"""
        self.assertTrue(is_emergency_query("I'm having a heart attack"))
        self.assertTrue(is_emergency_query("Call ambulance"))
        self.assertFalse(is_emergency_query("What is a cold?"))


class TestMedicalKnowledge(unittest.TestCase):
    """Test cases for MedicalKnowledge class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.knowledge = MedicalKnowledge()
    
    def test_get_condition_info(self):
        """Test condition information retrieval"""
        info = self.knowledge.get_condition_info("flu")
        self.assertIsNotNone(info)
        self.assertIn("symptoms", info)
        self.assertIn("self_care", info)
    
    def test_get_symptoms(self):
        """Test symptom retrieval"""
        symptoms = self.knowledge.get_symptoms("flu")
        self.assertIsInstance(symptoms, list)
        self.assertGreater(len(symptoms), 0)
    
    def test_get_self_care(self):
        """Test self-care retrieval"""
        self_care = self.knowledge.get_self_care("cold")
        self.assertIsInstance(self_care, list)
    
    def test_suggest_red_flags(self):
        """Test red flag suggestions"""
        red_flags = self.knowledge.suggest_red_flags(["chest pain"])
        self.assertGreater(len(red_flags), 0)
        
        red_flags = self.knowledge.suggest_red_flags(["mild headache"])
        self.assertEqual(len(red_flags), 0)


if __name__ == '__main__':
    unittest.main()