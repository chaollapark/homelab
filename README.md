# Homelab Tools

A collection of tools for monitoring and managing my home network.

## 📱 Phone Presence Monitor

Monitors device presence on the network using the VOO router API and sends Telegram notifications.

**Features:**
- Auto-discovers all devices from router
- Logs arrivals/departures to CSV for statistics
- Sends Telegram notifications for specified devices
- Telegram bot commands: `/status`, `/stats`, `/today`, `/week`, `/help`
- Runs as a systemd service

**Location:** `phone-presence-monitor/`

## 🔍 MOTD Tools

Network scanning and router integration tools.

### network-scan
Scans the local network and displays connected devices with custom names.

### network-scan-daemon
Background daemon for periodic network scanning.

### voo-router-api
Low-level API client for VOO Technicolor routers with PBKDF2 authentication.

### voo-router-sync
Syncs device names from the VOO router to the local device database.

**Location:** `motd-tools/`

## Installation

See individual README files in each directory for setup instructions.

## Systemd Services

Included service files:
- `phone-monitor.service` - Phone presence monitor
- `network-scan.service` + `network-scan.timer` - Periodic network scanning
