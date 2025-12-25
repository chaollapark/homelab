# Phone Presence Monitor

Monitors device presence on the network using the VOO router API and sends Telegram notifications.

## Features

- **Auto-discovers** all devices from router
- **Logs arrivals/departures** to CSV for statistics
- **Sends Telegram notifications** for specified devices
- **Router control** - block/unblock sites and devices
- Runs as a **systemd service**

## Telegram Bot Commands

### Presence Monitoring
| Command | Description |
|---------|-------------|
| `/status` | Current device status |
| `/stats` | Presence statistics |
| `/today` | Today's activity |
| `/week` | This week's summary |
| `/devices` | List all devices |
| `/help` | Show all commands |

### Site Blocking
| Command | Description |
|---------|-------------|
| `/block <site>` | Block a website (e.g., `/block facebook.com`) |
| `/unblock <site>` | Unblock a website |
| `/blocklist` | Show blocked sites |

### Device Control
| Command | Description |
|---------|-------------|
| `/kick <device>` | Kick device off network (by name) |
| `/allow <device>` | Allow device back on network |
| `/banned` | Show blocked/kicked devices |

## Files

| File | Description |
|------|-------------|
| `monitor.py` | Main monitor service |
| `telegram_bot.py` | Telegram bot with commands |
| `telegram_notifier.py` | Simple notification sender |
| `router_client.py` | VOO router API client (read-only) |
| `router_control.py` | VOO router control (block/kick) |
| `presence_detector.py` | Device presence detection logic |
| `presence_logger.py` | CSV logging for statistics |
| `config.example.py` | Example configuration |
| `phone-monitor.service` | Systemd service file |

## Installation

1. Copy files to your server:
   ```bash
   mkdir -p ~/phone-presence-monitor
   cp *.py ~/phone-presence-monitor/
   ```

2. Create configuration:
   ```bash
   cp config.example.py config.py
   # Edit config.py with your settings
   ```

3. Install dependencies:
   ```bash
   pip install requests
   ```

4. Set up systemd service:
   ```bash
   sudo cp phone-monitor.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable phone-monitor
   sudo systemctl start phone-monitor
   ```

## Configuration

Edit `config.py` with:
- `TELEGRAM_BOT_TOKEN` - Your Telegram bot token
- `TELEGRAM_CHAT_ID` - Your Telegram chat ID
- `ROUTER_URL` - Router URL (default: http://192.168.0.1)
- `ROUTER_USERNAME` - Router admin username
- `ROUTER_PASSWORD` - Router admin password
- `TRACKED_DEVICES` - List of device names to track

## Router Compatibility

Tested with VOO Technicolor routers using PBKDF2 authentication.
May work with other Technicolor routers with similar APIs.
