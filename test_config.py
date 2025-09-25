#!/usr/bin/env python3
"""
Test script to verify configuration and dependencies
"""

import sys
import os

def test_imports():
    """Test if all required packages can be imported"""
    try:
        import pyrogram
        print("✓ Pyrogram imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import pyrogram: {e}")
        return False
    
    try:
        import tgcrypto
        print("✓ TgCrypto imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import tgcrypto: {e}")
        return False
    
    try:
        import motor
        print("✓ Motor imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import motor: {e}")
        return False
    
    try:
        import flask
        print("✓ Flask imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import flask: {e}")
        return False
    
    return True

def test_config():
    """Test configuration loading"""
    try:
        from config import BOT_TOKEN, API_ID, API_HASH, DB_URI, ADMINS
        print("✓ Configuration loaded successfully")
        
        if not BOT_TOKEN:
            print("⚠ BOT_TOKEN is not set")
        else:
            print("✓ BOT_TOKEN is set")
            
        if not API_ID:
            print("⚠ API_ID is not set")
        else:
            print("✓ API_ID is set")
            
        if not API_HASH:
            print("⚠ API_HASH is not set")
        else:
            print("✓ API_HASH is set")
            
        if not DB_URI:
            print("⚠ DB_URI is not set")
        else:
            print("✓ DB_URI is set")
            
        return True
    except Exception as e:
        print(f"✗ Failed to load configuration: {e}")
        return False

def main():
    print("Testing VJ Save Restricted Content Bot configuration...")
    print("=" * 50)
    
    # Test imports
    print("\n1. Testing imports:")
    imports_ok = test_imports()
    
    # Test configuration
    print("\n2. Testing configuration:")
    config_ok = test_config()
    
    print("\n" + "=" * 50)
    if imports_ok and config_ok:
        print("✓ All tests passed! Bot is ready for deployment.")
        return 0
    else:
        print("✗ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
