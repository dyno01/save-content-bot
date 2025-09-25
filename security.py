# Security module for VJ Save Restricted Content Bot
import os
import time
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional
import asyncio
from pyrogram import Client
from pyrogram.errors import FloodWait, AuthKeyUnregistered, SessionPasswordNeeded

class SecurityManager:
    def __init__(self):
        # Security configurations
        self.MAX_BATCH_SIZE = int(os.environ.get('MAX_BATCH_SIZE', '100'))
        self.SESSION_TIMEOUT = int(os.environ.get('SESSION_TIMEOUT', '0'))  # 0 = disabled
        self.RATE_LIMIT_WINDOW = int(os.environ.get('RATE_LIMIT_WINDOW', '300'))  # 5 minutes
        self.MAX_REQUESTS_PER_WINDOW = int(os.environ.get('MAX_REQUESTS_PER_WINDOW', '20'))
        self.MAX_FILE_SIZE = int(os.environ.get('MAX_FILE_SIZE', '2097152000'))  # 2GB
        
        # User activity tracking
        self.user_activity: Dict[int, Dict] = {}
        self.rate_limits: Dict[int, list] = {}
        self.suspicious_activity: Dict[int, int] = {}
        
    def generate_session_id(self) -> str:
        """Generate a secure session ID"""
        return secrets.token_urlsafe(32)
    
    def hash_session(self, session_string: str) -> str:
        """Hash session string for secure storage"""
        return hashlib.sha256(session_string.encode()).hexdigest()
    
    def is_rate_limited(self, user_id: int) -> bool:
        """Check if user is rate limited"""
        now = time.time()
        if user_id not in self.rate_limits:
            self.rate_limits[user_id] = []
        
        # Remove old requests outside the window
        self.rate_limits[user_id] = [
            req_time for req_time in self.rate_limits[user_id] 
            if now - req_time < self.RATE_LIMIT_WINDOW
        ]
        
        # Check if user has exceeded the limit
        if len(self.rate_limits[user_id]) >= self.MAX_REQUESTS_PER_WINDOW:
            return True
        
        # Add current request
        self.rate_limits[user_id].append(now)
        return False
    
    def track_user_activity(self, user_id: int, activity_type: str):
        """Track user activity for security monitoring"""
        now = time.time()
        if user_id not in self.user_activity:
            self.user_activity[user_id] = {
                'last_activity': now,
                'login_time': None,
                'request_count': 0,
                'suspicious_count': 0
            }
        
        self.user_activity[user_id]['last_activity'] = now
        self.user_activity[user_id]['request_count'] += 1
        
        # Track suspicious activity
        if activity_type in ['large_batch', 'rapid_requests', 'invalid_input']:
            self.user_activity[user_id]['suspicious_count'] += 1
            if user_id not in self.suspicious_activity:
                self.suspicious_activity[user_id] = 0
            self.suspicious_activity[user_id] += 1
    
    def is_session_expired(self, user_id: int) -> bool:
        """Check if user session has expired"""
        # Session timeout is disabled (SESSION_TIMEOUT = 0)
        if self.SESSION_TIMEOUT == 0:
            return False
            
        if user_id not in self.user_activity:
            return True
        
        last_activity = self.user_activity[user_id].get('last_activity', 0)
        return time.time() - last_activity > self.SESSION_TIMEOUT
    
    def validate_batch_size(self, from_id: int, to_id: int) -> tuple[bool, str]:
        """Validate batch size for safety"""
        batch_size = to_id - from_id + 1
        
        if batch_size <= 0:
            return False, "Invalid batch range"
        
        if batch_size > self.MAX_BATCH_SIZE:
            return False, f"Batch size too large. Maximum allowed: {self.MAX_BATCH_SIZE}"
        
        if batch_size > 50:
            return True, f"Large batch detected ({batch_size} messages). This may take a while."
        
        return True, "Valid batch"
    
    def validate_input(self, text: str) -> tuple[bool, str]:
        """Validate user input for security"""
        if not text or len(text) > 2000:
            return False, "Input too long or empty"
        
        # Check for suspicious patterns
        suspicious_patterns = [
            'script', 'javascript', 'eval', 'exec', 'import',
            'subprocess', 'os.system', 'shell', 'cmd'
        ]
        
        text_lower = text.lower()
        for pattern in suspicious_patterns:
            if pattern in text_lower:
                return False, "Suspicious input detected"
        
        return True, "Valid input"
    
    def get_security_warning(self, user_id: int) -> Optional[str]:
        """Get security warning for user if needed"""
        if user_id not in self.suspicious_activity:
            return None
        
        suspicious_count = self.suspicious_activity[user_id]
        if suspicious_count >= 5:
            return "⚠️ High suspicious activity detected. Your account may be temporarily restricted."
        elif suspicious_count >= 3:
            return "⚠️ Suspicious activity detected. Please use the bot responsibly."
        
        return None
    
    async def validate_session(self, client: Client, user_id: int) -> tuple[bool, str]:
        """Validate user session is still active"""
        try:
            # Try to get user info to validate session
            me = await client.get_me()
            if not me:
                return False, "Session validation failed"
            return True, "Session valid"
        except AuthKeyUnregistered:
            return False, "Session expired or invalid"
        except Exception as e:
            return False, f"Session validation error: {str(e)}"
    
    def log_security_event(self, user_id: int, event_type: str, details: str):
        """Log security events for monitoring"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] User {user_id}: {event_type} - {details}"
        
        # In production, you might want to send this to a logging service
        print(f"SECURITY: {log_entry}")
        
        # You could also write to a file or send to monitoring service
        # with open('security.log', 'a') as f:
        #     f.write(log_entry + '\n')

# Global security manager instance
security_manager = SecurityManager()

