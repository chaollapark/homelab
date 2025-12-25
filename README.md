# Homelab Tools (Part1)

A collection of tools for monitoring and managing my home network.

## 📱 Phone Presence Monitor

Monitors device presence on the network using the VOO router API and sends Telegram notifications.

**Features:**
- Auto-discovers all devices from router
- Logs arrivals/departures to CSV for statistics
- Sends Telegram notifications for specified devices
- **Router control** - block/unblock sites and kick devices
- Runs as a systemd service

**Telegram Bot Commands:**
- `/status`, `/stats`, `/today`, `/week` - Presence monitoring
- `/block <site>`, `/unblock <site>`, `/blocklist` - Site blocking
- `/kick <device>`, `/allow <device>`, `/banned` - Device control
- `/devices`, `/help` - Info commands

**Location:** `phone-presence-monitor/`

## 🔍 MOTD Tools

Network scanning and router management tools for SSH login and command-line use.

### router (NEW)
**Local CLI for router management** - works offline!
```bash
router devices          # List devices from router
router kick <name>      # Block device from network
router allow <name>     # Unblock device
router block <site>     # Block website
router banned           # Show blocked devices/sites
```

### network-scan
Scans the local network and displays connected devices with custom names.
```bash
scan                    # Quick summary
scan -v                 # Verbose details
scan --live             # Fresh scan
```

### dns-traffic
Analyze DNS queries per device to see what domains they're accessing.
```bash
dns-traffic capture     # Live capture
dns-traffic analyze     # Analyze saved capture
```

### voo-router-api / voo-router-sync
Low-level router API tools for device discovery and name syncing.

**Location:** `motd-tools/`

## 🖥️ SSH Login MOTD

When you SSH in, you'll see:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🖥️  Welcome back! Network Status (cached)
🌐 Network: 10 devices (all known)
📱 Redmi Note 12 Pro 5G: PRESENT/ABSENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Quick Commands: (work offline - no internet needed)
  scan -v|-a|--live     Network scan
  router devices        List devices from router
  router kick <name>    Block device
  router allow <name>   Unblock device
  router block <site>   Block website
  router banned         Show blocked
  router --help         Full help
  dns-traffic           DNS analyzer
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Installation

See individual README files in each directory for setup instructions.

## Systemd Services

Included service files:
- `phone-monitor.service` - Phone presence monitor with Telegram bot
- `network-scan.service` + `network-scan.timer` - Periodic network scanning

## Router Compatibility

Tested with **VOO Technicolor routers** using PBKDF2 authentication.
May work with other Technicolor routers with similar APIs.
