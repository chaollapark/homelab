"""
Telegram notification module for sending presence alerts.
"""

import urllib.request
import urllib.parse
import json
from typing import Optional


class TelegramNotifier:
    """Sends notifications via Telegram Bot API."""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
    
    def send_message(self, message: str) -> bool:
        """Send a message to the configured chat."""
        url = f"{self.base_url}/sendMessage"
        data = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        
        try:
            encoded_data = urllib.parse.urlencode(data).encode('utf-8')
            request = urllib.request.Request(url, data=encoded_data, method='POST')
            
            with urllib.request.urlopen(request, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result.get("ok", False)
        except Exception as e:
            print(f"Failed to send Telegram message: {e}")
            return False
    
    def send_phone_arrived(self, phone_name: str, ip: str) -> bool:
        """Send notification that phone has arrived on network."""
        message = (
            f"📱 <b>Phone Arrived!</b>\n\n"
            f"🟢 <b>{phone_name}</b>\n"
            f"IP: <code>{ip}</code>\n"
            f"Status: Connected to network"
        )
        return self.send_message(message)
    
    def send_phone_left(self, phone_name: str, ip: str) -> bool:
        """Send notification that phone has left the network."""
        message = (
            f"📱 <b>Phone Left!</b>\n\n"
            f"🔴 <b>{phone_name}</b>\n"
            f"IP: <code>{ip}</code>\n"
            f"Status: Disconnected from network"
        )
        return self.send_message(message)


def test_connection(bot_token: str, chat_id: str) -> bool:
    """Test if the Telegram bot configuration is working."""
    notifier = TelegramNotifier(bot_token, chat_id)
    return notifier.send_message("🔔 Phone Presence Monitor is now active!")
