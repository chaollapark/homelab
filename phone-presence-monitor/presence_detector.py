"""
Network presence detection module using ping.
"""

import subprocess
import platform
from typing import Tuple


class PresenceDetector:
    """Detects device presence on network via ping."""
    
    def __init__(self, ip: str, timeout: int = 2, attempts: int = 3):
        self.ip = ip
        self.timeout = timeout
        self.attempts = attempts
        self._system = platform.system().lower()
    
    def _build_ping_command(self) -> list:
        """Build platform-specific ping command."""
        if self._system == "windows":
            return ["ping", "-n", "1", "-w", str(self.timeout * 1000), self.ip]
        else:
            # Linux/macOS
            return ["ping", "-c", "1", "-W", str(self.timeout), self.ip]
    
    def ping_once(self) -> bool:
        """Execute a single ping and return True if successful."""
        cmd = self._build_ping_command()
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=self.timeout + 1
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            return False
        except Exception as e:
            print(f"Ping error: {e}")
            return False
    
    def is_present(self) -> Tuple[bool, int]:
        """
        Check if device is present on network.
        
        Returns:
            Tuple of (is_present, successful_pings)
        """
        successful = 0
        for _ in range(self.attempts):
            if self.ping_once():
                successful += 1
        
        # Consider present if at least one ping succeeds
        return (successful > 0, successful)
    
    def check_status(self) -> dict:
        """Get detailed status of the device."""
        is_present, successful_pings = self.is_present()
        return {
            "ip": self.ip,
            "is_present": is_present,
            "successful_pings": successful_pings,
            "total_attempts": self.attempts
        }
