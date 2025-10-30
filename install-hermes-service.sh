#!/bin/bash

# Hermes Systemd Service Installation Script
# This script sets up Hermes as a systemd service with API token authentication
#
# Environment Variables:
#   HERMES_API_TOKEN  - Custom API token (generated if not provided)
#   HERMES_DATA_DIR   - Custom data directory (defaults to /var/www/html)
#   HERMES_TEMP_DIR   - Custom temporary directory (defaults to HERMES_DATA_DIR)
#
# Usage Examples:
#   sudo ./install-hermes-service.sh
#   sudo HERMES_DATA_DIR=/custom/path ./install-hermes-service.sh
#   sudo HERMES_API_TOKEN=mytoken HERMES_DATA_DIR=/custom/path ./install-hermes-service.sh
#   sudo HERMES_TEMP_DIR=/tmp/hermes HERMES_DATA_DIR=/opt/data ./install-hermes-service.sh

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "This script must be run as root (use sudo)"
    exit 1
fi

print_step "Setting up Hermes systemd service..."

# Detect container runtime (Docker or Podman)
if command -v docker >/dev/null 2>&1 && systemctl is-active --quiet docker.service 2>/dev/null; then
    CONTAINER_RUNTIME="docker"
    CONTAINER_SERVICE="docker.service"
    CONTAINER_COMMAND="/usr/bin/docker"
    print_step "Detected Docker as container runtime"
elif command -v podman >/dev/null 2>&1; then
    CONTAINER_RUNTIME="podman"
    CONTAINER_SERVICE=""  # Podman doesn't require a system service
    CONTAINER_COMMAND="/usr/bin/podman"
    print_step "Detected Podman as container runtime"
else
    print_error "Neither Docker nor Podman found. Please install one of them first."
    exit 1
fi

# Configuration
SERVICE_NAME="hermes"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
ENV_DIR="/etc/hermes"
ENV_FILE="${ENV_DIR}/hermes.env"
DATA_DIR="${HERMES_DATA_DIR:-/var/www/html}"
TEMP_DIR="${HERMES_TEMP_DIR:-$DATA_DIR}"
SYSTEM_USER="hermes"

# Generate API token if not provided
if [ -z "$HERMES_API_TOKEN" ]; then
    print_step "Generating secure API token..."
    HERMES_API_TOKEN=$(openssl rand -hex 32)
    print_success "Generated API token: ${HERMES_API_TOKEN:0:16}..."
else
    print_step "Using provided API token: ${HERMES_API_TOKEN:0:16}..."
fi

# Check data directory configuration
if [ "$DATA_DIR" = "/var/www/html" ]; then
    print_step "Using default data directory: $DATA_DIR"
else
    print_step "Using custom data directory: $DATA_DIR"
fi

# Check temp directory configuration
if [ "$TEMP_DIR" = "$DATA_DIR" ]; then
    print_step "Using data directory for temporary files: $TEMP_DIR"
else
    print_step "Using custom temporary directory: $TEMP_DIR"
fi

# Create environment directory
print_step "Creating environment directory..."
mkdir -p "$ENV_DIR"
chmod 700 "$ENV_DIR"

# Create environment file
print_step "Creating environment file..."
cat > "$ENV_FILE" << EOF
# Hermes Configuration
# Generated on $(date)
HERMES_API_TOKEN=$HERMES_API_TOKEN
HERMES_DATA_DIR=$DATA_DIR
HERMES_TEMP_DIR=$TEMP_DIR
EOF

# Secure the environment file
chmod 600 "$ENV_FILE"
print_success "Environment file created at $ENV_FILE"

# Create dedicated system user for Hermes
print_step "Creating dedicated system user..."
if ! id "$SYSTEM_USER" &>/dev/null; then
    useradd -r -s /bin/false -c "Hermes Archive Service" -d /nonexistent "$SYSTEM_USER"
    print_success "Created system user: $SYSTEM_USER"
else
    print_step "System user $SYSTEM_USER already exists"
fi

# Get the user's UID and GID
HERMES_UID=$(id -u "$SYSTEM_USER")
HERMES_GID=$(id -g "$SYSTEM_USER")
print_step "Using UID:GID $HERMES_UID:$HERMES_GID for container user mapping"

# Create systemd service file
print_step "Creating systemd service file..."

# Create different service files based on container runtime
if [ "$CONTAINER_RUNTIME" = "docker" ]; then
    cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Hermes Archive Extraction Service
Documentation=https://github.com/hermesbaby/hermes
After=docker.service
Requires=docker.service

[Service]
Type=forking
RemainAfterExit=yes
EnvironmentFile=$ENV_FILE
ExecStartPre=-$CONTAINER_COMMAND stop $SERVICE_NAME
ExecStartPre=-$CONTAINER_COMMAND rm $SERVICE_NAME
ExecStart=$CONTAINER_COMMAND run -d \\
    --name $SERVICE_NAME \\
    --user $HERMES_UID:$HERMES_GID \\
    -v "\${HERMES_DATA_DIR}":/www-root \\
    -v "\${HERMES_TEMP_DIR}":/temp-root \\
    -e HERMES_BASE_DIRECTORY="/www-root" \\
    -e HERMES_TEMP_DIRECTORY="/temp-root" \\
    -e HERMES_API_TOKEN="\${HERMES_API_TOKEN}" \\
    -p 8000:8000 \\
    --restart unless-stopped \\
    docker.cloudsmith.io/hermesbaby/hermes/hermes:latest
ExecStop=$CONTAINER_COMMAND stop $SERVICE_NAME
ExecStopPost=$CONTAINER_COMMAND rm $SERVICE_NAME
TimeoutStartSec=0
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
else
    # Podman service file (no service dependency needed)
    cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Hermes Archive Extraction Service
