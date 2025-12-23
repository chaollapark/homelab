# Phone Presence Monitor

A Python application that monitors your phone's presence on the local network and sends Telegram notifications when the phone connects or disconnects.

## Features

- 📱 Monitors phone presence via network ping
- 📬 Sends Telegram notifications on state changes
- 🔄 Continuous monitoring with configurable intervals
- 🖥️ Cross-platform (Linux, macOS, Windows)

## Setup

### 1. Create a Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Send `/newbot` and follow the instructions
3. Copy the bot token you receive

### 2. Get Your Chat ID

1. Search for `@userinfobot` or `@get_id_bot` on Telegram
2. Start a chat and it will show your chat ID
3. Copy your chat ID

### 3. Configure the App

Edit `config.py` and fill in your details:

```python
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"  # Your bot token
TELEGRAM_CHAT_ID = "123456789"  # Your chat ID

# Phone to monitor
PHONE_IP = "192.168.0.183"  # Already configured for your Redmi
PHONE_NAME = "Redmi Note 12 Pro 5G"

# Check interval in seconds
CHECK_INTERVAL = 30
```

### 4. Run the Monitor

```bash
cd phone_presence_monitor
python3 monitor.py
```

## Running as a Background Service

### Linux (systemd)

Create `/etc/systemd/system/phone-monitor.service`:

```ini
[Unit]
Description=Phone Presence Monitor
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/phone_presence_monitor
ExecStart=/usr/bin/python3 monitor.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable phone-monitor
sudo systemctl start phone-monitor
```

### macOS (launchd)

Create `~/Library/LaunchAgents/com.phone.monitor.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.phone.monitor</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/path/to/phone_presence_monitor/monitor.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>WorkingDirectory</key>
    <string>/path/to/phone_presence_monitor</string>
</dict>
</plist>
```

Then:
```bash
launchctl load ~/Library/LaunchAgents/com.phone.monitor.plist
```

## How It Works

1. The app pings your phone's IP address at regular intervals
2. If the phone responds, it's considered "present" on the network
3. When the state changes (present → absent or absent → present), a Telegram notification is sent
4. The app handles network fluctuations by requiring multiple failed pings before declaring the phone absent

## Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token | Required |
| `TELEGRAM_CHAT_ID` | Your Telegram chat ID | Required |
| `PHONE_IP` | IP address of the phone | `192.168.0.183` |
| `PHONE_NAME` | Display name for notifications | `Redmi Note 12 Pro 5G` |
| `CHECK_INTERVAL` | Seconds between checks | `30` |
| `PING_TIMEOUT` | Ping timeout in seconds | `2` |
| `PING_ATTEMPTS` | Number of ping attempts | `3` |

## Troubleshooting

- **Phone not detected**: Make sure the phone has a static IP or DHCP reservation
- **Telegram not working**: Verify your bot token and chat ID are correct
- **Permission denied**: On some systems, ping may require elevated privileges
