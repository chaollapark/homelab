#!/usr/bin/env python3
"""
Allowlist Manager - Manages devices that should never be blocked.

These are essential devices like:
- This device (the one running the lockdown)
- Router/Modem
- WiFi Access Points
- Critical servers
"""

import json
import subprocess
import re
from pathlib import Path
from typing import List, Dict, Optional


# Default config location
ALLOWLIST_FILE = Path(__file__).parent / "allowlist.json"

# Default essential devices (WiFi APs from your setup)
DEFAULT_ESSENTIAL_DEVICES = [
    # WiFi Access Points - these provide WiFi connectivity
    {"name": "AP1-Archer", "mac": "60:83:E7:B5:66:22", "reason": "WiFi AP"},
    {"name": "AP2-Archer", "mac": "60:83:E7:B5:67:5D", "reason": "WiFi AP"},
    {"name": "AP3-Archer", "mac": "60:83:E7:B5:41:8C", "reason": "WiFi AP"},
    {"name": "AP4-Archer", "mac": "20:23:51:21:61:9F", "reason": "WiFi AP"},
]


class AllowlistManager:
    """Manages the allowlist of devices that should never be blocked."""
    
    def __init__(self, allowlist_file: Path = None):
        self.allowlist_file = allowlist_file or ALLOWLIST_FILE
        self._allowlist = None
    
    def _load(self) -> Dict:
        """Load allowlist from file."""
        if self._allowlist is not None:
            return self._allowlist
        
        if self.allowlist_file.exists():
            try:
                with open(self.allowlist_file, 'r') as f:
                    self._allowlist = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._allowlist = self._create_default()
        else:
            self._allowlist = self._create_default()
        
        return self._allowlist
    
    def _save(self):
        """Save allowlist to file."""
        with open(self.allowlist_file, 'w') as f:
            json.dump(self._allowlist, f, indent=2)
    
    def _create_default(self) -> Dict:
        """Create default allowlist with this device and essential devices."""
        this_mac = self.get_this_device_mac()
        
        devices = []
        
        # Add this device first
        if this_mac:
            devices.append({
                "name": "This Device (Homelab)",
                "mac": this_mac.upper(),
                "reason": "Control device - never block"
            })
        
        # Add default essential devices
        devices.extend(DEFAULT_ESSENTIAL_DEVICES)
        
        return {"devices": devices}
    
    @staticmethod
    def get_this_device_mac() -> Optional[str]:
        """Auto-detect this device's MAC address."""
        try:
            # Linux: get MAC of first UP interface
            result = subprocess.run(
                ["ip", "link", "show"],
                capture_output=True, text=True, timeout=5
            )
            
            lines = result.stdout.split('\n')
            in_up_interface = False
            
            for line in lines:
                if 'state UP' in line and 'LOOPBACK' not in line:
                    in_up_interface = True
                elif in_up_interface and 'ether' in line:
                    match = re.search(r'ether\s+([0-9a-fA-F:]{17})', line)
                    if match:
                        return match.group(1).upper()
                elif line.strip() and not line.startswith(' '):
                    in_up_interface = False
            
            return None
        except Exception:
            return None
    
    def get_allowlist(self) -> List[Dict]:
        """Get list of allowlisted devices."""
        return self._load().get("devices", [])
    
    def get_allowlisted_macs(self) -> List[str]:
        """Get list of allowlisted MAC addresses (uppercase)."""
        return [d["mac"].upper() for d in self.get_allowlist()]
    
    def is_allowlisted(self, mac: str) -> bool:
        """Check if a MAC address is in the allowlist."""
        return mac.upper() in self.get_allowlisted_macs()
    
    def add_device(self, name: str, mac: str, reason: str = "User added") -> bool:
        """Add a device to the allowlist."""
        mac = mac.upper()
        
        if self.is_allowlisted(mac):
            return False  # Already in list
        
        self._load()
        self._allowlist["devices"].append({
            "name": name,
            "mac": mac,
            "reason": reason
        })
        self._save()
        return True
    
    def remove_device(self, mac: str) -> bool:
        """Remove a device from the allowlist by MAC."""
        mac = mac.upper()
        
        self._load()
        original_len = len(self._allowlist["devices"])
        self._allowlist["devices"] = [
            d for d in self._allowlist["devices"]
            if d["mac"].upper() != mac
        ]
        
        if len(self._allowlist["devices"]) < original_len:
            self._save()
            return True
        return False
    
    def initialize(self):
        """Initialize allowlist file with defaults if it doesn't exist."""
        if not self.allowlist_file.exists():
            self._allowlist = self._create_default()
            self._save()
            return True
        return False


if __name__ == "__main__":
    # Test/initialize allowlist
    manager = AllowlistManager()
    manager.initialize()
    
    print("Allowlisted devices:")
    for device in manager.get_allowlist():
        print(f"  {device['name']}: {device['mac']} ({device['reason']})")
    
    print(f"\nThis device MAC: {manager.get_this_device_mac()}")
