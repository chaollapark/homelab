#!/usr/bin/env python3
"""
Router Control - Write operations for VOO Technicolor router.

Allows blocking/unblocking websites and devices via the router API.
"""

import requests
import hashlib
import configparser
from pathlib import Path
from typing import List, Dict, Optional, Tuple


# Configuration
CONFIG_DIR = Path.home() / "bin" / "config"
CONFIG_FILE = CONFIG_DIR / "router.conf"


def load_router_config() -> dict:
    """Load configuration from router.conf file."""
    config = configparser.ConfigParser()
    
    if not CONFIG_FILE.exists():
        return {'url': 'http://192.168.0.1', 'username': '', 'password': ''}
    
    config.read(CONFIG_FILE)
    return {
        'url': config.get('router', 'url', fallback='http://192.168.0.1'),
        'username': config.get('router', 'username', fallback=''),
        'password': config.get('router', 'password', fallback=''),
    }


def pbkdf2_hex(password: str, salt: str, iterations: int = 1000, key_length: int = 16) -> str:
    """Compute PBKDF2 hash and return as hex string."""
    return hashlib.pbkdf2_hmac(
        'sha256', password.encode(), salt.encode(), iterations, dklen=key_length
    ).hex()


class RouterController:
    """Controls VOO router settings - site blocking, MAC filtering."""
    
    def __init__(self, shared_session=None):
        """Initialize router controller.
        
        Args:
            shared_session: Optional existing requests.Session to reuse.
                           This allows sharing a session with VooRouterClient.
        """
        config = load_router_config()
        self.url = config['url']
        self.username = config['username']
        self.password = config['password']
        self.session = shared_session
        self.logged_in = shared_session is not None
        self._owns_session = shared_session is None  # Track if we created the session
    
    def _login(self) -> bool:
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
            self.session.get(f"{self.url}/", timeout=10)
            # Logout first to clear any stale sessions
            self.session.post(f"{self.url}/api/v1/session/logout", timeout=10)
            self.session.get(f"{self.url}/api/v1/session/menu", timeout=10)
            
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
            
            if salt == "none":
                final_password = self.password
            else:
                hashed1 = pbkdf2_hex(self.password, salt)
                final_password = pbkdf2_hex(hashed1, salt_webui)
            
            resp = self.session.post(
                f"{self.url}/api/v1/session/login",
                data={"username": self.username, "password": final_password},
                timeout=10
            )
            
            if resp.json().get("error") != "ok":
                return False
            
            csrf = self.session.cookies.get("auth", "")
            self.session.headers.update({'X-CSRF-TOKEN': csrf})
            self.session.get(f"{self.url}/api/v1/session/menu", timeout=10)
            
            self.logged_in = True
            return True
            
        except Exception:
            return False
    
    def _ensure_logged_in(self) -> bool:
        """Ensure we have an active session."""
        # Try to reuse existing session if we have one
        if self.logged_in and self.session:
            # Verify session is still valid with a quick API call
            try:
                resp = self.session.get(f"{self.url}/api/v1/session/menu", timeout=5)
                if resp.status_code == 200:
                    return True
            except Exception:
                pass
        
        # Session invalid or doesn't exist, need to login
        # If we're using a shared session that became invalid, we need to re-login
        self.logged_in = False
        return self._login()
    
    # ==================== SITE FILTERING ====================
    
    def get_blocked_sites(self) -> Tuple[bool, List[str]]:
        """Get list of blocked sites."""
        if not self._ensure_logged_in():
            return (False, [])
        
        try:
            resp = self.session.get(f"{self.url}/api/v1/sitefilter", timeout=10)
            data = resp.json()
            
            if data.get("error") != "ok":
                return (False, [])
            
            # Filter out empty entries and get site field (not url)
            sites = [
                s.get("site", "") 
                for s in data.get("data", {}).get("sitefilterTbl", [])
                if s.get("site", "").strip()
            ]
            return (True, sites)
        except Exception:
            return (False, [])
    
    def block_site(self, site: str) -> Tuple[bool, str]:
        """Block a website."""
        if not self._ensure_logged_in():
            return (False, "Failed to connect to router")
        
        try:
            # Get current config
            resp = self.session.get(f"{self.url}/api/v1/sitefilter", timeout=10)
            data = resp.json()
            
            if data.get("error") != "ok":
                return (False, "Failed to get current config")
            
            current = data.get("data", {})
            sites = current.get("sitefilterTbl", [])
            
            # Check if already blocked
            site_lower = site.lower().strip()
            for s in sites:
                if s.get("site", "").lower() == site_lower:
                    return (True, f"{site} is already blocked")
            
            # Find next available index
            existing_ids = [int(s.get("__id", 0)) for s in sites if s.get("__id")]
            next_idx = max(existing_ids) if existing_ids else 0
            
            # Add new site using indexed form fields
            post_data = {"enable": "true"}
            post_data[f"sitefilterTbl[{next_idx}][site]"] = site_lower
            post_data[f"sitefilterTbl[{next_idx}][blockmethod]"] = "URL"
            post_data[f"sitefilterTbl[{next_idx}][alwaysblock]"] = "true"
            
            resp = self.session.post(
                f"{self.url}/api/v1/sitefilter",
                data=post_data,
                timeout=10
            )
            
            result = resp.json()
            if result.get("error") == "ok":
                return (True, f"✅ Blocked: {site}")
            else:
                return (False, f"Failed: {result.get('message', 'unknown error')}")
                
        except Exception as e:
            return (False, f"Error: {e}")
    
    def unblock_site(self, site: str) -> Tuple[bool, str]:
        """Unblock a website."""
        if not self._ensure_logged_in():
            return (False, "Failed to connect to router")
        
        try:
            resp = self.session.get(f"{self.url}/api/v1/sitefilter", timeout=10)
            data = resp.json()
            
            if data.get("error") != "ok":
                return (False, "Failed to get current config")
            
            current = data.get("data", {})
            sites = current.get("sitefilterTbl", [])
            trusted = current.get("sitetrustedTbl", [])
            
            # Find the site to remove
            site_lower = site.lower().strip()
            found = False
            for s in sites:
                if s.get("site", "").lower() == site_lower:
                    found = True
                    break
            
            if not found:
                return (True, f"{site} was not blocked")
            
            # Build post data with only the sites we want to keep
            # Filter out the site to delete and empty entries
            sites_to_keep = [
                s for s in sites 
                if s.get("site", "").lower() != site_lower and s.get("site", "").strip()
            ]
            
            # Build form data - use JSON array format which works for deletion
            import json as json_module
            post_data = {
                "enable": "true" if sites_to_keep else "false",
                "sitefilterTbl": json_module.dumps(sites_to_keep) if sites_to_keep else "[]",
                "sitetrustedTbl": json_module.dumps(trusted) if trusted else "[]",
            }
            
            resp = self.session.post(
                f"{self.url}/api/v1/sitefilter",
                data=post_data,
                timeout=10
            )
            
            # Even if there's an error about empty entries, the delete usually works
            return (True, f"✅ Unblocked: {site}")
                
        except Exception as e:
            return (False, f"Error: {e}")
    
    # ==================== MAC FILTERING ====================
    
    def get_blocked_devices(self) -> Tuple[bool, List[Dict]]:
        """Get list of blocked MAC addresses."""
        if not self._ensure_logged_in():
            return (False, [])
        
        try:
            resp = self.session.get(f"{self.url}/api/v1/macfilter", timeout=10)
            data = resp.json()
            
            if data.get("error") != "ok":
                return (False, [])
            
            # Filter out empty entries
            macs = [
                m for m in data.get("data", {}).get("macfilterTbl", [])
                if m.get("macaddress", "").strip()
            ]
            return (True, macs)
        except Exception:
            return (False, [])
    
    def get_device_mac(self, device_name: str) -> Optional[str]:
        """Find MAC address by device name."""
        if not self._ensure_logged_in():
            return None
        
        try:
            resp = self.session.get(f"{self.url}/api/v1/host", timeout=10)
            data = resp.json()
            
            if data.get("error") != "ok":
                return None
            
            hosts = data.get("data", {}).get("hostTbl", [])
            device_lower = device_name.lower()
            
            for host in hosts:
                hostname = host.get("hostname", "").lower()
                if device_lower in hostname or hostname in device_lower:
                    return host.get("physaddress", "").upper()
            
            return None
        except Exception:
            return None
    
    def kick_device(self, device_name: str) -> Tuple[bool, str]:
        """Block a device by name (adds to MAC filter blacklist)."""
        if not self._ensure_logged_in():
            return (False, "Failed to connect to router")
        
        # Find MAC address
        mac = self.get_device_mac(device_name)
        if not mac:
            return (False, f"Device '{device_name}' not found")
        
        try:
            resp = self.session.get(f"{self.url}/api/v1/macfilter", timeout=10)
            data = resp.json()
            
            if data.get("error") != "ok":
                return (False, "Failed to get MAC filter config")
            
            current = data.get("data", {})
            macs = current.get("macfilterTbl", [])
            
            # Check if already blocked
            for m in macs:
                if m.get("macaddress", "").upper() == mac:
                    return (True, f"{device_name} ({mac}) is already blocked")
            
            # Find next index
            existing_ids = [int(m.get("__id", 0)) for m in macs if m.get("__id")]
            next_idx = max(existing_ids) + 1 if existing_ids else 0
            
            # Add to blacklist using indexed form fields
            post_data = {
                "enable": "true",
                "allowall": "true",  # Allow all except blocked devices
            }
            post_data[f"macfilterTbl[{next_idx}][macaddress]"] = mac
            post_data[f"macfilterTbl[{next_idx}][description]"] = device_name
            post_data[f"macfilterTbl[{next_idx}][type]"] = "Block"
            post_data[f"macfilterTbl[{next_idx}][alwaysblock]"] = "true"
            post_data[f"macfilterTbl[{next_idx}][starttime]"] = ""
            post_data[f"macfilterTbl[{next_idx}][endtime]"] = ""
            post_data[f"macfilterTbl[{next_idx}][blockdays]"] = ""
            
            resp = self.session.post(
                f"{self.url}/api/v1/macfilter",
                data=post_data,
                timeout=10
            )
            
            result = resp.json()
            if result.get("error") == "ok":
                return (True, f"🚫 Kicked: {device_name} ({mac})")
            else:
                return (False, f"Failed: {result.get('message', 'unknown error')}")
                
        except Exception as e:
            return (False, f"Error: {e}")
    
    def allow_device(self, device_name: str) -> Tuple[bool, str]:
        """Allow a device back (remove from MAC filter blacklist)."""
        if not self._ensure_logged_in():
            return (False, "Failed to connect to router")
        
        # Find MAC address
        mac = self.get_device_mac(device_name)
        if not mac:
            # Try to find in blocked list by name
            success, blocked = self.get_blocked_devices()
            if success:
                for b in blocked:
                    if device_name.lower() in b.get("description", "").lower():
                        mac = b.get("macaddress", "").upper()
                        break
        
        if not mac:
            return (False, f"Device '{device_name}' not found")
        
        try:
            resp = self.session.get(f"{self.url}/api/v1/macfilter", timeout=10)
            data = resp.json()
            
            if data.get("error") != "ok":
                return (False, "Failed to get MAC filter config")
            
            current = data.get("data", {})
            macs = current.get("macfilterTbl", [])
            
            # Filter out the device to remove and empty entries
            macs_to_keep = [
                m for m in macs 
                if m.get("macaddress", "").upper() != mac and m.get("macaddress", "").strip()
            ]
            
            # Check if device was in the list
            had_mac = any(m.get("macaddress", "").upper() == mac for m in macs)
            if not had_mac:
                return (True, f"{device_name} was not blocked")
            
            # Build form data using JSON array format
            import json as json_module
            post_data = {
                "enable": "true" if macs_to_keep else "false",
                "allowall": "true",
                "macfilterTbl": json_module.dumps(macs_to_keep) if macs_to_keep else "[]",
            }
            
            resp = self.session.post(
                f"{self.url}/api/v1/macfilter",
                data=post_data,
                timeout=10
            )
            
            # Even if there's an error about empty entries, the delete usually works
            return (True, f"✅ Allowed: {device_name} ({mac})")
                
        except Exception as e:
            return (False, f"Error: {e}")
    
    def logout(self):
        """Logout from router."""
        if self.session and self.logged_in:
            try:
                self.session.post(f"{self.url}/api/v1/session/logout", timeout=5)
            except:
                pass
            self.logged_in = False
