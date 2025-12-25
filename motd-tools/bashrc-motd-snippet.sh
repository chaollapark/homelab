# ============================================
# Network Scanner Tools (added for SSH login)
# ============================================

# Add ~/bin to PATH if not already there
if [[ ":$PATH:" != *":$HOME/bin:"* ]]; then
    export PATH="$HOME/bin:$PATH"
fi

# Show network scan on SSH login
if [[ -n "$SSH_CONNECTION" ]]; then
    echo ""
    echo -e "\033[1;36m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m"
    echo -e "\033[1m🖥️  Welcome back! Network Status (cached)\033[0m"
    ~/bin/network-scan 2>/dev/null || echo "Network scan unavailable"
    # Show Redmi Note 12 Pro 5G presence
    # Check both scan cache and cross-reference with known Redmi MACs in device names
    if grep -qiE "redmi|5E:9C:18:23:07:78|72:4C:44:DD:66:F6|8E:7D:29:38:58:7F|92:D4:3D:67:89:E5|A2:73:1A:EF:12:89|A6:0A:02:2C:BC:8F|EE:AE:38:6D:C7:16" ~/.local/share/network-scan/scan_cache.json 2>/dev/null; then
        echo -e "\033[1m📱 Redmi Note 12 Pro 5G:\033[0m \033[0;32m\033[1mPRESENT\033[0m"
    else
        echo -e "\033[1m📱 Redmi Note 12 Pro 5G:\033[0m \033[0;31m\033[1mABSENT\033[0m"
    fi
    echo -e "\033[1;36m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m"
    echo -e "\033[1mQuick Commands:\033[0m (work offline - no internet needed)"
    echo -e "  \033[1;33mscan\033[0m -v|-a|--live     Network scan (verbose/all/fresh)"
    echo -e "  \033[1;33mrouter\033[0m devices        List devices from router"
    echo -e "  \033[1;33mrouter\033[0m kick <name>    Block device from network"
    echo -e "  \033[1;33mrouter\033[0m allow <name>   Unblock device"
    echo -e "  \033[1;33mrouter\033[0m block <site>   Block website"
    echo -e "  \033[1;33mrouter\033[0m banned         Show blocked devices/sites"
    echo -e "  \033[1;33mrouter\033[0m --help         Full router command help"
    echo -e "  \033[1;33mdns-traffic\033[0m            Analyze DNS queries per device"
    echo -e "\033[1;36m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m"
    echo ""
fi
