"""
Configuration for Phone Presence Monitor

You need to:
1. Create a Telegram bot via @BotFather and get the token
2. Get your chat ID by messaging @userinfobot or @get_id_bot
3. Copy this file to config.py and fill in your values
"""

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID_HERE"

# Auto-discovery mode: fetch devices from VOO router
# If True, devices are fetched from router API
# If False, only DEVICES list below is monitored
AUTO_DISCOVER = True

# How often to refresh device list from router (in seconds)
# Router is queried every ROUTER_REFRESH_INTERVAL seconds
ROUTER_REFRESH_INTERVAL = 300  # 5 minutes

# Devices that trigger Telegram notifications (matched by name substring)
# Only these devices will send you Telegram alerts when they arrive/leave
# All other devices are still logged to CSV for statistics
NOTIFY_PATTERNS = ["Redmi"]

# Static devices to always monitor (in addition to auto-discovered ones)
# Format: {"name": "...", "ip": "...", "notify": True/False}
STATIC_DEVICES = [
    # Add any devices you always want to track even if router doesn't report them
]

# Legacy: Manual device list (used if AUTO_DISCOVER = False)
DEVICES = [
    {"name": "Phone 1", "ip": "192.168.0.100", "notify": True},
    {"name": "Phone 2", "ip": "192.168.0.101", "notify": False},
]

# Check interval in seconds (how often to ping devices)
CHECK_INTERVAL = 30

# Ping timeout in seconds
PING_TIMEOUT = 2

# Number of ping attempts before declaring absent
PING_ATTEMPTS = 3