Documentation=https://github.com/hermesbaby/hermes
After=network-online.target
Wants=network-online.target

[Service]
Type=forking
RemainAfterExit=yes
EnvironmentFile=$ENV_FILE
ExecStartPre=-$CONTAINER_COMMAND stop $SERVICE_NAME
ExecStartPre=-$CONTAINER_COMMAND rm $SERVICE_NAME
ExecStart=$CONTAINER_COMMAND run -d \\
    --name $SERVICE_NAME \\
    --user $HERMES_UID:$HERMES_GID \\
    -v "\${HERMES_DATA_DIR}":/www-root \\
    -v "\${HERMES_TEMP_DIR}":/temp-root \\
    -e HERMES_BASE_DIRECTORY="/www-root" \\
    -e HERMES_TEMP_DIRECTORY="/temp-root" \\
    -e HERMES_API_TOKEN="\${HERMES_API_TOKEN}" \\
    -p 8000:8000 \\
    --restart unless-stopped \\
    docker.cloudsmith.io/hermesbaby/hermes/hermes:latest
ExecStop=$CONTAINER_COMMAND stop $SERVICE_NAME
ExecStopPost=$CONTAINER_COMMAND rm $SERVICE_NAME
TimeoutStartSec=0
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
fi

print_success "Service file created at $SERVICE_FILE"

# Reload systemd and enable service
print_step "Reloading systemd daemon..."
systemctl daemon-reload

print_step "Enabling Hermes service..."
systemctl enable "$SERVICE_NAME"

# Pull the container image
print_step "Pulling Hermes container image..."
$CONTAINER_COMMAND pull docker.cloudsmith.io/hermesbaby/hermes/hermes:latest

# Start the service
print_step "Starting Hermes service..."
systemctl start "$SERVICE_NAME"

# Wait a moment for the service to start
sleep 3

# Check service status
print_step "Checking service status..."
if systemctl is-active --quiet "$SERVICE_NAME"; then
    print_success "Hermes service is running!"
else
    print_error "Service failed to start. Check logs with: journalctl -u $SERVICE_NAME"
    exit 1
fi

# Test the service
print_step "Testing Hermes API..."
if curl -s http://localhost:8000/health > /dev/null; then
    HEALTH_RESPONSE=$(curl -s http://localhost:8000/health)
    print_success "Hermes API is responding: $HEALTH_RESPONSE"
else
    print_warning "Hermes API is not responding yet. It may still be starting up."
fi

print_success "Installation completed successfully!"
echo
echo "📋 Service Information:"
echo "   Service name: $SERVICE_NAME"
echo "   Service file: $SERVICE_FILE"
echo "   Environment file: $ENV_FILE"
echo "   Data directory: $DATA_DIR"
echo "   Temp directory: $TEMP_DIR"
echo "   API endpoint: http://localhost:8000"
echo
echo "🔑 Your API token: $HERMES_API_TOKEN"
echo "   (Also stored securely in $ENV_FILE)"
echo
echo "🎛️  Service Management Commands:"
echo "   Start:    sudo systemctl start $SERVICE_NAME"
echo "   Stop:     sudo systemctl stop $SERVICE_NAME"
echo "   Restart:  sudo systemctl restart $SERVICE_NAME"
echo "   Status:   sudo systemctl status $SERVICE_NAME"
echo "   Logs:     sudo journalctl -u $SERVICE_NAME -f"
echo "   Enable:   sudo systemctl enable $SERVICE_NAME"
echo "   Disable:  sudo systemctl disable $SERVICE_NAME"
echo
echo "🧪 Test the service:"
echo "   # Health check"
echo "   curl http://localhost:8000/health"
echo
echo "   # Upload test (create test.tar.gz first)"
echo "   echo 'Hello World' > test.txt && tar -czf test.tar.gz test.txt"
echo "   curl -X PUT -F \"file=@test.tar.gz\" \\"
echo "     -H \"Authorization: Bearer $HERMES_API_TOKEN\" \\"
echo "     http://localhost:8000/test/upload"
echo
echo "🔧 Additional Management:"
echo "   # View configuration (API token, data directory, and temp directory)"
echo "   sudo cat /etc/hermes/hermes.env"
echo "   # Update container image"
echo "   sudo $CONTAINER_COMMAND pull docker.cloudsmith.io/hermesbaby/hermes/hermes:latest"
echo "   sudo systemctl restart $SERVICE_NAME"
echo "   # Remove service completely"
echo "   sudo systemctl stop $SERVICE_NAME && sudo systemctl disable $SERVICE_NAME"
echo "   sudo rm /etc/systemd/system/$SERVICE_NAME.service && sudo systemctl daemon-reload"
echo
echo "🔄 Update Configuration:"
echo "   # To change API token, data directory, or temp directory after installation:"
echo "   sudo nano /etc/hermes/hermes.env"
echo "   sudo systemctl restart $SERVICE_NAME"
echo
echo "   # If changing data or temp directory, also update ownership:"
echo "   sudo chown -R \$(id -u hermes):\$(id -g hermes) /new/directory/path"
echo "   sudo chmod -R 755 /new/directory/path"
echo
echo "⚠️  Security Notes:"
echo "   - Environment file is secured with 600 permissions"
echo "   - Only root can read the API token"
echo "   - Dedicated system user '$SYSTEM_USER' created (UID: $HERMES_UID)"
echo "   - Container runs with mapped user $HERMES_UID:$HERMES_GID"
echo "   - Data directory owned by system user '$SYSTEM_USER'"
echo "   - Service follows production security best practices"