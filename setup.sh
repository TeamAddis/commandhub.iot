#!/bin/bash
set -e

# ─────────────────────────────────────────────────────────────────────────────
# setup.sh — Install and configure the commandhub.iot service on Raspberry Pi
# ─────────────────────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 1. Require root
if [[ "$EUID" -ne 0 ]]; then
    echo "Error: This script must be run as root. Use: sudo ./setup.sh"
    exit 1
fi

echo "==> [1/8] Updating apt and installing Python dependencies..."
apt-get update -qq
apt-get install -y python3 python3-pip python3-venv

# 2. Create virtual environment (idempotent — skipped if venv already exists)
echo "==> [2/8] Setting up Python virtual environment..."
if [[ ! -d "$SCRIPT_DIR/venv" ]]; then
    python3 -m venv "$SCRIPT_DIR/venv"
    echo "     Virtual environment created at $SCRIPT_DIR/venv"
else
    echo "     Virtual environment already exists, skipping creation."
fi

# 3. Install Python dependencies
echo "==> [3/8] Installing Python dependencies from requirements.txt..."
"$SCRIPT_DIR/venv/bin/pip" install --quiet --upgrade pip
"$SCRIPT_DIR/venv/bin/pip" install --quiet -r "$SCRIPT_DIR/requirements.txt"

# 4. Check for .env file
echo "==> [4/8] Checking for .env configuration file..."
if [[ ! -f "$SCRIPT_DIR/.env" ]]; then
    echo ""
    echo "  ┌─────────────────────────────────────────────────────────────────┐"
    echo "  │  WARNING: No .env file found!                                   │"
    echo "  │                                                                 │"
    echo "  │  Before running this script, copy the example file and fill in │"
    echo "  │  your values:                                                   │"
    echo "  │                                                                 │"
    echo "  │    cp .env.example .env                                         │"
    echo "  │    nano .env                                                    │"
    echo "  │                                                                 │"
    echo "  │  Then re-run: sudo ./setup.sh                                   │"
    echo "  └─────────────────────────────────────────────────────────────────┘"
    echo ""
    exit 1
fi

# 5. Install systemd service file (replace placeholder paths with actual project dir)
echo "==> [5/8] Installing systemd service file..."
sed "s|/home/pi/commandhub.iot|$SCRIPT_DIR|g" \
    "$SCRIPT_DIR/commandhub.service" \
    > /etc/systemd/system/commandhub.service
echo "     Installed commandhub.service to /etc/systemd/system/ (paths set to $SCRIPT_DIR)"

# 6. Reload systemd
echo "==> [6/8] Reloading systemd daemon..."
systemctl daemon-reload

# 7. Enable service
echo "==> [7/8] Enabling commandhub service (start on boot)..."
systemctl enable commandhub

# 8. Start (or restart) service
echo "==> [8/8] Starting commandhub service..."
if systemctl is-active --quiet commandhub; then
    systemctl restart commandhub
    echo "     Service restarted."
else
    systemctl start commandhub
    echo "     Service started."
fi

echo ""
echo "  ✅  commandhub.iot is running!"
echo ""
echo "  Check service status:  sudo systemctl status commandhub"
echo "  View live logs:        journalctl -u commandhub -f"
echo "  Swagger UI:            http://localhost:8000/docs"
echo ""
