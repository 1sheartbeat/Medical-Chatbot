"""
Security utilities for Medical Chatbot
Provides input sanitization, session validation, and security helpers
"""

import re
import hashlib
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple
from functools import wraps
from flask import request, session, jsonify

logger = logging.getLogger(__name__)


class SecurityHelper:
    """
    Security helper class for input validation and sanitization
    """
    
    # Pattern for dangerous SQL injection attempts
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|UNION)\b)",
        r"(--)",
        r"(;.*--)",
        r"(\bOR\b.*=)",
        r"(\bAND\b.*=)"
    ]
    
    # Pattern for XSS attempts
    XSS_PATTERNS = [
        r"<script.*?>.*?</script>",
        r"javascript:",
        r"onerror=",
        r"onload=",
        r"onclick=",
        r"<iframe.*?>"
    ]
    
    # Maximum message length
    MAX_MESSAGE_LENGTH = 2000
    
    @staticmethod
    def sanitize_input(text: str) -> str:
        """
        Sanitize user input to prevent injection attacks
        
        Args:
            text: Raw user input
            
        Returns:
            Sanitized input
        """
        if not text:
            return ""
        
        # Trim whitespace
        text = text.strip()
        
        # Limit length
        if len(text) > SecurityHelper.MAX_MESSAGE_LENGTH:
            text = text[:SecurityHelper.MAX_MESSAGE_LENGTH]
            logger.warning(f"Input truncated to {SecurityHelper.MAX_MESSAGE_LENGTH} chars")
        
        # Remove dangerous characters
        text = re.sub(r'[<>]', '', text)
        
        # Remove SQL injection patterns
        for pattern in SecurityHelper.SQL_INJECTION_PATTERNS:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Remove XSS patterns
        for pattern in SecurityHelper.XSS_PATTERNS:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        return text
    
    @staticmethod
    def is_safe_input(text: str) -> Tuple[bool, str]:
        """
        Check if input is safe
        
        Args:
            text: Input to check
            
        Returns:
            Tuple of (is_safe, reason)
        """
        if not text:
            return True, ""
        
        # Check length
        if len(text) > SecurityHelper.MAX_MESSAGE_LENGTH:
            return False, f"Message exceeds maximum length of {SecurityHelper.MAX_MESSAGE_LENGTH} characters"
        
        # Check for SQL injection
        for pattern in SecurityHelper.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return False, "Potential SQL injection detected"
        
        # Check for XSS
        for pattern in SecurityHelper.XSS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return False, "Potential XSS attack detected"
        
        return True, ""
    
    @staticmethod
    def generate_session_id() -> str:
        """
        Generate a secure random session ID
        
        Returns:
            Secure random session ID
        """
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def hash_token(token: str) -> str:
        """
        Hash a token for secure storage
        
        Args:
            token: Token to hash
            
        Returns:
            SHA-256 hash of token
        """
        return hashlib.sha256(token.encode()).hexdigest()
    
    @staticmethod
    def validate_session(session_id: str, stored_sessions: dict, timeout_seconds: int = 3600) -> bool:
        """
        Validate if session is still active
        
        Args:
            session_id: Session ID to validate
            stored_sessions: Dictionary of stored sessions
            timeout_seconds: Session timeout in seconds
            
        Returns:
            True if session is valid, False otherwise
        """
        if session_id not in stored_sessions:
            return False
        
        session_data = stored_sessions[session_id]
        last_active = session_data.get('last_active')
        
        if not last_active:
            return False
        
        # Check timeout
        elapsed = (datetime.utcnow() - last_active).total_seconds()
        if elapsed > timeout_seconds:
            return False
        
        return True
    
    @staticmethod
    def rate_limit_check(ip: str, request_count: dict, limit: int = 10, period: int = 60) -> Tuple[bool, int]:
        """
        Check rate limit for IP address
        
        Args:
            ip: IP address
            request_count: Dictionary tracking request counts
            limit: Maximum requests per period
            period: Time period in seconds
            
        Returns:
            Tuple of (allowed, remaining_requests)
        """
        now = datetime.utcnow()
        
        if ip not in request_count:
            request_count[ip] = {'count': 1, 'window_start': now}
            return True, limit - 1
        
        data = request_count[ip]
        elapsed = (now - data['window_start']).total_seconds()
        
        if elapsed > period:
            # Reset window
            data['count'] = 1
            data['window_start'] = now
            return True, limit - 1
        
        if data['count'] >= limit:
            return False, 0
        
        data['count'] += 1
        remaining = limit - data['count']
        return True, remaining


def sanitize_input(text: str) -> str:
    """Convenience function for input sanitization"""
    return SecurityHelper.sanitize_input(text)


def validate_session(session_id: str, stored_sessions: dict) -> bool:
    """Convenience function for session validation"""
    return SecurityHelper.validate_session(session_id, stored_sessions)


def rate_limit(limit: int = 10, period: int = 60):
    """
    Decorator for rate limiting API endpoints
    
    Args:
        limit: Maximum requests per period
        period: Time period in seconds
    """
    request_counts = {}
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get client IP
            ip = request.remote_addr
            
            # Check rate limit
            allowed, remaining = SecurityHelper.rate_limit_check(ip, request_counts, limit, period)
            
            if not allowed:
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'message': f'Too many requests. Please try again in {period} seconds.'
                }), 429
            
            # Add rate limit headers
            response = f(*args, **kwargs)
            
            if isinstance(response, tuple):
                resp_obj = response[0]
                status_code = response[1] if len(response) > 1 else 200
                headers = response[2] if len(response) > 2 else {}
                headers['X-RateLimit-Remaining'] = str(remaining)
                return resp_obj, status_code, headers
            elif hasattr(response, 'headers'):
                response.headers['X-RateLimit-Remaining'] = str(remaining)
                return response
            
            return response
        
        return decorated_function
    
    return decorator