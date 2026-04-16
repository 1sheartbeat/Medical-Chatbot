"""
Database models for Medical Chatbot
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Conversation(db.Model):
    """Stores conversation history"""
    __tablename__ = 'conversations'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(64), nullable=False, index=True)
    user_message = db.Column(db.Text, nullable=False)
    bot_response = db.Column(db.Text, nullable=False)
    intent = db.Column(db.String(32), default='general')
    confidence = db.Column(db.Float, default=0.0)
    response_time_ms = db.Column(db.Integer, default=0)
    tokens_used = db.Column(db.Integer, default=0)
    is_emergency = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user': self.user_message,
            'bot': self.bot_response,
            'intent': self.intent,
            'time': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


class ChatSession(db.Model):
    """Stores chat sessions for history"""
    __tablename__ = 'chat_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(64), nullable=False, unique=True, index=True)
    title = db.Column(db.String(200), default='New Conversation')
    message_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'title': self.title,
            'message_count': self.message_count,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }


class UserSession(db.Model):
    """Tracks user sessions"""
    __tablename__ = 'user_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(64), nullable=False, unique=True, index=True)
    user_ip = db.Column(db.String(45))
    user_agent = db.Column(db.String(512))
    message_count = db.Column(db.Integer, default=0)
    emergency_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_active = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def increment_messages(self):
        self.message_count += 1
        self.last_active = datetime.utcnow()
    
    def increment_emergency(self):
        self.emergency_count += 1
        self.last_active = datetime.utcnow()


class Feedback(db.Model):
    """Stores user feedback"""
    __tablename__ = 'feedback'
    
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id', ondelete='SET NULL'))
    session_id = db.Column(db.String(64), index=True)
    rating = db.Column(db.Integer)
    comment = db.Column(db.Text)
    was_helpful = db.Column(db.Boolean, default=None)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    conversation = db.relationship('Conversation', backref='feedbacks')