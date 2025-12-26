#!/usr/bin/env python3
"""
Telegram Bot with commands for presence monitor and router control.
"""

import urllib.request
import urllib.parse
import json
import logging
from typing import Callable, Optional
from datetime import datetime, timedelta
import csv
from pathlib import Path


# Setup logging for telegram commands
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
CMD_LOG_FILE = LOG_DIR / "telegram_commands.log"

logging.basicConfig(level=logging.INFO)
cmd_logger = logging.getLogger("telegram_commands")
cmd_handler = logging.FileHandler(CMD_LOG_FILE)
cmd_handler.setFormatter(logging.Formatter(
    '%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
))
cmd_logger.addHandler(cmd_handler)


class TelegramBot:
    """Telegram bot that handles commands."""
    
    def __init__(self, bot_token: str, chat_id: str, router_session=None):
        """Initialize Telegram bot.
        
        Args:
            bot_token: Telegram bot token
            chat_id: Telegram chat ID to respond to
            router_session: Optional shared router session to avoid session conflicts
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.last_update_id = 0
        self.running = False
        self.log_file = Path(__file__).parent / "logs" / "presence_history.csv"
        self.router_controller = None
        self._router_session = router_session
        self._init_router_controller(router_session)
    
    def _init_router_controller(self, router_session=None):
        """Initialize router controller for block/kick commands."""
        try:
            from router_control import RouterController
            self.router_controller = RouterController(shared_session=router_session)
        except Exception as e:
            print(f"Router controller not available: {e}")
    
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
        args = parts[1:] if len(parts) > 1 else []
        
        # Log the command
        cmd_logger.info(f"CMD: {command} {' '.join(args) if args else ''}")
        
        # Presence monitor commands
        if command == "/status":
            self._cmd_status(get_status_func)
        elif command == "/stats":
            self._cmd_stats()
        elif command == "/today":
            self._cmd_today()
        elif command == "/week":
            self._cmd_week()
        elif command == "/devices":
            self._cmd_devices(get_status_func)
        elif command == "/help":
            self._cmd_help()
        
        # Router control commands
        elif command == "/block":
            self._cmd_block(args)
        elif command == "/unblock":
            self._cmd_unblock(args)
        elif command == "/blocklist":
            self._cmd_blocklist()
        elif command == "/kick":
            self._cmd_kick(args)
        elif command == "/allow":
            self._cmd_allow(args)
        elif command == "/banned":
            self._cmd_banned()
        elif command == "/wifi":
            self._cmd_wifi(args)
        elif command == "/lockdown":
            self._cmd_lockdown(args)
    
    # ==================== HELP ====================
    
    def _cmd_help(self):
        """Show help message."""
        msg = (
            "📱 <b>Phone Presence Monitor</b>\n\n"
            "<b>📊 Status Commands:</b>\n"
            "/status - Current device status\n"
            "/devices - List all devices\n"
            "/stats - Overall statistics\n"
            "/today - Today's activity\n"
            "/week - This week's summary\n\n"
            "<b>🌐 Site Blocking:</b>\n"
            "/block &lt;site&gt; - Block a website\n"
            "/unblock &lt;site&gt; - Unblock a website\n"
            "/blocklist - Show blocked sites\n\n"
            "<b>📵 Device Control:</b>\n"
            "/kick &lt;device&gt; - Kick device off network\n"
            "/allow &lt;device&gt; - Allow device back\n"
            "/banned - Show banned devices\n"
            "/wifi off - Turn OFF all WiFi\n"
            "/wifi on - Turn ON all WiFi\n\n"
            "<b>🔒 Lockdown:</b>\n"
            "/lockdown on - Block ALL except homelab\n"
            "/lockdown off - Unblock all devices\n\n"
            "/help - Show this help"
        )
        self.send_message(msg)
    
    # ==================== PRESENCE COMMANDS ====================
    
    def _cmd_status(self, get_status_func: Callable = None):
        """Show current device status."""
        if get_status_func:
            statuses = get_status_func()
            online = [(n, s) for n, s in statuses.items() if s]
            offline = [(n, s) for n, s in statuses.items() if not s]
            
            lines = [f"📱 <b>Device Status</b> ({len(online)}/{len(statuses)} online)\n"]
            
            if online:
                lines.append("<b>🟢 Online:</b>")
                for name, _ in sorted(online)[:15]:
                    lines.append(f"  • {name}")
                if len(online) > 15:
                    lines.append(f"  ... and {len(online) - 15} more")
            
            if offline and len(offline) <= 10:
                lines.append("\n<b>🔴 Offline:</b>")
                for name, _ in sorted(offline):
                    lines.append(f"  • {name}")
            
            self.send_message("\n".join(lines))
        else:
            self.send_message("❌ Status not available")
    
    def _cmd_devices(self, get_status_func: Callable = None):
        """List all monitored devices."""
        if get_status_func:
            statuses = get_status_func()
            lines = [f"📋 <b>All Devices</b> ({len(statuses)} total)\n"]
            for name, is_online in sorted(statuses.items()):
                icon = "🟢" if is_online else "🔴"
                lines.append(f"{icon} {name}")
            self.send_message("\n".join(lines[:50]))  # Limit to 50
        else:
            self.send_message("❌ Device list not available")
    
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
        for event in events[-15:]:
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
    
    # ==================== SITE BLOCKING COMMANDS ====================
    
    def _cmd_block(self, args: list):
        """Block a website."""
        if not self.router_controller:
            self.send_message("❌ Router control not available")
            return
        
        if not args:
            self.send_message("Usage: /block &lt;website&gt;\nExample: /block facebook.com")
            return
        
        site = args[0].lower().strip()
        success, message = self.router_controller.block_site(site)
        cmd_logger.info(f"BLOCK site={site} success={success} msg={message}")
        self.send_message(message)
    
    def _cmd_unblock(self, args: list):
        """Unblock a website."""
        if not self.router_controller:
            self.send_message("❌ Router control not available")
            return
        
        if not args:
            self.send_message("Usage: /unblock &lt;website&gt;\nExample: /unblock facebook.com")
            return
        
        site = args[0].lower().strip()
        success, message = self.router_controller.unblock_site(site)
        cmd_logger.info(f"UNBLOCK site={site} success={success} msg={message}")
        self.send_message(message)
    
    def _cmd_blocklist(self):
        """Show blocked websites."""
        if not self.router_controller:
            self.send_message("❌ Router control not available")
            return
        
        success, sites = self.router_controller.get_blocked_sites()
        
        if not success:
            self.send_message("❌ Failed to get blocked sites")
            return
        
        if not sites:
            self.send_message("🌐 <b>Blocked Sites</b>\n\nNo sites are currently blocked.")
            return
        
        lines = [f"🌐 <b>Blocked Sites</b> ({len(sites)})\n"]
        for site in sites:
            lines.append(f"🚫 {site}")
        
        self.send_message("\n".join(lines))
    
    # ==================== DEVICE CONTROL COMMANDS ====================
    
    def _cmd_kick(self, args: list):
        """Kick a device off the network."""
        if not self.router_controller:
            self.send_message("❌ Router control not available")
            return
        
        if not args:
            self.send_message("Usage: /kick &lt;device_name&gt;\nExample: /kick Samsung")
            return
        
        device = " ".join(args)
        success, message = self.router_controller.kick_device(device)
        cmd_logger.info(f"KICK device={device} success={success} msg={message}")
        self.send_message(message)
    
    def _cmd_allow(self, args: list):
        """Allow a device back on the network."""
        if not self.router_controller:
            self.send_message("❌ Router control not available")
            return
        
        if not args:
            self.send_message("Usage: /allow &lt;device_name&gt;\nExample: /allow Samsung")
            return
        
        device = " ".join(args)
        success, message = self.router_controller.allow_device(device)
        cmd_logger.info(f"ALLOW device={device} success={success} msg={message}")
        self.send_message(message)
    
    def _cmd_banned(self):
        """Show banned devices."""
        if not self.router_controller:
            self.send_message("❌ Router control not available")
            return
        
        success, devices = self.router_controller.get_blocked_devices()
        
        if not success:
            self.send_message("❌ Failed to get banned devices")
            return
        
        if not devices:
            self.send_message("📵 <b>Banned Devices</b>\n\nNo devices are currently banned.")
            return
        
        lines = [f"📵 <b>Banned Devices</b> ({len(devices)})\n"]
        for dev in devices:
            name = dev.get('name', 'Unknown')
            mac = dev.get('mac', '')
            lines.append(f"🚫 {name} ({mac})")
        
        self.send_message("\n".join(lines))
    
    def _cmd_wifi(self, args: list):
        """Turn WiFi on/off by blocking/unblocking Archer APs."""
        if not self.router_controller:
            self.send_message("❌ Router control not available")
            return
        
        if not args or args[0].lower() not in ['on', 'off']:
            self.send_message("Usage: /wifi on or /wifi off")
            return
        
        action = args[0].lower()
        
        cmd_logger.info(f"WIFI action={action}")
        # Archer C80 Access Points - MAC addresses
        archer_aps = [
            ('AP1', '60:83:E7:B5:66:22'),
            ('AP2', '60:83:E7:B5:67:5D'),
            ('AP3', '60:83:E7:B5:41:8C'),
            ('AP4', '20:23:51:21:61:9F'),
        ]
        
        results = []
        if action == 'off':
            self.send_message("📡 Blocking all WiFi APs...")
            for name, mac in archer_aps:
                success, msg = self.router_controller.kick_device(mac)
                status = "✓" if success or "already" in msg.lower() else "✗"
                results.append(f"{status} {name}")
            
            msg = "📵 <b>WiFi is now OFF</b>\n\n" + "\n".join(results)
            msg += "\n\n<i>APs still broadcast but no internet</i>"
        else:
            self.send_message("📡 Unblocking all WiFi APs...")
            for name, mac in archer_aps:
                success, msg = self.router_controller.allow_device(mac)
                status = "✓" if success or "not blocked" in msg.lower() else "✗"
                results.append(f"{status} {name}")
            
            msg = "📶 <b>WiFi is now ON</b>\n\n" + "\n".join(results)
        cmd_logger.info(f"WIFI result: {results}")
        
        self.send_message(msg)

    def _cmd_lockdown(self, args: list):
        """Lockdown mode - block all devices except homelab."""
        if not self.router_controller:
            self.send_message("❌ Router control not available")
            return
        
        if not args or args[0].lower() not in ['on', 'off']:
            self.send_message("Usage: /lockdown on or /lockdown off")
            return
        
        action = args[0].lower()
        
        cmd_logger.info(f"LOCKDOWN action={action}")
        # Protected MAC - never block
        PROTECTED_MAC = '3C:07:54:72:71:1A'
        
        rc = self.router_controller
        
        if action == 'on':
            self.send_message("🔒 Activating lockdown...")
            
            # Get all devices
            try:
                resp = rc.session.get(f"{rc.url}/api/v1/host", timeout=10)
                data = resp.json()
                hosts = data.get('data', {}).get('hostTbl', [])
                
                # Build block list
                post_data = {"enable": "true", "allowall": "true"}
                idx = 0
                blocked = []
                
                for h in hosts:
                    mac = h.get('physaddress', '').upper()
                    name = h.get('hostname', 'Unknown')
                    
                    if mac == PROTECTED_MAC.upper():
                        continue
                    
                    post_data[f"macfilterTbl[{idx}][macaddress]"] = mac
                    post_data[f"macfilterTbl[{idx}][description]"] = f"LOCKDOWN: {name}"
                    post_data[f"macfilterTbl[{idx}][type]"] = "Block"
                    post_data[f"macfilterTbl[{idx}][alwaysblock]"] = "true"
                    idx += 1
                    blocked.append(name)
                
                rc.session.post(f"{rc.url}/api/v1/macfilter", data=post_data, timeout=10)
                
                msg = f"🔒 <b>LOCKDOWN ACTIVE</b>\n\n{len(blocked)} devices blocked\n🛡️ Homelab protected"
                self.send_message(msg)
                cmd_logger.info(f"LOCKDOWN ON success=True blocked={len(blocked)}")
            except Exception as e:
                self.send_message(f"❌ Lockdown failed: {e}")
                cmd_logger.error(f"LOCKDOWN ON failed: {e}")
        
        else:  # off
            self.send_message("🔓 Lifting lockdown...")
            try:
                post_data = {"enable": "true", "allowall": "true"}
                rc.session.post(f"{rc.url}/api/v1/macfilter", data=post_data, timeout=10)
                self.send_message("🔓 <b>LOCKDOWN LIFTED</b>\n\nAll devices unblocked")
                cmd_logger.info(f"LOCKDOWN OFF success=True")
            except Exception as e:
                self.send_message(f"❌ Failed to lift lockdown: {e}")
                cmd_logger.error(f"LOCKDOWN OFF failed: {e}")

    # ==================== HELPER METHODS ====================
    
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
        
        result = {}
        for date_str in sorted(dates.keys(), reverse=True):
            info = dates[date_str]
            if info['arrivals'] > 0 or info['departures'] > 0:
                result[info['day_name']] = info
        
        return result
