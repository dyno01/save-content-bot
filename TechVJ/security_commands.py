# Security commands for VJ Save Restricted Content Bot
from pyrogram import Client, filters
from pyrogram.types import Message
from security import security_manager
# Admin functionality removed
import time

@Client.on_message(filters.private & filters.command(["security"]))
async def security_status(client: Client, message: Message):
    """Show security status and settings"""
    user_id = message.from_user.id
    
    # Get user activity info
    activity = security_manager.user_activity.get(user_id, {})
    suspicious_count = security_manager.suspicious_activity.get(user_id, 0)
    
    # Calculate session time remaining (if timeout is enabled)
    if security_manager.SESSION_TIMEOUT > 0:
        last_activity = activity.get('last_activity', 0)
        time_remaining = security_manager.SESSION_TIMEOUT - (time.time() - last_activity)
        time_remaining = max(0, time_remaining)
        
        # Format time remaining
        hours = int(time_remaining // 3600)
        minutes = int((time_remaining % 3600) // 60)
        seconds = int(time_remaining % 60)
        
        if hours > 0:
            time_str = f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            time_str = f"{minutes}m {seconds}s"
        else:
            time_str = f"{seconds}s"
    else:
        time_str = "Disabled (No timeout)"
    
    status_text = f"""
🔒 **Security Status**

**Session Info:**
• Session expires in: `{time_str}`
• Requests made: `{activity.get('request_count', 0)}`
• Suspicious activities: `{suspicious_count}`

**Security Settings:**
• Max batch size: `{security_manager.MAX_BATCH_SIZE}`
• Session timeout: `{"Disabled" if security_manager.SESSION_TIMEOUT == 0 else f"{security_manager.SESSION_TIMEOUT // 3600} hours"}`
• Rate limit: `{security_manager.MAX_REQUESTS_PER_WINDOW} requests per {security_manager.RATE_LIMIT_WINDOW // 60} minutes`

**Your Status:**
• Rate limited: `{'Yes' if security_manager.is_rate_limited(user_id) else 'No'}`
• Session expired: `{'Yes' if security_manager.is_session_expired(user_id) else 'No'}`

**Tips:**
• Use `/logout` if you suspect unauthorized access
• Don't share your login session with others
• Use `/force_logout` for emergency security
"""
    
    await message.reply_text(status_text)

# Admin commands removed - no longer needed

@Client.on_message(filters.private & filters.command(["force_logout"]))
async def force_logout(client: Client, message: Message):
    """Force logout all sessions (security measure)"""
    user_id = message.from_user.id
    
    # Clear all security data
    security_manager.user_activity.pop(user_id, None)
    security_manager.rate_limits.pop(user_id, None)
    security_manager.suspicious_activity.pop(user_id, None)
    
    # Clear session from database
    from database.db import db
    await db.set_session(user_id, session=None)
    
    security_manager.log_security_event(user_id, "FORCE_LOGOUT", "User forced logout")
    
    await message.reply_text("**🔒 All sessions logged out for security. Please /login again.**")

