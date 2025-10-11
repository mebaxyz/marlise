#!/usr/bin/env bash
# Install Marlise systemd services on Raspberry Pi or Linux system

set -e

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
SYSTEMD_DIR="$SCRIPT_DIR/systemd"
USER="${1:-$USER}"

echo "🚀 Installing Marlise systemd services for user: $USER"
echo ""

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    echo "⚠️  This script needs sudo privileges to install systemd units"
    echo "   It will be requested when needed."
    echo ""
fi

# Verify systemd directory exists
if [ ! -d "$SYSTEMD_DIR" ]; then
    echo "❌ Error: Systemd directory not found: $SYSTEMD_DIR"
    exit 1
fi

# Copy service files to systemd directory
echo "📋 Installing service files..."
sudo cp "$SYSTEMD_DIR"/*.service /etc/systemd/system/
sudo cp "$SYSTEMD_DIR"/*.target /etc/systemd/system/

# Reload systemd
echo "🔄 Reloading systemd daemon..."
sudo systemctl daemon-reload

# Enable services (but don't start yet)
echo "✅ Enabling Marlise services..."
sudo systemctl enable marlise.target
sudo systemctl enable "marlise-mod-host@${USER}.service"
sudo systemctl enable "marlise-bridge@${USER}.service"
sudo systemctl enable "marlise-session-manager@${USER}.service"
sudo systemctl enable "marlise-client-interface@${USER}.service"
sudo systemctl enable "marlise-web-client@${USER}.service"

echo ""
echo "✅ Installation complete!"
echo ""
echo "📝 Next steps:"
echo "   1. Start services:    sudo systemctl start marlise.target"
echo "   2. Check status:      systemctl status 'marlise-*@${USER}.service'"
echo "   3. View logs:         journalctl -f -u 'marlise-*@${USER}.service'"
echo "   4. Stop services:     sudo systemctl stop marlise.target"
echo ""
echo "🔧 Individual service control:"
echo "   sudo systemctl start marlise-mod-host@${USER}.service"
echo "   sudo systemctl start marlise-bridge@${USER}.service"
echo "   sudo systemctl start marlise-session-manager@${USER}.service"
echo "   sudo systemctl start marlise-client-interface@${USER}.service"
echo "   sudo systemctl start marlise-web-client@${USER}.service"
echo ""
echo "💡 Services will auto-start on boot and restart on failure"
