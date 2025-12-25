#!/usr/bin/env python3
"""
Phone Presence Monitor - Main application

Monitors device presence on the network:
- Uses VOO router API to detect device presence (more reliable than ping)
- Logs ALL device arrivals/departures to CSV
- Sends Telegram notifications only for specified devices (NOTIFY_PATTERNS)
- Provides Telegram bot commands for stats and status
"""

import time
import signal
import sys
from datetime import datetime
from typing import Dict, Set

from config import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    AUTO_DISCOVER,
    ROUTER_REFRESH_INTERVAL,
    NOTIFY_PATTERNS,
    STATIC_DEVICES,
    DEVICES,
    CHECK_INTERVAL,
)
from telegram_notifier import TelegramNotifier
from presence_logger import PresenceLogger
from telegram_bot import TelegramBot


class DeviceTracker:
    """Tracks a single device's presence state."""
    
    def __init__(self, name: str, ip: str, mac: str = "", active: bool = False):
        self.name = name
        self.ip = ip
        self.mac = mac
        self.last_state: bool | None = None
        self.current_state: bool = active
        self.last_seen: datetime | None = None
        self.connection: str = ""
    
    def should_notify(self) -> bool:
        """Check if this device should trigger Telegram notifications."""
        for pattern in NOTIFY_PATTERNS:
            if pattern.lower() in self.name.lower():
                return True
        return False


