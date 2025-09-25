import os
import sys

# Bot token @Botfather
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# Your API ID from my.telegram.org
API_ID = os.environ.get("API_ID", "")
if API_ID:
    API_ID = int(API_ID)

# Your API Hash from my.telegram.org
API_HASH = os.environ.get("API_HASH", "")

# Your Owner / Admin Id For Broadcast 
ADMINS = os.environ.get("ADMINS", "2031933716")
if ADMINS:
    ADMINS = int(ADMINS)

# Your Mongodb Database Url
# Warning - Give Db uri in deploy server environment variable, don't give in repo.
DB_URI = os.environ.get("DB_URI", "") # Warning - Give Db uri in deploy server environment variable, don't give in repo.
DB_NAME = os.environ.get("DB_NAME", "vjsavecontentbot")

# If You Want Error Message In Your Personal Message Then Turn It True Else If You Don't Want Then Flase
ERROR_MESSAGE = os.environ.get('ERROR_MESSAGE', 'True').lower() in ('true', '1', 'yes', 'on')

# Content Delivery: Direct to User Chat (Log Channel removed for simplicity)

# Performance Configuration
MAX_CONCURRENT_DOWNLOADS = int(os.environ.get('MAX_CONCURRENT_DOWNLOADS', '5'))
MAX_CONCURRENT_UPLOADS = int(os.environ.get('MAX_CONCURRENT_UPLOADS', '3'))
PARALLEL_PROCESSING = os.environ.get('PARALLEL_PROCESSING', 'True').lower() in ('true', '1', 'yes', 'on')

# Validate required environment variables
required_vars = ['BOT_TOKEN', 'API_ID', 'API_HASH', 'DB_URI']
missing_vars = [var for var in required_vars if not os.environ.get(var)]

if missing_vars:
    print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
    print("Please set these environment variables in your Render dashboard.")
    sys.exit(1)
