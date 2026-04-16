let isLoading = false;
let currentSessionId = null;
let currentModel = 'gemma3:4b';

// DOM elements
const messagesList = document.getElementById('messagesList');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const newChatBtn = document.getElementById('newChatBtn');
const welcomeMessage = document.getElementById('welcomeMessage');
const sessionList = document.getElementById('sessionList');
const modelSelect = document.getElementById('modelSelect');
const currentModelSpan = document.getElementById('currentModel');

// Initialize
loadSessions();
loadCurrentModel();

// Event listeners
userInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 100) + 'px';
});

userInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

sendBtn.addEventListener('click', sendMessage);

newChatBtn.addEventListener('click', createNewChat);

modelSelect.addEventListener('change', function() {
    switchModel(this.value);
});

// Load all sessions
async function loadSessions() {
    try {
        const response = await fetch('/api/sessions');
        const data = await response.json();
        
        sessionList.innerHTML = '';
        
        if (data.sessions && data.sessions.length > 0) {
            data.sessions.forEach(session => {
                addSessionToSidebar(session);
            });
            
            const mostRecent = data.sessions[0];
            currentSessionId = mostRecent.session_id;
            highlightActiveSession(currentSessionId);
            await loadSessionMessages(currentSessionId);
        } else {
            await createNewChat();
        }
    } catch (error) {
        console.error('Load sessions error:', error);
    }
}

// Add session to sidebar
function addSessionToSidebar(session) {
    const sessionDiv = document.createElement('div');
    sessionDiv.className = 'session-item';
    sessionDiv.dataset.sessionId = session.session_id;
    
    sessionDiv.innerHTML = `
        <div class="session-info">
            <div class="session-title">${escapeHtml(session.title)}</div>
            <div class="session-date">${formatDate(session.updated_at)}</div>
        </div>
        <button class="delete-session" onclick="deleteSession('${session.session_id}', event)">
            <i class="fas fa-trash"></i>
        </button>
    `;
    
    sessionDiv.addEventListener('click', (e) => {
        if (!e.target.closest('.delete-session')) {
            switchSession(session.session_id);
        }
    });
    
    sessionList.appendChild(sessionDiv);
}

// Highlight active session
function highlightActiveSession(sessionId) {
    document.querySelectorAll('.session-item').forEach(item => {
        if (item.dataset.sessionId === sessionId) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });
}

// Switch to another session
async function switchSession(sessionId) {
    currentSessionId = sessionId;
    highlightActiveSession(sessionId);
    await loadSessionMessages(sessionId);
    
    await fetch('/api/current_session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId })
    });
}

// Load messages for a session
async function loadSessionMessages(sessionId) {
    try {
        const response = await fetch(`/api/sessions/${sessionId}`);
        const data = await response.json();
        
        messagesList.innerHTML = '';
        
        if (data.messages && data.messages.length > 0) {
            if (welcomeMessage) welcomeMessage.style.display = 'none';
            
            data.messages.forEach(msg => {
                addMessageToUI(msg.user, 'user');
                addMessageToUI(msg.bot, 'bot');
            });
        } else {
            if (welcomeMessage) welcomeMessage.style.display = 'block';
        }
        
        scrollToBottom();
    } catch (error) {
        console.error('Load messages error:', error);
    }
}

// Create new chat session
async function createNewChat() {
    try {
        const response = await fetch('/api/sessions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title: 'New Conversation' })
        });
        
        const data = await response.json();
        currentSessionId = data.session_id;
        
        await loadSessions();
        
        messagesList.innerHTML = '';
        if (welcomeMessage) welcomeMessage.style.display = 'block';
        
        showToast('New conversation created', 'success');
    } catch (error) {
        console.error('Create session error:', error);
    }
}

// Delete a session
async function deleteSession(sessionId, event) {
    event.stopPropagation();
    
    if (!confirm('Delete this conversation?')) return;
    
    try {
        const response = await fetch(`/api/sessions/${sessionId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            if (currentSessionId === sessionId) {
                await createNewChat();
            }
            await loadSessions();
            showToast('Conversation deleted', 'success');
        }
    } catch (error) {
        console.error('Delete session error:', error);
        showToast('Failed to delete', 'error');
    }
}

// Send message
async function sendMessage() {
    const message = userInput.value.trim();
    if (!message || isLoading) return;
    
    userInput.value = '';
    userInput.style.height = 'auto';
    
    if (welcomeMessage) welcomeMessage.style.display = 'none';
    
    addMessageToUI(message, 'user');
    showTypingIndicator();
    isLoading = true;
    sendBtn.disabled = true;
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                message: message,
                session_id: currentSessionId
            })
        });
        
        const data = await response.json();
        
        hideTypingIndicator();
        addMessageToUI(data.response, 'bot');
        
        await loadSessions();
        highlightActiveSession(currentSessionId);
        
    } catch (error) {
        console.error('Error:', error);
        hideTypingIndicator();
        addMessageToUI('Sorry, I encountered an error. Please try again.', 'bot');
        showToast('Connection error', 'error');
    } finally {
        isLoading = false;
        sendBtn.disabled = false;
        userInput.focus();
    }
}

// Add message to UI
function addMessageToUI(text, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubble.innerHTML = escapeHtml(text).replace(/\n/g, '<br>');
    
    const timeSpan = document.createElement('div');
    timeSpan.className = 'message-time';
    timeSpan.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    bubble.appendChild(timeSpan);
    messageDiv.appendChild(bubble);
    messagesList.appendChild(messageDiv);
    
    scrollToBottom();
}

// Show typing indicator
function showTypingIndicator() {
    const indicator = document.createElement('div');
    indicator.id = 'typingIndicator';
    indicator.className = 'message bot';
    indicator.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';
    messagesList.appendChild(indicator);
    scrollToBottom();
}

// Hide typing indicator
function hideTypingIndicator() {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) indicator.remove();
}

// Scroll to bottom
function scrollToBottom() {
    const container = document.getElementById('messagesContainer');
    container.scrollTop = container.scrollHeight;
}

// Switch model
async function switchModel(modelName) {
    try {
        const response = await fetch('/api/switch_model', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ model_name: modelName })
        });
        
        if (response.ok) {
            currentModel = modelName;
            currentModelSpan.textContent = `Current: ${currentModel}`;
            showToast(`Switched to ${modelName}`, 'success');
        }
    } catch (error) {
        console.error('Switch model error:', error);
    }
}

// Load current model
async function loadCurrentModel() {
    try {
        const response = await fetch('/api/current_model');
        const data = await response.json();
        currentModel = data.model;
        currentModelSpan.textContent = `Current: ${currentModel}`;
        if (modelSelect) modelSelect.value = currentModel;
    } catch (error) {
        console.error('Load model error:', error);
    }
}

// Helper functions
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateStr) {
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now - date;
    
    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)} min ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)} hours ago`;
    return date.toLocaleDateString();
}

function showToast(message, type) {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    
    setTimeout(() => toast.remove(), 3000);
}