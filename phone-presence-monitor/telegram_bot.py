#!/usr/bin/env python3
"""
Telegram Bot with commands for presence monitor.
"""

import urllib.request
import urllib.parse
import json
import threading
import time
from typing import Callable, Optional
from datetime import datetime, timedelta
import csv
from pathlib import Path


class TelegramBot:
    """Telegram bot that handles commands."""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.last_update_id = 0
        self.running = False
        self.commands = {}
        self.log_file = Path(__file__).parent / "logs" / "presence_history.csv"
    
    def register_command(self, command: str, handler: Callable):
        """Register a command handler."""
        self.commands[command] = handler
    
    def send_message(self, message: str, parse_mode: str = "HTML") -> bool:
        """Send a message to the configured chat."""
        url = f"{self.base_url}/sendMessage"
        data = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": parse_mode
        }
        
        try:
            encoded_data = urllib.parse.urlencode(data).encode('utf-8')
            request = urllib.request.Request(url, data=encoded_data, method='POST')
            with urllib.request.urlopen(request, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result.get("ok", False)
        except Exception as e:
            print(f"Failed to send message: {e}")
            return False
    
    def get_updates(self) -> list:
        """Get new messages from Telegram."""
        url = f"{self.base_url}/getUpdates"
        params = {
            "offset": self.last_update_id + 1,
            "timeout": 5
        }
        
        try:
            full_url = f"{url}?{urllib.parse.urlencode(params)}"
            request = urllib.request.Request(full_url)
            with urllib.request.urlopen(request, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                if result.get("ok"):
                    return result.get("result", [])
        except Exception:
            pass
        return []
    
    def process_updates(self, get_status_func: Callable = None):
        """Process incoming messages and handle commands."""
        updates = self.get_updates()
        
        for update in updates:
            self.last_update_id = update.get("update_id", self.last_update_id)
            message = update.get("message", {})
            text = message.get("text", "")
            chat_id = str(message.get("chat", {}).get("id", ""))
            
            # Only respond to our chat
            if chat_id != self.chat_id:
                continue
            
            if text.startswith("/"):
                self._handle_command(text, get_status_func)
    
    def _handle_command(self, text: str, get_status_func: Callable = None):
        """Handle a bot command."""
        parts = text.split()
        command = parts[0].lower().replace("@", " ").split()[0]  # Remove @botname
        
        if command == "/status":
            self._cmd_status(get_status_func)
        elif command == "/stats":
            self._cmd_stats()
        elif command == "/today":
            self._cmd_today()
        elif command == "/week":
            self._cmd_week()
        elif command == "/help":
            self._cmd_help()
        elif command == "/devices":
            self._cmd_devices(get_status_func)
    
    def _cmd_help(self):
        """Show help message."""
        msg = (
            "📱 <b>Phone Presence Monitor</b>\n\n"
            "<b>Commands:</b>\n"
            "/status - Current status of all devices\n"
            "/devices - List monitored devices\n"
            "/stats - Overall statistics\n"
            "/today - Today's activity\n"
            "/week - This week's summary\n"
            "/help - Show this help"
        )
        self.send_message(msg)
    
    def _cmd_status(self, get_status_func: Callable = None):
        """Show current device status."""
        if get_status_func:
            statuses = get_status_func()
            lines = ["📱 <b>Current Device Status</b>\n"]
            for name, is_present in statuses.items():
                icon = "🟢" if is_present else "🔴"
                status = "Online" if is_present else "Offline"
                lines.append(f"{icon} {name}: {status}")
            self.send_message("\n".join(lines))
        else:
            self.send_message("❌ Status not available")
    
    def _cmd_devices(self, get_status_func: Callable = None):
        """List all monitored devices."""
        from config import DEVICES
        lines = ["📋 <b>Monitored Devices</b>\n"]
        for dev in DEVICES:
            notify = "🔔" if dev.get("notify") else "🔕"
            lines.append(f"{notify} {dev['name']} ({dev['ip']})")
        lines.append("\n🔔 = Telegram notifications enabled")
        self.send_message("\n".join(lines))
    
    def _cmd_stats(self):
        """Show overall statistics."""
        stats = self._get_stats()
        if not stats:
            self.send_message("📊 No data yet. Check back later!")
            return
        
        msg = (
            f"📊 <b>Presence Statistics</b>\n\n"
            f"Total events: {stats['total_events']}\n"
            f"Arrivals: {stats['arrivals']}\n"
            f"Departures: {stats['departures']}\n"
            f"Days tracked: {stats['days_tracked']}\n"
            f"Unique devices: {stats['unique_devices']}"
        )
        self.send_message(msg)
    
    def _cmd_today(self):
        """Show today's activity."""
        today = datetime.now().strftime('%Y-%m-%d')
        events = self._get_events_for_date(today)
        
        if not events:
            self.send_message(f"📅 No activity recorded today ({today})")
            return
        
        lines = [f"📅 <b>Today's Activity</b> ({today})\n"]
        for event in events[-15:]:  # Last 15 events
            icon = "🟢" if event['event'] == 'arrived' else "🔴"
            lines.append(f"{icon} {event['time']} - {event['phone_name']}")
        
        if len(events) > 15:
            lines.append(f"\n... and {len(events) - 15} more events")
        
        self.send_message("\n".join(lines))
    
    def _cmd_week(self):
        """Show this week's summary."""
        week_stats = self._get_week_stats()
        
        if not week_stats:
            self.send_message("📅 No data for this week yet.")
            return
        
        lines = ["📅 <b>This Week's Summary</b>\n"]
        for day, stats in week_stats.items():
            lines.append(f"<b>{day}</b>: {stats['arrivals']}↑ {stats['departures']}↓")
        
        self.send_message("\n".join(lines))
    
    def _get_stats(self) -> dict:
        """Get overall statistics from log file."""
        if not self.log_file.exists():
            return {}
        
        arrivals = 0
        departures = 0
        days = set()
        devices = set()
        
        try:
            with open(self.log_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['event'] == 'arrived':
                        arrivals += 1
                    elif row['event'] == 'left':
                        departures += 1
                    days.add(row['date'])
                    devices.add(row['phone_name'])
        except Exception:
            return {}
        
        return {
            'total_events': arrivals + departures,
            'arrivals': arrivals,
            'departures': departures,
            'days_tracked': len(days),
            'unique_devices': len(devices)
        }
    
    def _get_events_for_date(self, date: str) -> list:
        """Get events for a specific date."""
        if not self.log_file.exists():
            return []
        
        events = []
        try:
            with open(self.log_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['date'] == date:
                        events.append(row)
        except Exception:
            pass
        
        return events
    
    def _get_week_stats(self) -> dict:
        """Get stats for the past 7 days."""
        if not self.log_file.exists():
            return {}
        
        # Get last 7 days
        dates = {}
        for i in range(7):
            d = datetime.now() - timedelta(days=i)
            date_str = d.strftime('%Y-%m-%d')
            day_name = d.strftime('%a %d')
            dates[date_str] = {'day_name': day_name, 'arrivals': 0, 'departures': 0}
        
        try:
            with open(self.log_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['date'] in dates:
                        if row['event'] == 'arrived':
                            dates[row['date']]['arrivals'] += 1
                        elif row['event'] == 'left':
                            dates[row['date']]['departures'] += 1
        except Exception:
            pass
        
        # Convert to ordered dict by day name
        result = {}
        for date_str in sorted(dates.keys(), reverse=True):
            info = dates[date_str]
            if info['arrivals'] > 0 or info['departures'] > 0:
                result[info['day_name']] = info
        
        return result
