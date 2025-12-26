# VOO Technicolor Router API Map (CGA4233VOO)

## Overview
- **Model**: Technicolor CGA4233VOO
- **Firmware**: CGA4233VOO-19.3B1-015-E20-RMQ
- **Base URL**: `http://192.168.0.1`
- **API Base**: `/api/v1/`

## Authentication
Uses PBKDF2 challenge-response:
1. POST `/api/v1/session/login` with `password=seeksalthash` to get salt
2. Hash password: `pbkdf2(pbkdf2(password, salt), saltwebui)`
3. POST `/api/v1/session/login` with hashed password
4. Get CSRF token from `auth` cookie, use in `X-CSRF-TOKEN` header

---

## 🟢 WORKING ENDPOINTS

### Session Management
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/session/menu` | GET | Get menu structure & available APIs |
| `/api/v1/session/login` | POST | Authenticate |
| `/api/v1/session/logout` | POST | End session |

---

### 📡 Network & Devices

#### `/api/v1/host` - Connected Devices
```json
{
  "LanIPAddress": "192.168.0.1",
  "LanMode": "router",
  "hostTbl": [
    {
      "physaddress": "MAC address",
      "ipaddress": "192.168.0.x",
      "hostname": "device name",
      "active": "true/false",
      "leasetimeremaining": "seconds",
      "addresssource": "DHCP/Static",
      "rssi": "signal strength (-200 = wired)",
      "layer1interface": "Device.Ethernet.Interface.X",
      "ipv41": "IPv4 address",
      "ipv61": "IPv6 address"
    }
  ]
}
```
**Use cases**: List all devices, check online status, get MAC/IP mappings

#### `/api/v1/host/hostTbl` - Just the device table
Same as above but only returns `hostTbl` array.

#### `/api/v1/devicecontrol` - WAN/LAN Settings
```json
{
  "LanMode": "router",
  "LanIPAddress": "192.168.0.1",
  "LanSubnetMask": "255.255.255.0",
  "WanAddressMode": "DHCP",
  "IPAddressRT": "public IP",
  "HostName": "Docsis-Gateway"
}
```
**Use cases**: Get public IP, check router mode

#### `/api/v1/troubleshooting` - Network Diagnostics
```json
{
  "pingHost": "target",
  "pingState": "None/Running/Complete",
  "PingStatistics": "results",
  "trHost": "traceroute target",
  "trState": "None/Running/Complete",
  "trTbl": [],
  "ARPTbl": [
    {"IPAddress": "x.x.x.x", "MACAddress": "xx:xx:xx:xx:xx:xx"}
  ]
}
```
**Use cases**: Run ping/traceroute, view ARP table (all devices that communicated recently)

---

### 🔒 Security & Filtering

#### `/api/v1/macfilter` - Device Blocking (MAC Filter)
```json
{
  "enable": "true/false",
  "allowall": "true/false",  // true=blocklist mode, false=allowlist mode
  "macfilterTbl": [
    {
      "macaddress": "XX:XX:XX:XX:XX:XX",
      "description": "Device name",
      "type": "Block/Allow",
      "alwaysblock": "true/false",
      "starttime": "HH:MM",
      "endtime": "HH:MM",
      "blockdays": "Mon,Tue,Wed..."
    }
  ]
}
```
**Use cases**: Block/unblock devices, schedule access, parental controls

#### `/api/v1/sitefilter` - Website Blocking
```json
{
  "enable": "true/false",
  "sitefilterTbl": [
    {
      "site": "example.com",
      "blockmethod": "URL",
      "alwaysblock": "true/false",
      "starttime": "",
      "endtime": "",
      "blockdays": ""
    }
  ],
  "sitetrustedTbl": []  // Devices exempt from filtering
}
```
**Use cases**: Block websites, schedule access

#### `/api/v1/servicefilter` - Port/Service Blocking
```json
{
  "enable": "true/false",
  "servicefilterTbl": [
    {
      "description": "Service name",
      "startport": "80",
      "endport": "443",
      "protocol": "TCP/UDP/Both",
      "alwaysblock": "true/false"
    }
  ]
}
```
**Use cases**: Block specific ports/services

#### `/api/v1/ipfilter` - IP Range Filtering
```json
{
  "ipfilterTbl": [
    {"from": "192.168.0.100", "to": "192.168.0.200", "block": "true"}
  ],
  "ipfilterTblv6": []
}
```
**Use cases**: Block IP ranges

#### `/api/v1/firewall` - Firewall Settings
```json
{
  "FirewallLevel": "Low/Medium/High/Custom",
  "UPnPIGD": "true/false",
  "FilterAnonymousInternetRequests": "true/false",
  "L2TPPassthrough": "true/false",
  "PPTPPassthrough": "true/false",
  "IPSecPassthrough": "true/false",
  "WebBlockCookies": "true/false",
  "WebBlockActiveX": "true/false",
  "WebBlockJava": "true/false",
  "FilterHTTP": "true/false",
  "FilterP2P": "true/false",
  "BlockIPSpoof": "true/false",
  "BlockTCPSynFlood": "true/false",
  "BlockUDPFlood": "true/false"
}
```
**Use cases**: Configure firewall rules, enable/disable protections

---

### 🌐 Port Forwarding & NAT

#### `/api/v1/portforward` - Port Forwarding
```json
{
  "pwEnable": "true/false",
  "portmappingTbl": [
    {
      "enable": "true",
      "description": "SSH",
      "protocol": "TCP",
      "externalport": "22",
      "internalport": "22",
      "internalclient": "192.168.0.100"
    }
  ],
  // ALG (Application Layer Gateway) settings:
  "FTP": "true/false",
  "SIP": "true/false",
  "H323": "true/false",
  "PPTP": "true/false",
  "IPSEC": "true/false"
}
```
**Use cases**: Forward ports to internal servers, configure ALGs

#### `/api/v1/porttrigger` - Port Triggering
```json
{
  "ptEnable": "true/false",
  "porttriggerTbl": []
}
```

#### `/api/v1/dmz` - DMZ Host
```json
{
  "enable": "true/false",
  "host": "192.168.0.x",
  "hostv6": "IPv6 address"
}
```
**Use cases**: Expose a device to all incoming traffic (⚠️ security risk)

#### `/api/v1/upnp` - UPnP Settings
```json
{
  "enableupnp": "true/false",
  "adperiod": "1800",
  "timetolive": "5"
}
```

---

### 📊 System & Monitoring

#### `/api/v1/system` - System Information
```json
{
  "Manufacturer": "Technicolor",
  "ModelName": "CGA4233VOO",
  "SerialNumber": "CP2117KA4GE",
  "SoftwareVersion": "CGA4233VOO-19.3B1-015-E20-RMQ",
  "HardwareVersion": "1.0.0",
  "UpTime": "seconds since boot",
  "LocalTime": "2025-12-26 07:50:29",
  "MemTotal": "364436",
  "MemFree": "168400",
  "CPUUsage": "3",
  "MACAddressRT": "router MAC",
  "CMStatus": "OPERATIONAL"
}
```
**Use cases**: Monitor router health, check uptime, get system info

#### `/api/v1/report` - Security Logs
```json
{
  "LogTbl": [
    {
      "Count": "808",
      "Type": "Firewall Blocked",
      "time": "Dec 26 07:50:48 2025",
      "Des": "FW.WAN2SELF DROP"
    },
    {
      "Type": "Device Blocked",
      "Des": "Device MAC:XX:XX:XX:XX:XX:XX"
    }
  ]
}
```
**Use cases**: View blocked attempts, security monitoring, intrusion detection

#### `/api/v1/reset` - Reboot/Reset
```json
{
  "MtaEnable": "true"
}
```
POST to trigger reboot/reset.

---

### 🔧 Remote Access

#### `/api/v1/remoteaccess` - Remote Management
```json
{
  "httpenable": "true/false",
  "httpport": "8080",
  "httpsenable": "true/false",
  "httpsport": "443",
  "fromanyip": "true/false",
  "startip": "allowed IP range start",
  "endip": "allowed IP range end"
}
```
**Use cases**: Enable/disable remote management (⚠️ security sensitive)

#### `/api/v1/ddns` - Dynamic DNS
```json
{
  "enable": "true/false",
  "ddnsTbl": [
    {
      "enable": "true",
      "servicename": "www.duckdns.org",
      "domain": "yourdomain.duckdns.org",
      "username": "token"
    }
  ]
}
```
**Use cases**: Configure dynamic DNS for remote access

---

### 📞 Telephony (MTA)

#### `/api/v1/mta` - VoIP/Phone Status
```json
{
  "Enable": "true",
  "FQDN": "phone.domain",
  "IPAddress": "MTA IP",
  "status1": "On-Hook/Off-Hook",
  "status2": "On-Hook/Off-Hook",
  "EMTAProvisState": "Telephony-RegComplete"
}
```
**Use cases**: Monitor phone line status

---

### 🔍 Other Endpoints

#### `/api/v1/ippassthrough` - IP Passthrough/Bridge Mode
```json
{
  "enable": "true/false",
  "maxCpeAllowed": "2",
  "cpeTbl": []
}
```

#### `/api/v1/accesscontrol` - Access Control Summary
```json
{
  "siteEnable": "true/false",
  "serviceEnable": "true/false", 
  "deviceEnable": "true/false"
}
```

#### `/api/v1/insightC` - WiFi Insight
```json
{
  "ReqC": "None",
  "InsightTbl": []
}
```

---

## 🔴 ENDPOINTS THAT TIMEOUT/FAIL

These may need longer timeouts or special handling:
- `/api/v1/wifi` - WiFi settings (times out, may need different approach)
- `/api/v1/modem` - DOCSIS modem stats (times out)
- `/api/v1/dhcp` - DHCP settings (404)
- `/api/v1/routing` - Routing table (times out)
- `/api/v1/internet` - Internet status (404)
- `/api/v1/lanmanage` - LAN management (404)

---

## 🎯 FUN PROJECT IDEAS

### 1. **Network Monitor Dashboard**
- Real-time device tracking with `/api/v1/host`
- Bandwidth/connection monitoring
- Alert when new devices join

### 2. **Automated Security Response**
- Monitor `/api/v1/report` for attacks
- Auto-block suspicious IPs
- Send alerts on intrusion attempts

### 3. **Parental Controls Bot**
- Schedule-based device blocking via `/api/v1/macfilter`
- Website blocking via `/api/v1/sitefilter`
- "Homework mode" - block gaming/social media

### 4. **Wake-on-LAN Integration**
- Use ARP table from `/api/v1/troubleshooting`
- Track device sleep/wake patterns

### 5. **Dynamic Port Forwarding**
- Auto-configure port forwards via `/api/v1/portforward`
- Temporary access for specific services

### 6. **Router Health Monitor**
- Track CPU/memory via `/api/v1/system`
- Alert on high usage or issues
- Uptime monitoring

### 7. **Guest Network Manager**
- Temporary device access
- Auto-expire after time limit

### 8. **Network Topology Mapper**
- Build visual map from device data
- Track device relationships

---

## 📝 Notes

- All POST requests need `X-CSRF-TOKEN` header
- Session timeout is 600 seconds (10 minutes)
- Some endpoints return arrays directly (not wrapped in `data`)
- MAC addresses should be uppercase with colons
- Times are in 24-hour format "HH:MM"
- Days are comma-separated: "Mon,Tue,Wed,Thu,Fri,Sat,Sun"
