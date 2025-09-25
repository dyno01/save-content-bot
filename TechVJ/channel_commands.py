# Channel Management Commands for VJ Save Restricted Content Bot
from pyrogram import Client, filters
from pyrogram.types import Message
from config import LOG_CHANNEL, LOG_CHANNEL_USERNAME, ADMINS
from security import security_manager

@Client.on_message(filters.private & filters.command(["channel"]) & filters.user(ADMINS))
async def channel_status(client: Client, message: Message):
    """Show log channel status and configuration"""
    status_text = f"""
📺 **Log Channel Configuration**

**Current Settings:**
• **Channel ID:** `{LOG_CHANNEL if LOG_CHANNEL else 'Not Set'}`
• **Channel Username:** `{LOG_CHANNEL_USERNAME if LOG_CHANNEL_USERNAME else 'Not Set'}`
• **Status:** {'✅ Active' if LOG_CHANNEL else '❌ Disabled'}

**How it works:**
• When enabled, all downloaded content is sent to the log channel
• Content includes metadata (requester, timestamp, etc.)
• If disabled, content is sent directly to users

**Setup Instructions:**
1. Create a private channel
2. Add your bot as admin with 'Post Messages' permission
3. Set LOG_CHANNEL environment variable to channel ID
4. Optionally set LOG_CHANNEL_USERNAME for display

**Channel ID Format:**
• Use channel ID: `-1001234567890`
• Or use @username: `@your_channel`
"""
    
    await message.reply_text(status_text)

@Client.on_message(filters.private & filters.command(["test_channel"]) & filters.user(ADMINS))
async def test_channel(client: Client, message: Message):
    """Test log channel functionality"""
    if not LOG_CHANNEL:
        return await message.reply_text("**❌ Log channel is not configured. Set LOG_CHANNEL environment variable.**")
    
    try:
        test_message = f"""
🧪 **Channel Test Message**

**Bot Status:** ✅ Online
**Channel:** {LOG_CHANNEL}
**Username:** {LOG_CHANNEL_USERNAME if LOG_CHANNEL_USERNAME else 'Not set'}
**Test Time:** {message.date}

This is a test message to verify the log channel is working correctly.
"""
        
        await client.send_message(LOG_CHANNEL, test_message, parse_mode="html")
        await message.reply_text("**✅ Test message sent to log channel successfully!**")
        
    except Exception as e:
        await message.reply_text(f"**❌ Failed to send test message:** {str(e)}")

@Client.on_message(filters.private & filters.command(["channel_stats"]))
async def channel_stats(client: Client, message: Message):
    """Show channel usage statistics"""
    user_id = message.from_user.id
    
    # Get user activity
    activity = security_manager.user_activity.get(user_id, {})
    request_count = activity.get('request_count', 0)
    
    stats_text = f"""
📊 **Channel Usage Statistics**

**Your Activity:**
• **Total Requests:** {request_count}
• **Channel Target:** {'Log Channel' if LOG_CHANNEL else 'Direct to You'}

**System Status:**
• **Log Channel:** {'✅ Active' if LOG_CHANNEL else '❌ Disabled'}
• **Parallel Processing:** {'✅ Enabled' if security_manager.PARALLEL_PROCESSING else '❌ Disabled'}

**Performance:**
• **Max Concurrent Downloads:** {security_manager.MAX_CONCURRENT_DOWNLOADS}
• **Max Concurrent Uploads:** {security_manager.MAX_CONCURRENT_UPLOADS}

**Benefits of Log Channel:**
• 🚀 Faster processing (no individual forwarding)
• 📁 Centralized content storage
• 📊 Better organization and management
• ⚡ Reduced bot load
"""
    
    await message.reply_text(stats_text)

@Client.on_message(filters.private & filters.command(["setup_channel"]))
async def setup_channel_guide(client: Client, message: Message):
    """Guide for setting up log channel"""
    guide_text = """
📺 **Log Channel Setup Guide**

**Step 1: Create Channel**
1. Open Telegram
2. Create a new channel
3. Make it private (recommended)
4. Add a descriptive name

**Step 2: Add Bot as Admin**
1. Go to channel settings
2. Add administrators
3. Add your bot (@your_bot_username)
4. Give these permissions:
   ✅ Post Messages
   ✅ Edit Messages
   ✅ Delete Messages

**Step 3: Get Channel ID**
1. Forward any message from your channel to @userinfobot
2. Copy the channel ID (starts with -100)
3. Or use @username format

**Step 4: Configure Environment**
Add to your Render environment variables:
```
LOG_CHANNEL=-1001234567890
LOG_CHANNEL_USERNAME=your_channel_name
```

**Step 5: Test**
Use `/test_channel` command to verify setup

**Benefits:**
• All content goes to one place
• Faster processing
• Better organization
• Reduced bot load
"""
    
    await message.reply_text(guide_text)
