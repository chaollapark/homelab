#!/usr/bin/env python3
"""
Lockdown Manager - Block all devices except allowlisted ones.

This module provides the ability to:
- Block all network devices except essential ones (this device, APs, router)
- Restore normal access by unblocking all devices
- Track lockdown state for recovery

Two modes:
- STRICT (default): Uses router's allowlist mode - blocks ALL unknown devices,
  including any new devices that connect later
- SOFT: Only blocks currently visible devices (new devices can still connect)
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple

from allowlist import AllowlistManager
from router_control import RouterController
from router_client import VooRouterClient


# State file to track lockdown status and blocked devices
LOCKDOWN_STATE_FILE = Path(__file__).parent / "lockdown_state.json"


class LockdownManager:
    """Manages network lockdown - blocking all devices except allowlisted ones."""
    
    def __init__(self):
        self.allowlist = AllowlistManager()
        self.router_client = VooRouterClient()
        self.router_control = RouterController()
        self.state_file = LOCKDOWN_STATE_FILE
    
    def _load_state(self) -> Dict:
        """Load lockdown state from file."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {"active": False, "blocked_devices": [], "started_at": None, "mode": None}
    
    def _save_state(self, state: Dict):
        """Save lockdown state to file."""
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def is_active(self) -> bool:
        """Check if lockdown is currently active."""
        return self._load_state().get("active", False)
    
    def get_status(self) -> Dict:
        """Get detailed lockdown status."""
        state = self._load_state()
        return {
            "active": state.get("active", False),
            "mode": state.get("mode", "unknown"),
            "blocked_count": len(state.get("blocked_devices", [])),
            "blocked_devices": state.get("blocked_devices", []),
            "started_at": state.get("started_at"),
        }
    
    def get_devices_to_block(self) -> List[Dict]:
        """Get list of devices that would be blocked (not in allowlist)."""
        all_devices = self.router_client.get_devices()
        allowlisted_macs = self.allowlist.get_allowlisted_macs()
        
        to_block = []
        for device in all_devices:
            mac = device.get("mac", "").upper()
            if mac and mac not in allowlisted_macs:
                to_block.append(device)
        
        return to_block
    
    def start_lockdown(self, dry_run: bool = False, strict: bool = True) -> Tuple[bool, str, List[Dict]]:
        """Start lockdown - block all devices except allowlisted ones.
        
        Args:
            dry_run: If True, just return what would be blocked without blocking.
            strict: If True (default), use allowlist mode on router.
                    This blocks ALL unknown devices including future connections.
                    If False, only block currently visible devices.
        
        Returns:
            Tuple of (success, message, list of blocked/affected devices)
        """
        if self.is_active():
            state = self._load_state()
            return (False, "Lockdown already active", state.get("blocked_devices", []))
        
        self.allowlist.initialize()
        devices_to_block = self.get_devices_to_block()
        
        if dry_run:
            mode_str = "STRICT (blocks all unknown)" if strict else "SOFT (blocks visible only)"
            return (True, f"[{mode_str}] Would block {len(devices_to_block)} devices", devices_to_block)
        
        if strict:
            return self._start_strict_lockdown(devices_to_block)
        else:
            return self._start_soft_lockdown(devices_to_block)
    
    def _start_strict_lockdown(self, devices_to_block: List[Dict]) -> Tuple[bool, str, List[Dict]]:
        """Start strict lockdown using router's allowlist mode.
        
        This sets the router to ONLY allow devices in the allowlist.
        Any device not explicitly allowed will be blocked, including
        new devices that try to connect later.
        """
        if not self.router_control._ensure_logged_in():
            return (False, "Failed to connect to router", [])
        
        try:
            # Get allowlisted devices to add to router's allow list
            allowlisted = self.allowlist.get_allowlist()
            
            # Build the MAC filter table with ONLY allowlisted devices
            mac_entries = []
            for i, device in enumerate(allowlisted):
                mac_entries.append({
                    "macaddress": device["mac"].upper(),
                    "description": device["name"],
                    "type": "Allow",
                    "alwaysblock": "false",
                })
            
            # Set router to allowlist mode (allowall=false means block all except listed)
            post_data = {
                "enable": "true",
                "allowall": "false",  # KEY: This blocks everything not in the list
                "macfilterTbl": json.dumps(mac_entries),
            }
            
            resp = self.router_control.session.post(
                f"{self.router_control.url}/api/v1/macfilter",
                data=post_data,
                timeout=15
            )
            
            result = resp.json()
            if result.get("error") != "ok":
                return (False, f"Router error: {result.get('message', 'unknown')}", [])
            
            # Save state
            state = {
                "active": True,
                "mode": "strict",
                "blocked_devices": [{"mac": d["mac"], "name": d.get("name", d["mac"])} for d in devices_to_block],
                "allowlisted_devices": [{"mac": d["mac"], "name": d["name"]} for d in allowlisted],
                "started_at": datetime.now().isoformat(),
            }
            self._save_state(state)
            
            msg = f"🔒 STRICT Lockdown active: Only {len(allowlisted)} devices allowed"
            msg += f"\n   {len(devices_to_block)} devices blocked (+ all unknown devices)"
            return (True, msg, devices_to_block)
            
        except Exception as e:
            return (False, f"Error: {e}", [])
    
    def _start_soft_lockdown(self, devices_to_block: List[Dict]) -> Tuple[bool, str, List[Dict]]:
        """Start soft lockdown - only block currently visible devices."""
        if not devices_to_block:
            return (True, "No devices to block (all are allowlisted)", [])
        
        blocked = []
        failed = []
        
        for device in devices_to_block:
            mac = device.get("mac", "")
            name = device.get("name", device.get("hostname", mac))
            
            success, msg = self._block_device_by_mac(mac, name)
            if success:
                blocked.append({"mac": mac, "name": name})
            else:
                failed.append({"mac": mac, "name": name, "error": msg})
        
        state = {
            "active": True,
            "mode": "soft",
            "blocked_devices": blocked,
            "failed_devices": failed,
            "started_at": datetime.now().isoformat(),
        }
        self._save_state(state)
        
        msg = f"🔒 SOFT Lockdown active: blocked {len(blocked)} devices"
        if failed:
            msg += f" ({len(failed)} failed)"
        msg += "\n   ⚠️  New devices can still connect!"
        return (True, msg, blocked)
    
    def stop_lockdown(self) -> Tuple[bool, str, List[Dict]]:
        """Stop lockdown - restore normal network access."""
        state = self._load_state()
        
        if not state.get("active", False):
            return (False, "Lockdown is not active", [])
        
        mode = state.get("mode", "soft")
        
        if mode == "strict":
            return self._stop_strict_lockdown(state)
        else:
            return self._stop_soft_lockdown(state)
    
    def _stop_strict_lockdown(self, state: Dict) -> Tuple[bool, str, List[Dict]]:
        """Stop strict lockdown - restore allowall mode."""
        if not self.router_control._ensure_logged_in():
            return (False, "Failed to connect to router", [])
        
        try:
            # Set router back to allowall mode (allow everything)
            post_data = {
                "enable": "false",
                "allowall": "true",
                "macfilterTbl": "[]",
            }
            
            resp = self.router_control.session.post(
                f"{self.router_control.url}/api/v1/macfilter",
                data=post_data,
                timeout=15
            )
            
            blocked_devices = state.get("blocked_devices", [])
            self._save_state({"active": False, "mode": None, "stopped_at": datetime.now().isoformat()})
            
            return (True, f"🔓 Lockdown ended: All devices can now connect", blocked_devices)
            
        except Exception as e:
            return (False, f"Error: {e}", [])
    
    def _stop_soft_lockdown(self, state: Dict) -> Tuple[bool, str, List[Dict]]:
        """Stop soft lockdown - unblock previously blocked devices."""
        blocked_devices = state.get("blocked_devices", [])
        
        if not blocked_devices:
            self._save_state({"active": False, "mode": None})
            return (True, "No devices to unblock", [])
        
        unblocked = []
        failed = []
        
        for device in blocked_devices:
            mac = device.get("mac", "")
            name = device.get("name", mac)
            
            success, msg = self._unblock_device_by_mac(mac)
            if success or "not blocked" in msg.lower():
                unblocked.append({"mac": mac, "name": name})
            else:
                failed.append({"mac": mac, "name": name, "error": msg})
        
        self._save_state({"active": False, "mode": None, "stopped_at": datetime.now().isoformat()})
        
        msg = f"🔓 Lockdown ended: unblocked {len(unblocked)} devices"
        if failed:
            msg += f" ({len(failed)} failed)"
        return (True, msg, unblocked)
    
    def _block_device_by_mac(self, mac: str, name: str = "") -> Tuple[bool, str]:
        """Block a device by MAC address directly."""
        if not self.router_control._ensure_logged_in():
            return (False, "Failed to connect to router")
        
        try:
            resp = self.router_control.session.get(
                f"{self.router_control.url}/api/v1/macfilter", timeout=10
            )
            data = resp.json()
            
            if data.get("error") != "ok":
                return (False, "Failed to get MAC filter config")
            
            macs = data.get("data", {}).get("macfilterTbl", [])
            
            for m in macs:
                if m.get("macaddress", "").upper() == mac.upper():
                    return (True, f"{name} already blocked")
            
            existing_ids = [int(m.get("__id", 0)) for m in macs if m.get("__id")]
            next_idx = max(existing_ids) + 1 if existing_ids else 0
            
            post_data = {
                "enable": "true",
                "allowall": "true",
            }
            post_data[f"macfilterTbl[{next_idx}][macaddress]"] = mac.upper()
            post_data[f"macfilterTbl[{next_idx}][description]"] = name or "Lockdown"
            post_data[f"macfilterTbl[{next_idx}][type]"] = "Block"
            post_data[f"macfilterTbl[{next_idx}][alwaysblock]"] = "true"
            
            resp = self.router_control.session.post(
                f"{self.router_control.url}/api/v1/macfilter",
                data=post_data,
                timeout=10
            )
            
            result = resp.json()
            if result.get("error") == "ok":
                return (True, f"Blocked {name}")
            else:
                return (False, result.get("message", "Unknown error"))
                
        except Exception as e:
            return (False, str(e))
    
    def _unblock_device_by_mac(self, mac: str) -> Tuple[bool, str]:
        """Unblock a device by MAC address."""
        if not self.router_control._ensure_logged_in():
            return (False, "Failed to connect to router")
        
        try:
            resp = self.router_control.session.get(
                f"{self.router_control.url}/api/v1/macfilter", timeout=10
            )
            data = resp.json()
            
            if data.get("error") != "ok":
                return (False, "Failed to get MAC filter config")
            
            macs = data.get("data", {}).get("macfilterTbl", [])
            
            macs_to_keep = [
                m for m in macs
                if m.get("macaddress", "").upper() != mac.upper() and m.get("macaddress", "").strip()
            ]
            
            had_mac = any(m.get("macaddress", "").upper() == mac.upper() for m in macs)
            if not had_mac:
                return (True, "Device was not blocked")
            
            post_data = {
                "enable": "true" if macs_to_keep else "false",
                "allowall": "true",
                "macfilterTbl": json.dumps(macs_to_keep) if macs_to_keep else "[]",
            }
            
            resp = self.router_control.session.post(
                f"{self.router_control.url}/api/v1/macfilter",
                data=post_data,
                timeout=10
            )
            
            return (True, f"Unblocked {mac}")
                
        except Exception as e:
            return (False, str(e))


