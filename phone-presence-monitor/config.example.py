"""
Configuration for Phone Presence Monitor

Copy this file to config.py and fill in your details.
"""

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # Get from @BotFather
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID_HERE"      # Get from @userinfobot

# Auto-discovery mode: fetch devices from VOO router
AUTO_DISCOVER = True

# How often to refresh device list from router (in seconds)
ROUTER_REFRESH_INTERVAL = 300  # 5 minutes

# Devices that trigger Telegram notifications (matched by name substring)
NOTIFY_PATTERNS = ["Redmi", "iPhone"]

# Static devices to always monitor
STATIC_DEVICES = []

# Legacy manual device list (used if AUTO_DISCOVER = False)
DEVICES = []

# Check interval in seconds
CHECK_INTERVAL = 30

# Ping settings (only used if not using router API)
PING_TIMEOUT = 2
PING_ATTEMPTS = 3