class RouterBasedMonitor:
    """Monitor that uses router API for presence detection (no ping needed)."""
    
    def __init__(self):
        self.devices: Dict[str, DeviceTracker] = {}  # keyed by MAC
        self.notifier = TelegramNotifier(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
        self.logger = PresenceLogger()
        self.running = False
        self.check_count = 0
        self.router_client = None
        
        # Initialize router client
        try:
            from router_client import VooRouterClient
            self.router_client = VooRouterClient()
        except Exception as e:
            self._log(f"Error: Could not initialize router client: {e}")
            sys.exit(1)
        
        # Login to router first so we have a session to share
        if not self.router_client.login():
            self._log("Warning: Initial router login failed, will retry later")
        
        # Initialize telegram bot with shared router session to avoid session conflicts
        # The router only allows one active session at a time
        router_session = self.router_client.session if self.router_client else None
        self.bot = TelegramBot(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, router_session=router_session)
    
    def _log(self, message: str):
        """Print timestamped log message."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}", flush=True)
    
    def _handle_state_change(self, device: DeviceTracker, is_present: bool):
        """Handle device state change - always log, notify only if matched."""
        # Always log to CSV
        if is_present:
            self._log(f"📱 {device.name} has ARRIVED on the network")
            self.logger.log_arrived(device.name, device.ip)
            device.last_seen = datetime.now()
        else:
            self._log(f"📱 {device.name} has LEFT the network")
            self.logger.log_left(device.name, device.ip)
        
        # Only send Telegram notification if device matches notify patterns
        if device.should_notify():
            if is_present:
                success = self.notifier.send_phone_arrived(device.name, device.ip)
            else:
                success = self.notifier.send_phone_left(device.name, device.ip)
            
            if success:
                self._log("✅ Telegram notification sent")
            else:
                self._log("❌ Failed to send Telegram notification")
    
    def _fetch_and_update_devices(self):
        """Fetch device list from router and detect state changes."""
        try:
            router_devices = self.router_client.get_devices()
            if not router_devices:
                self._log("Router returned no devices, retrying login...")
                self.router_client.logged_in = False
                return
            
            # Track which MACs we've seen this round
            seen_macs = set()
            
            for dev in router_devices:
                mac = dev.get("mac", "")
                if not mac:
                    continue
                
                seen_macs.add(mac)
                ip = dev.get("ip", "")
                name = dev.get("name", mac)
                is_active = dev.get("active", False)
                connection = dev.get("connection", "")
                
                if mac not in self.devices:
                    # New device discovered
                    self.devices[mac] = DeviceTracker(
                        name=name, ip=ip, mac=mac, active=is_active
                    )
                    self.devices[mac].connection = connection
                    self._log(f"🆕 Discovered: {name} ({ip}) - {'ONLINE' if is_active else 'OFFLINE'}")
                    
                    # Set initial state without triggering notification
                    self.devices[mac].last_state = is_active
                    self.devices[mac].current_state = is_active
                    if is_active:
                        self.devices[mac].last_seen = datetime.now()
                else:
                    # Existing device - check for state change
                    device = self.devices[mac]
                    device.ip = ip  # IP might change
                    device.connection = connection
                    
                    # Update name if it changed to something meaningful
                    if name != mac and device.name == device.mac:
                        self._log(f"📝 Updated name: {device.name} → {name}")
                        device.name = name
                    
                    old_state = device.current_state
                    device.current_state = is_active
                    
                    if is_active:
                        device.last_seen = datetime.now()
                    
                    # Detect state change
                    if device.last_state is not None and is_active != device.last_state:
                        self._handle_state_change(device, is_active)
                    
                    device.last_state = is_active
            
            # Log summary periodically
            if self.check_count % 10 == 0:
                online = sum(1 for d in self.devices.values() if d.current_state)
                self._log(f"📊 Status: {online}/{len(self.devices)} devices online")
            
        except Exception as e:
            self._log(f"Error fetching devices: {e}")
    
    def get_device_statuses(self) -> dict:
        """Get current status of all devices (for bot commands)."""
        return {dev.name: dev.current_state for dev in self.devices.values()}
    
    def run(self):
        """Main monitoring loop."""
        self.running = True
        self._log("Starting Router-Based Presence Monitor")
        self._log(f"Using router API for presence detection (no ping needed)")
        self._log(f"Notify patterns: {NOTIFY_PATTERNS}")
        self._log(f"Check interval: {CHECK_INTERVAL}s")
        self._log("-" * 50)
        
        # Initial fetch
        self._log("Fetching initial device list from router...")
        self._fetch_and_update_devices()
        
        online_count = sum(1 for d in self.devices.values() if d.current_state)
        notify_count = sum(1 for d in self.devices.values() if d.should_notify())
        
        self._log(f"Tracking {len(self.devices)} devices ({online_count} online)")
        
        # Send startup notification
        self.notifier.send_message(
            f"🔔 <b>Presence Monitor Started</b>\n\n"
            f"Mode: Router API (reliable)\n"
            f"Tracking: {len(self.devices)} devices\n"
            f"Online now: {online_count}\n"
            f"Notify patterns: {', '.join(NOTIFY_PATTERNS)}\n\n"
            f"<b>Commands:</b> /status /stats /today /help"
        )
        
        while self.running:
            try:
                self._fetch_and_update_devices()
                self.check_count += 1
                
                # Process bot commands
                self.bot.process_updates(get_status_func=self.get_device_statuses)
                
                time.sleep(CHECK_INTERVAL)
            except KeyboardInterrupt:
                break
            except Exception as e:
                self._log(f"Error: {e}")
                time.sleep(5)
        
        self._log("Monitor stopped")
        if self.router_client:
            self.router_client.logout()
    
    def stop(self):
        """Stop the monitoring loop."""
        self.running = False


def main():
    """Entry point for the monitor."""
    monitor = RouterBasedMonitor()
    
    # Handle graceful shutdown
    def signal_handler(sig, frame):
        print("\nShutting down...")
        monitor.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Validate configuration
    if TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ Error: Please configure your Telegram bot token in config.py")
        sys.exit(1)
    
    if TELEGRAM_CHAT_ID == "YOUR_CHAT_ID_HERE":
        print("❌ Error: Please configure your Telegram chat ID in config.py")
        sys.exit(1)
    
    monitor.run()


if __name__ == "__main__":
    main()
