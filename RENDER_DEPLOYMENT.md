# VJ Save Restricted Content Bot - Render Deployment Guide

This guide will help you deploy the VJ Save Restricted Content Bot on Render.com.

## Prerequisites

1. A Render.com account
2. Telegram Bot Token from [@BotFather](https://t.me/BotFather)
3. Telegram API ID and API Hash from [my.telegram.org](https://my.telegram.org)
4. MongoDB database (MongoDB Atlas recommended)

## Step 1: Prepare Your Repository

1. Fork this repository to your GitHub account
2. Make sure all files are committed and pushed to your repository

## Step 2: Create a New Web Service on Render

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New +" and select "Web Service"
3. Connect your GitHub account and select this repository
4. Configure the service:
   - **Name**: `vj-save-restricted-bot` (or any name you prefer)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Plan**: Choose your preferred plan (Free tier available)

## Step 3: Set Environment Variables

In your Render service dashboard, go to "Environment" tab and add these variables:

### Required Variables:
- `BOT_TOKEN`: Your bot token from @BotFather
- `API_ID`: Your Telegram API ID (number)
- `API_HASH`: Your Telegram API Hash (string)
- `DB_URI`: Your MongoDB connection string
- `ADMINS`: Your Telegram user ID (number)

### Optional Variables:
- `DB_NAME`: Database name (default: `vjsavecontentbot`)
- `ERROR_MESSAGE`: Set to `True` or `False` (default: `True`)

## Step 4: Create a Background Worker

1. Go back to Render Dashboard
2. Click "New +" and select "Background Worker"
3. Connect the same repository
4. Configure:
   - **Name**: `vj-bot-worker`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python bot.py`
   - **Plan**: Choose your preferred plan

## Step 5: Set Environment Variables for Worker

Add the same environment variables to your background worker as you did for the web service.

## Step 6: Deploy

1. Click "Create Web Service" and "Create Background Worker"
2. Wait for the deployment to complete
3. Check the logs to ensure everything is working correctly

## Environment Variables Reference

| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `BOT_TOKEN` | Telegram bot token from @BotFather | Yes | `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz` |
| `API_ID` | Telegram API ID from my.telegram.org | Yes | `1234567` |
| `API_HASH` | Telegram API Hash from my.telegram.org | Yes | `abcdef1234567890abcdef1234567890` |
| `DB_URI` | MongoDB connection string | Yes | `mongodb+srv://user:pass@cluster.mongodb.net/` |
| `ADMINS` | Your Telegram user ID | Yes | `123456789` |
| `DB_NAME` | Database name | No | `vjsavecontentbot` |
| `ERROR_MESSAGE` | Show error messages to users | No | `True` or `False` |

## Getting Your Telegram Credentials

### Bot Token:
1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot` and follow the instructions
3. Copy the bot token

### API ID and API Hash:
1. Go to [my.telegram.org](https://my.telegram.org)
2. Log in with your phone number
3. Go to "API development tools"
4. Create a new application
5. Copy the API ID and API Hash

### Your User ID:
1. Message [@userinfobot](https://t.me/userinfobot) on Telegram
2. It will reply with your user ID

## MongoDB Setup

### Using MongoDB Atlas (Recommended):
1. Go to [MongoDB Atlas](https://www.mongodb.com/atlas)
2. Create a free account and cluster
3. Create a database user
4. Get the connection string
5. Replace `<password>` with your actual password

### Connection String Format:
```
mongodb+srv://<username>:<password>@<cluster-url>/<database-name>?retryWrites=true&w=majority
```

## Bot Commands

Once deployed, your bot will support these commands:

- `/start` - Check if bot is working
- `/help` - Show help message
- `/login` - Login with your Telegram session
- `/logout` - Logout from your session
- `/cancel` - Cancel any ongoing task
- `/broadcast` - Broadcast message to users (Admin only)

## Usage

### For Public Chats:
Just send the post link

### For Private Chats:
1. First send the invite link of the chat (if not already a member)
2. Then send the post link

### For Bot Chats:
Send link with format: `https://t.me/b/botusername/4321`

### Multiple Posts:
Send links with format: `https://t.me/xxxx/1001-1010`

## Troubleshooting

### Common Issues:

1. **Bot not responding**: Check if both web service and background worker are running
2. **Database connection error**: Verify your MongoDB URI is correct
3. **API errors**: Ensure your API_ID and API_HASH are correct
4. **Permission errors**: Make sure your bot has necessary permissions

### Checking Logs:
1. Go to your Render service dashboard
2. Click on "Logs" tab
3. Check for any error messages

## Support

If you encounter any issues:
1. Check the logs in Render dashboard
2. Verify all environment variables are set correctly
3. Ensure your MongoDB database is accessible
4. Make sure your Telegram bot token is valid

## Credits

- Original repository: [VJBots/VJ-Save-Restricted-Content](https://github.com/VJBots/VJ-Save-Restricted-Content)
- Modified by: [dyno01](https://github.com/dyno01)
- YouTube: [@Tech_VJ](https://youtube.com/@Tech_VJ)
