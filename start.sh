#!/bin/bash

# Start script for VJ Save Restricted Content Bot
echo "Starting VJ Save Restricted Content Bot..."

# Check if required environment variables are set
if [ -z "$BOT_TOKEN" ]; then
    echo "Error: BOT_TOKEN environment variable is not set"
    exit 1
fi

if [ -z "$API_ID" ]; then
    echo "Error: API_ID environment variable is not set"
    exit 1
fi

if [ -z "$API_HASH" ]; then
    echo "Error: API_HASH environment variable is not set"
    exit 1
fi

if [ -z "$DB_URI" ]; then
    echo "Error: DB_URI environment variable is not set"
    exit 1
fi

echo "All required environment variables are set. Starting bot..."
python3 bot.py
