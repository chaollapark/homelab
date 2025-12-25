# MOTD Tools

Network scanning and router management tools for SSH login MOTD and command-line use.

## Tools

### router
**Local CLI tool for VOO router management** - works offline (no internet needed)

```bash
router                      # Show help
router devices              # List all devices from router
router devices --active     # List only active devices
router kick <name>          # Block device by name
router allow <name>         # Unblock device
router block <site>         # Block a website
router unblock <site>       # Unblock a website
router banned               # Show blocked devices
router sites                # Show blocked sites
router blocked              # Show all blocked (sites + devices)
router status               # Test router connection
```

### network-scan
**Network scanner with device tracking**

```bash
scan                        # Quick summary (cached)
scan -v                     # Verbose with details
scan -a                     # Show ALL devices
scan --live                 # Force fresh scan
scan --list                 # List known devices
scan --name MAC "Name"      # Name a device
scan --forget MAC           # Forget a device
```

### dns-traffic
**DNS traffic analyzer** - see what domains devices are querying

```bash
dns-traffic capture         # Start live capture (requires sudo)
dns-traffic analyze <file>  # Analyze saved capture
dns-traffic --help          # Full help
```

### voo-router-api
**Low-level VOO router API client** with PBKDF2 authentication

```bash
voo-router-api --discover   # Discover API endpoints
voo-router-api --devices    # List devices (JSON)
```

### voo-router-sync
**Sync device names from router to local database**

```bash
voo-router-sync             # Show devices from router
voo-router-sync --update    # Update device_names.db
voo-router-sync --json      # Output as JSON
```

## MOTD Setup

Add the contents of `bashrc-motd-snippet.sh` to your `~/.bashrc` to show:
- Network status on SSH login
- Device presence (e.g., Redmi Note 12 Pro 5G)
- Quick command reference

```bash
cat bashrc-motd-snippet.sh >> ~/.bashrc
```

## Installation

1. Copy tools to `~/bin`:
   ```bash
   cp router network-scan dns-traffic voo-router-* ~/bin/
   chmod +x ~/bin/router ~/bin/network-scan ~/bin/dns-traffic ~/bin/voo-router-*
   ```

2. Create config directory:
   ```bash
   mkdir -p ~/bin/config
   cp config/router.conf.example ~/bin/config/router.conf
   # Edit router.conf with your credentials
   ```

3. Create data directory:
   ```bash
   mkdir -p ~/.local/share/network-scan
   ```

4. Add MOTD to bashrc:
   ```bash
   cat bashrc-motd-snippet.sh >> ~/.bashrc
   ```

## Configuration

Create `~/bin/config/router.conf`:
```ini
[router]
url = http://192.168.0.1
username = admin
password = your_password

[network]
network = 192.168.0.0/24
interface = eth0
my_ip = 192.168.0.100
```

## Systemd Services

- `network-scan.service` + `network-scan.timer` - Periodic scanning
- `seclab.service` - Security lab container

## Files

| File | Description |
|------|-------------|
| `router` | Router CLI tool (block/kick/devices) |
| `network-scan` | Network scanner with MOTD output |
| `network-scan-daemon` | Background scanning daemon |
| `dns-traffic` | DNS traffic analyzer |
| `voo-router-api` | Low-level router API client |
| `voo-router-sync` | Sync device names from router |
| `bashrc-motd-snippet.sh` | MOTD configuration for ~/.bashrc |
| `config/router.conf.example` | Example router configuration |

## Router Compatibility

Tested with VOO Technicolor routers using PBKDF2 authentication.
