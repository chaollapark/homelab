#!/usr/bin/env python3
"""
VOO Router API Client - Fetches devices from the router.
Based on ~/bin/voo-router-sync
"""

import requests
import hashlib
import configparser
from pathlib import Path
from typing import List, Dict, Optional


# Configuration
CONFIG_DIR = Path.home() / "bin" / "config"
CONFIG_FILE = CONFIG_DIR / "router.conf"


def load_router_config() -> dict:
    """Load configuration from router.conf file."""
    config = configparser.ConfigParser()
    
    if not CONFIG_FILE.exists():
        return {
            'url': 'http://192.168.0.1',
            'username': '',
            'password': '',
        }
    
    config.read(CONFIG_FILE)
    
    return {
        'url': config.get('router', 'url', fallback='http://192.168.0.1'),
        'username': config.get('router', 'username', fallback=''),
        'password': config.get('router', 'password', fallback=''),
    }


def pbkdf2_hex(password: str, salt: str, iterations: int = 1000, key_length: int = 16) -> str:
    """Compute PBKDF2 hash and return as hex string."""
    if isinstance(password, str):
        password = password.encode('utf-8')
    if isinstance(salt, str):
        salt = salt.encode('utf-8')
    derived = hashlib.pbkdf2_hmac('sha256', password, salt, iterations, dklen=key_length)
    return derived.hex()


class VooRouterClient:
    """VOO Technicolor Router API client."""
    
    def __init__(self):
        config = load_router_config()
        self.url = config['url']
        self.username = config['username']
        self.password = config['password']
        self.session = None
        self.logged_in = False
    
    def login(self) -> bool:
        """Authenticate with the router."""
        if not self.username or not self.password:
            return False
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0',
            'Accept': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': f'{self.url}/',
        })
        
        try:
            # Initialize session
            self.session.get(f"{self.url}/", timeout=10)
            self.session.get(f"{self.url}/api/v1/session/menu", timeout=10)
            
            # Get salt
            resp = self.session.post(
                f"{self.url}/api/v1/session/login",
                data={"username": self.username, "password": "seeksalthash"},
                timeout=10
            )
            data = resp.json()
            
            if data.get("error") != "ok":
                return False
            
            salt = data.get("salt", "")
            salt_webui = data.get("saltwebui", "")
            
            # Compute password hash
            if salt == "none":
                final_password = self.password
            else:
                hashed1 = pbkdf2_hex(self.password, salt)
                final_password = pbkdf2_hex(hashed1, salt_webui)
            
            # Login
            resp = self.session.post(
                f"{self.url}/api/v1/session/login",
                data={"username": self.username, "password": final_password},
                timeout=10
            )
            data = resp.json()
            
            if data.get("error") != "ok":
                return False
            
            # Set CSRF token
            csrf = self.session.cookies.get("auth", "")
            self.session.headers.update({'X-CSRF-TOKEN': csrf})
            
            # Activate session
            self.session.get(f"{self.url}/api/v1/session/menu", timeout=10)
            
            self.logged_in = True
            return True
            
        except Exception:
            return False
    
    def get_devices(self) -> List[Dict]:
        """Fetch list of all devices from router."""
        if not self.session or not self.logged_in:
            if not self.login():
                return []
        
        try:
            resp = self.session.get(f"{self.url}/api/v1/host", timeout=30)
            data = resp.json()
            
            if data.get("error") == "ok":
                hosts = data.get("data", {}).get("hostTbl", [])
                return self._parse_devices(hosts)
            return []
                
        except Exception:
            return []
    
    def _parse_devices(self, hosts: list) -> List[Dict]:
        """Parse device list from router response."""
        devices = []
        for h in hosts:
            mac = h.get("physaddress", "").upper()
            ip = h.get("ipaddress", "")
            hostname = h.get("hostname", "")
            active = h.get("active") == "true"
            interface = h.get("layer1interface", "").lower()
            
            # Determine connection type
            if "wifi" in interface:
                if "ssid.1" in interface:
                    conn = "WiFi 2.4G"
                elif "ssid.2" in interface:
                    conn = "WiFi 5G"
                else:
                    conn = "WiFi"
            elif "ethernet" in interface:
                conn = "Ethernet"
            else:
                conn = "Unknown"
            
            # Use hostname or MAC as name
            name = hostname if hostname and hostname.lower() != mac.lower().replace(":", "") else mac
            
            devices.append({
                "mac": mac,
                "ip": ip,
                "name": name,
                "hostname": hostname,
                "active": active,
                "connection": conn,
            })
        
        return devices
    
    def get_active_devices(self) -> List[Dict]:
        """Get only active devices."""
        return [d for d in self.get_devices() if d["active"]]
    
    def logout(self):
        """Logout from router."""
        if self.session and self.logged_in:
            try:
                self.session.post(f"{self.url}/api/v1/session/logout", timeout=5)
            except:
                pass
            self.logged_in = False
