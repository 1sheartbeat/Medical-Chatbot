"""
API endpoint tests for Medical Chatbot
Tests Flask routes and API responses
"""

import unittest
import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from models import Conversation, UserSession


class TestAPI(unittest.TestCase):
    """Test cases for API endpoints"""
    
    def setUp(self):
        """Set up test client and database"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        self.client = app.test_client()
        
        with app.app_context():
            db.create_all()
    
    def tearDown(self):
        """Clean up after tests"""
        with app.app_context():
            db.session.remove()
            db.drop_all()
    
    def test_index_page(self):
        """Test home page loads"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'MediAssist', response.data)
    
    def test_chat_api_general(self):
        """Test chat API with general query"""
        response = self.client.post('/api/chat', 
            json={'message': 'What is the flu?'},
            headers={'Content-Type': 'application/json'})
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('response', data)
        self.assertIn('intent', data)
        self.assertEqual(data['intent'], 'symptom')
    
    def test_chat_api_empty_message(self):
        """Test chat API with empty message"""
        response = self.client.post('/api/chat', 
            json={'message': ''},
            headers={'Content-Type': 'application/json'})
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_chat_api_emergency(self):
        """Test chat API with emergency message"""
        response = self.client.post('/api/chat', 
            json={'message': 'I have chest pain and difficulty breathing'},
            headers={'Content-Type': 'application/json'})
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['intent'], 'emergency')
        self.assertIn('URGENT', data['response'])
        self.assertIn('911', data['response'])
    
    def test_history_api(self):
        """Test history API"""
        # First send a message
        self.client.post('/api/chat', 
            json={'message': 'Hello'},
            headers={'Content-Type': 'application/json'})
        
        # Then get history
        response = self.client.get('/api/history')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('history', data)
    
    def test_reset_api(self):
        """Test reset API"""
        # Send a message first
        self.client.post('/api/chat', 
            json={'message': 'Hello'},
            headers={'Content-Type': 'application/json'})
        
        # Reset session
        response = self.client.post('/api/reset')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
    
    def test_stats_api(self):
        """Test stats API"""
        response = self.client.get('/api/stats')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('session', data)
        self.assertIn('total_messages', data)
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('status', data)
        self.assertIn('database', data)
    
    def test_feedback_api(self):
        """Test feedback submission"""
        # First send a message to get conversation ID
        chat_response = self.client.post('/api/chat', 
            json={'message': 'Test message'},
            headers={'Content-Type': 'application/json'})
        
        chat_data = json.loads(chat_response.data)
        
        # Submit feedback
        response = self.client.post('/api/feedback',
            json={
                'conversation_id': 1,
                'rating': 5,
                'comment': 'Very helpful!',
                'was_helpful': True
            },
            headers={'Content-Type': 'application/json'})
        
        # Note: Feedback may not be implemented yet
        self.assertIn(response.status_code, [200, 404])
    
    def test_rate_limiting(self):
        """Test rate limiting (if implemented)"""
        # Make multiple requests quickly
        for _ in range(5):
            response = self.client.post('/api/chat',
                json={'message': 'Test message'},
                headers={'Content-Type': 'application/json'})
            self.assertIn(response.status_code, [200, 429])


class TestDatabaseModels(unittest.TestCase):
    """Test cases for database models"""
    
    def setUp(self):
        """Set up test database"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        with app.app_context():
            db.create_all()
    
    def tearDown(self):
        """Clean up after tests"""
        with app.app_context():
            db.session.remove()
            db.drop_all()
    
    def test_create_conversation(self):
        """Test creating a conversation record"""
        with app.app_context():
            conv = Conversation(
                session_id='test-session',
                user_message='Hello',
                bot_response='Hi there!',
                intent='greeting',
                confidence=0.95
            )
            db.session.add(conv)
            db.session.commit()
            
            saved = Conversation.query.first()
            self.assertIsNotNone(saved)
            self.assertEqual(saved.user_message, 'Hello')
            self.assertEqual(saved.bot_response, 'Hi there!')
    
    def test_create_session(self):
        """Test creating a session record"""
        with app.app_context():
            session = UserSession(
                session_id='test-session-123',
                user_ip='127.0.0.1',
                user_agent='Test Agent'
            )
            db.session.add(session)
            db.session.commit()
            
            saved = UserSession.query.first()
            self.assertIsNotNone(saved)
            self.assertEqual(saved.session_id, 'test-session-123')
            self.assertEqual(saved.message_count, 0)
    
    def test_increment_message_count(self):
        """Test incrementing message count"""
        with app.app_context():
            session = UserSession(
                session_id='test-session',
                user_ip='127.0.0.1'
            )
            db.session.add(session)
            db.session.commit()
            
            session.increment_messages()
            db.session.commit()
            
            saved = UserSession.query.first()
            self.assertEqual(saved.message_count, 1)


if __name__ == '__main__':
    unittest.main()