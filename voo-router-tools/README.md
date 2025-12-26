# VOO Router Tools

Python tools for interacting with VOO Technicolor routers using PBKDF2 authentication.

## Tools

### voo-router-api
General API client for the VOO router. Can discover endpoints and fetch device lists.

```bash
./voo-router-api --discover  # Discover available API endpoints
./voo-router-api --devices   # List connected devices
./voo-router-api --json      # Output as JSON
```

### voo-router-sync
Sync device names from the router to a local database.

```bash
./voo-router-sync           # Show devices from router
./voo-router-sync --update  # Update device_names.db
./voo-router-sync --json    # Output as JSON
./voo-router-sync --active  # Show only active devices
```

## Configuration

1. Copy `router.conf.example` to `~/.config/router.conf` or `~/bin/config/router.conf`
2. Fill in your router credentials:

```ini
[router]
url = http://192.168.0.1
username = your_username
password = your_password
```

## Requirements

- Python 3.6+
- requests
- cryptography (optional, falls back to hashlib)
