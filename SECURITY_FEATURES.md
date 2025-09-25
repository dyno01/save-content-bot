# 🔒 Security Features - VJ Save Restricted Content Bot

## Overview

This bot now includes comprehensive security measures to protect user accounts and prevent abuse. All security features are designed to maintain user privacy while ensuring safe operation.

## 🛡️ Security Features Implemented

### 1. **Rate Limiting** ⏱️
- **Purpose**: Prevents spam and abuse
- **Default**: 20 requests per 5 minutes per user
- **Configurable**: Set `MAX_REQUESTS_PER_WINDOW` and `RATE_LIMIT_WINDOW`
- **Action**: Temporary blocking with clear error messages

### 2. **Session Timeout** ⏰
- **Purpose**: Automatic logout for inactive users
- **Default**: 1 hour (3600 seconds)
- **Configurable**: Set `SESSION_TIMEOUT` environment variable
- **Action**: Forces re-login after timeout

### 3. **Batch Size Limits** 📊
- **Purpose**: Prevents server overload and abuse
- **Default**: Maximum 100 messages per batch
- **Configurable**: Set `MAX_BATCH_SIZE` environment variable
- **Action**: Rejects oversized batches with warning

### 4. **Input Validation** ✅
- **Purpose**: Prevents malicious input and injection attacks
- **Checks**: Length limits, suspicious patterns, format validation
- **Action**: Rejects invalid input with clear error messages

### 5. **Session Validation** 🔐
- **Purpose**: Ensures user sessions are still valid
- **Checks**: Telegram API validation, session expiration
- **Action**: Forces re-login if session is invalid

### 6. **Activity Monitoring** 📈
- **Purpose**: Tracks user behavior for security analysis
- **Tracks**: Login attempts, request patterns, suspicious activities
- **Action**: Logs events and can trigger warnings

### 7. **Security Logging** 📝
- **Purpose**: Audit trail for security events
- **Logs**: Login attempts, rate limits, suspicious activities
- **Action**: Records all security-related events

## 🔧 New Commands

### `/security` - Security Status
Shows your current security status including:
- Session expiration time
- Request count
- Suspicious activity count
- Rate limit status
- Security settings

### `/force_logout` - Emergency Logout
Immediately logs out all sessions for security:
- Clears all security data
- Removes session from database
- Forces re-login

### Admin Commands (Admin Only)

#### `/security_reset` - Reset User Security
Resets security data for a specific user:
- Reply to user's message
- Clears rate limits and activity data
- Admin only command

#### `/security_logs` - View Security Logs
Shows recent security events (coming soon)

## ⚙️ Environment Variables

Add these to your Render environment variables:

```bash
# Security Configuration
MAX_BATCH_SIZE=100                    # Maximum messages per batch
SESSION_TIMEOUT=3600                  # Session timeout in seconds (1 hour)
RATE_LIMIT_WINDOW=300                 # Rate limit window in seconds (5 minutes)
MAX_REQUESTS_PER_WINDOW=20            # Max requests per window
MAX_FILE_SIZE=2097152000              # Maximum file size (2GB)
```

## 🚨 Security Warnings

The bot will show warnings for:

1. **High Suspicious Activity** (5+ events)
   - "⚠️ High suspicious activity detected. Your account may be temporarily restricted."

2. **Suspicious Activity** (3+ events)
   - "⚠️ Suspicious activity detected. Please use the bot responsibly."

3. **Large Batch Detection** (50+ messages)
   - "⚠️ Large batch detected (X messages). This may take a while."

4. **Rate Limit Exceeded**
   - "⚠️ Rate limit exceeded. Please wait before making more requests."

## 🔍 What Gets Tracked

### User Activity
- Login/logout events
- Request frequency
- Batch sizes
- Session duration
- Error patterns

### Suspicious Activities
- Large batch requests
- Rapid successive requests
- Invalid input attempts
- Multiple login attempts

### Security Events
- Rate limit violations
- Session timeouts
- Invalid sessions
- Admin actions

## 🛠️ How It Works

### 1. **Request Flow**
```
User Request → Rate Limit Check → Input Validation → Security Check → Process → Log Event
```

### 2. **Session Management**
```
Login → Session Validation → Activity Tracking → Timeout Check → Auto Logout
```

### 3. **Batch Processing**
```
Batch Request → Size Validation → Security Check → Process with Limits → Completion Log
```

## 🔒 Privacy & Data Protection

### What's Stored
- **Session strings**: Encrypted in database
- **Activity data**: Temporary in memory only
- **Security logs**: Timestamped events only

### What's NOT Stored
- **Personal messages**: Not logged
- **File contents**: Not stored
- **User conversations**: Not recorded

### Data Retention
- **Sessions**: Until user logs out or timeout
- **Activity data**: Cleared on logout
- **Security logs**: Configurable retention

## 🚀 Benefits

### For Users
- **Account Protection**: Automatic session management
- **Abuse Prevention**: Rate limiting prevents spam
- **Transparency**: Clear security status and warnings
- **Control**: Force logout option for security

### For Admins
- **Monitoring**: Security event logging
- **Control**: User security management
- **Protection**: Server resource protection
- **Compliance**: Audit trail for security events

## ⚠️ Important Notes

1. **Session Security**: Never share your login session with others
2. **Rate Limits**: Respect the rate limits to avoid temporary blocks
3. **Batch Sizes**: Keep batch sizes reasonable to avoid timeouts
4. **Logout**: Use `/force_logout` if you suspect unauthorized access
5. **Admin Access**: Only trusted users should have admin privileges

## 🔧 Customization

### Adjusting Limits
Modify environment variables to suit your needs:

```bash
# More restrictive (higher security)
MAX_BATCH_SIZE=50
SESSION_TIMEOUT=1800
MAX_REQUESTS_PER_WINDOW=10

# Less restrictive (higher usability)
MAX_BATCH_SIZE=200
SESSION_TIMEOUT=7200
MAX_REQUESTS_PER_WINDOW=50
```

### Monitoring
- Check Render logs for security events
- Monitor user activity patterns
- Review rate limit violations
- Track suspicious activity trends

## 📞 Support

If you encounter security issues:
1. Check your security status with `/security`
2. Use `/force_logout` if needed
3. Contact admin if problems persist
4. Check server logs for detailed information

---

**Remember**: These security features are designed to protect you and the bot. They may occasionally cause minor inconveniences, but they significantly improve overall security and stability. 🔒