def main():
    """CLI interface for lockdown."""
    import sys
    
    manager = LockdownManager()
    
    if len(sys.argv) < 2:
        print("Usage: python lockdown.py [status|start|stop|preview|allowlist]")
        print("")
        print("Commands:")
        print("  status    - Show lockdown status")
        print("  preview   - Show what would be blocked")
        print("  start     - Start STRICT lockdown (blocks all unknown devices)")
        print("  start soft - Start SOFT lockdown (only blocks visible devices)")
        print("  stop      - Stop lockdown")
        print("  allowlist - Show allowlisted devices")
        sys.exit(1)
    
    cmd = sys.argv[1].lower()
    
    if cmd == "status":
        status = manager.get_status()
        if status["active"]:
            mode = status.get('mode', 'unknown').upper()
            print(f"🔒 Lockdown ACTIVE ({mode} mode) since {status['started_at']}")
            print(f"   Blocked devices: {status['blocked_count']}")
            for dev in status["blocked_devices"]:
                print(f"   - {dev['name']} ({dev['mac']})")
        else:
            print("🔓 Lockdown is NOT active")
    
    elif cmd == "preview":
        print("Devices that would be blocked:")
        devices = manager.get_devices_to_block()
        if not devices:
            print("  (none - all devices are allowlisted)")
        for dev in devices:
            print(f"  - {dev.get('name', dev.get('hostname', 'Unknown'))} ({dev['mac']})")
        print(f"\nTotal: {len(devices)} visible devices")
        print("\nNote: STRICT mode also blocks any NEW devices that try to connect!")
    
    elif cmd == "start":
        soft_mode = len(sys.argv) > 2 and sys.argv[2].lower() == "soft"
        mode_name = "SOFT" if soft_mode else "STRICT"
        print(f"Starting {mode_name} lockdown...")
        success, msg, blocked = manager.start_lockdown(strict=not soft_mode)
        print(msg)
        if blocked and not soft_mode:
            print("\nBlocked devices:")
            for dev in blocked:
                print(f"  - {dev.get('name', dev['mac'])} ({dev['mac']})")
    
    elif cmd == "stop":
        print("Stopping lockdown...")
        success, msg, unblocked = manager.stop_lockdown()
        print(msg)
    
    elif cmd == "allowlist":
        print("Allowlisted devices (never blocked):")
        manager.allowlist.initialize()
        for dev in manager.allowlist.get_allowlist():
            print(f"  ✓ {dev['name']} ({dev['mac']}) - {dev['reason']}")
    
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
