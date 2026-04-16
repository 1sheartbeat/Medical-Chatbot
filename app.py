"""
Medical Chatbot - Main Application with History and Multi-Model Support
"""

import uuid
import logging
import requests
import time
from datetime import datetime

from flask import Flask, render_template, request, jsonify, session

app = Flask(__name__)
app.secret_key = 'your-secret-key'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
from models import db, Conversation, ChatSession

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chatbot.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    db.create_all()


@app.route('/')
def index():
    """Render chat interface"""
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return render_template('index.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/privacy')
def privacy():
    return render_template('privacy.html')


@app.route('/api/chat', methods=['POST'])
def chat():
    """Chat API with Ollama - Detailed medical responses"""
    data = request.get_json()
    user_message = data.get('message', '').strip()
    session_id = data.get('session_id', session.get('session_id'))
    
    if not user_message:
        return jsonify({'error': 'Message cannot be empty'}), 400
    
    if not session_id:
        session_id = str(uuid.uuid4())
        session['session_id'] = session_id
    
    logger.info(f"Session {session_id[:8]}: {user_message[:100]}")
    
    # Update or create chat session
    chat_session = ChatSession.query.filter_by(session_id=session_id).first()
    if not chat_session:
        title = user_message[:50] + ('...' if len(user_message) > 50 else '')
        chat_session = ChatSession(session_id=session_id, title=title)
        db.session.add(chat_session)
        db.session.commit()
    
    # Emergency detection
    emergency_keywords = ['chest pain', 'heart attack', 'difficulty breathing', 'emergency', '911', 
                          'severe bleeding', 'unconscious', 'seizure', 'stroke', 'suicide', 'overdose']
    if any(kw in user_message.lower() for kw in emergency_keywords):
        response = """🚨 **URGENT MEDICAL ALERT** 🚨

The symptoms you described may indicate a medical emergency.

**Please take immediate action:**
1. Call Emergency Services (911) immediately
2. Go to the nearest emergency room
3. Do not wait for symptoms to improve

**While waiting for help:**
- Stay calm and rest
- Have someone stay with you
- Do not eat or drink unless instructed

I am an AI assistant and cannot provide emergency medical care. Please get professional help immediately."""
        
        conv = Conversation(
            session_id=session_id,
            user_message=user_message,
            bot_response=response,
            intent='emergency',
            is_emergency=True
        )
        db.session.add(conv)
        chat_session.message_count += 1
        db.session.commit()
        
        return jsonify({'response': response, 'session_id': session_id})
    
    # Build detailed medical prompt
    prompt = f"""You are MediAssist, a professional, empathetic medical assistant. Provide detailed, accurate, and safe health information.

**Guidelines for your response:**
1. If asked about symptoms: List common symptoms, possible causes, and when to worry
2. If asked about treatment: Provide general self-care recommendations (rest, hydration, OTC options)
3. Always include specific "when to see a doctor" guidance
4. Include a clear medical disclaimer
5. Use bullet points for easy reading
6. Be empathetic and professional

**User Question:** {user_message}

**Your Response (detailed and helpful):**
Assistant: """
    
    # Get current model from session
    current_model = session.get('current_model', 'gemma3:4b')
    
    # Call Ollama
    try:
        start_time = time.time()
        
        ollama_response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": current_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 512
                }
            },
            timeout=180
        )
        
        if ollama_response.status_code == 200:
            result = ollama_response.json()
            response = result.get("response", "I'm not sure how to answer that. Please consult a healthcare professional.")
            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.info(f"Response time: {elapsed_ms}ms")
        else:
            response = "Sorry, I'm having technical difficulties. Please try again later."
            elapsed_ms = 0
            
    except requests.exceptions.ConnectionError:
        response = "Cannot connect to the AI service. Please make sure Ollama is running with 'ollama serve'"
        elapsed_ms = 0
    except requests.exceptions.Timeout:
        response = "The request is taking too long. Please try again or ask a simpler question."
        elapsed_ms = 0
    except Exception as e:
        logger.error(f"Error: {e}")
        response = f"An error occurred: {str(e)}"
        elapsed_ms = 0
    
    # Add medical disclaimer
    disclaimer = "\n\n---\n⚠️ **Medical Disclaimer:** I am an AI assistant providing general health information only. This is not a substitute for professional medical advice, diagnosis, or treatment. Always consult a qualified healthcare provider for medical concerns."
    
    if len(response) < 2000:
        response = response + disclaimer
    
    # Save to database
    conv = Conversation(
        session_id=session_id,
        user_message=user_message,
        bot_response=response,
        intent='general',
        response_time_ms=elapsed_ms
    )
    db.session.add(conv)
    chat_session.message_count += 1
    chat_session.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'response': response,
        'session_id': session_id,
        'response_time_ms': elapsed_ms
    })


@app.route('/api/sessions', methods=['GET'])
def get_sessions():
    """Get all chat sessions for history"""
    sessions = ChatSession.query.order_by(ChatSession.updated_at.desc()).all()
    return jsonify({'sessions': [s.to_dict() for s in sessions]})


@app.route('/api/sessions/<session_id>', methods=['GET'])
def get_session_messages(session_id):
    """Get messages for a specific session"""
    conversations = Conversation.query.filter_by(session_id=session_id).order_by(Conversation.created_at).all()
    return jsonify({'messages': [c.to_dict() for c in conversations]})


@app.route('/api/sessions', methods=['POST'])
def create_session():
    """Create a new chat session"""
    session_id = str(uuid.uuid4())
    title = request.json.get('title', 'New Conversation')
    chat_session = ChatSession(session_id=session_id, title=title)
    db.session.add(chat_session)
    db.session.commit()
    return jsonify({'session_id': session_id, 'session': chat_session.to_dict()})


@app.route('/api/sessions/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """Delete a session and its messages"""
    chat_session = ChatSession.query.filter_by(session_id=session_id).first()
    if chat_session:
        Conversation.query.filter_by(session_id=session_id).delete()
        db.session.delete(chat_session)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'error': 'Session not found'}), 404


@app.route('/api/current_session', methods=['POST'])
def set_current_session():
    """Set current session"""
    data = request.get_json()
    session_id = data.get('session_id')
    session['session_id'] = session_id
    return jsonify({'success': True, 'session_id': session_id})


@app.route('/api/models', methods=['GET'])
def get_models():
    """Get available models"""
    return jsonify({
        'models': [
            {'name': 'gemma3:4b', 'description': 'Fast, Lightweight'},
            {'name': 'llama3:8b', 'description': 'Balanced Performance'},
            {'name': 'deepseek-r1:7b', 'description': 'Medical Reasoning'}
        ]
    })


@app.route('/api/switch_model', methods=['POST'])
def switch_model():
    """Switch model (stored in session)"""
    data = request.get_json()
    model_name = data.get('model_name')
    session['current_model'] = model_name
    return jsonify({'success': True, 'current_model': model_name})


@app.route('/api/current_model', methods=['GET'])
def get_current_model():
    """Get current model"""
    model = session.get('current_model', 'gemma3:4b')
    return jsonify({'model': model})


@app.route('/api/history', methods=['GET'])
def get_history():
    """Get conversation history (legacy)"""
    session_id = session.get('session_id')
    if not session_id:
        return jsonify({'history': []})
    
    conversations = Conversation.query.filter_by(
        session_id=session_id
    ).order_by(Conversation.created_at).limit(50).all()
    
    history = [c.to_dict() for c in conversations]
    return jsonify({'history': history})


@app.route('/api/reset', methods=['POST'])
def reset_session():
    """Reset current conversation"""
    session_id = session.get('session_id')
    if session_id:
        Conversation.query.filter_by(session_id=session_id).delete()
        db.session.commit()
    return jsonify({'status': 'success'})


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)