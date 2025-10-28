# Hermes Docker Troubleshooting Guide

## Common Issues and Solutions

### Permission Denied Error: `/var/www`

**Error Message:**
```json
{"detail":"Failed to extract archive: [Errno 13] Permission denied: '/var/www'"}
```

**Problem:**
This error occurs when the Docker container cannot create or write to the specified base directory due to permission issues. The container runs as a non-root user (`hermes` with UID 1000) but the host directory may be owned by root or have restrictive permissions.

**Solutions:**

#### Solution 1: Use Volume Mounting (Recommended)
Instead of setting the base directory to a host path directly, mount the host directory into the container:

```bash
# Stop the current container
docker stop <container_id>

# Run with proper volume mounting (no API token)
docker run -d \
  -v /var/www/html:/www-root \
  -e HERMES_BASE_DIRECTORY="/www-root" \
  -p 8000:8000 \
  docker.cloudsmith.io/hermesbaby/hermes/hermes:latest

# Run with API token security enabled
docker run -d \
  -v /var/www/html:/www-root \
  -e HERMES_BASE_DIRECTORY="/www-root" \
  -e HERMES_API_TOKEN="your-secure-token-here" \
  -p 8000:8000 \
  docker.cloudsmith.io/hermesbaby/hermes/hermes:latest
```

#### Solution 2: Fix Host Directory Permissions
Ensure the host directory has the correct ownership and permissions:

```bash
# Create the directory if it doesn't exist
sudo mkdir -p /var/www/html

# Change ownership to match the container user (UID 1000)
sudo chown -R 1000:1000 /var/www/html

# Set appropriate permissions
sudo chmod -R 755 /var/www/html

# Then run the container with the original command (no API token)
docker run -d \
  -e HERMES_BASE_DIRECTORY="/var/www/html" \
  -p 8000:8000 \
  docker.cloudsmith.io/hermesbaby/hermes/hermes:latest

# Or with API token security enabled
docker run -d \
  -e HERMES_BASE_DIRECTORY="/var/www/html" \
  -e HERMES_API_TOKEN="your-secure-token-here" \
  -p 8000:8000 \
  docker.cloudsmith.io/hermesbaby/hermes/hermes:latest
```

#### Solution 3: Run Container as Root (Less Secure)
If the above solutions don't work, you can run the container as root:

```bash
docker run -d \
  --user root \
  -e HERMES_BASE_DIRECTORY="/var/www/html" \
  -p 8000:8000 \
  docker.cloudsmith.io/hermesbaby/hermes/hermes:latest
```

**Note:** Running as root reduces security but may be necessary in some environments.

### API Token Security

For production deployments, it's highly recommended to enable API token authentication:

#### Generating a Secure Token

```bash
# Generate a secure random token
export HERMES_API_TOKEN=$(openssl rand -hex 32)
echo "Generated token: $HERMES_API_TOKEN"

# Or use a UUID-based token
export HERMES_API_TOKEN=$(uuidgen | tr -d '-')
echo "Generated token: $HERMES_API_TOKEN"
```

#### Running with API Token

```bash
# Volume mounting approach with API token
docker run -d \
  -v /var/www/html:/www-root \
  -e HERMES_BASE_DIRECTORY="/www-root" \
  -e HERMES_API_TOKEN="$HERMES_API_TOKEN" \
  -p 8000:8000 \
  docker.cloudsmith.io/hermesbaby/hermes/hermes:latest

# Permission fix approach with API token
docker run -d \
  -e HERMES_BASE_DIRECTORY="/var/www/html" \
  -e HERMES_API_TOKEN="$HERMES_API_TOKEN" \
  -p 8000:8000 \
  docker.cloudsmith.io/hermesbaby/hermes/hermes:latest
```

#### Using API Tokens in Requests

When API token is configured, all PUT requests require authentication:

```bash
# Method 1: Bearer token (recommended)
curl -X PUT -F "file=@test.tar.gz" \
  -H "Authorization: Bearer $HERMES_API_TOKEN" \
  http://localhost:8000/test/upload

# Method 2: X-API-Token header
curl -X PUT -F "file=@test.tar.gz" \
  -H "X-API-Token: $HERMES_API_TOKEN" \
  http://localhost:8000/test/upload

# Health endpoint remains unprotected
curl http://localhost:8000/health
```

#### API Token Error Responses

Without token when required:
```json
{"detail":"API token required. Provide via 'Authorization: Bearer <token>' or 'X-API-Token: <token>' header."}
```

With invalid token:
```json
{"detail":"Invalid API token"}
```

### Testing the Fix

After applying any of the solutions, test the service:

```bash
# Create a test archive
echo "Hello World" > test.txt
tar -czf test.tar.gz test.txt

# Upload the archive (no API token required)
curl -X PUT -F "file=@test.tar.gz" http://localhost:8000/test/upload

# Upload with API token using Bearer authentication
curl -X PUT -F "file=@test.tar.gz" \
  -H "Authorization: Bearer your-secure-token-here" \
  http://localhost:8000/test/upload

# Upload with API token using X-API-Token header
curl -X PUT -F "file=@test.tar.gz" \
  -H "X-API-Token: your-secure-token-here" \
  http://localhost:8000/test/upload

# Expected response (success):
# {"endpoint":"/test/upload","method":"PUT","created_path":"...","status":"extracted","archive_type":"tar.gz","filename":"test.tar.gz","file_size":133,"extracted_items":["test.txt"],"total_extracted_paths":1}
```

### Verifying Successful Extraction

If the upload was successful, you should be able to verify the extracted files:

```bash
# Check health endpoint
curl http://localhost:8000/health
# Expected: {"status":"ok","service":"hermes","version":"..."}

# Verify extracted file exists on host (for volume mount approach)
ls -la /var/www/html/test/upload/
# Should show: test.txt

# Or check inside container (for permission fix approach)
docker exec <container_id> ls -la /var/www/html/test/upload/
# Should show: test.txt
```

### Additional Debugging

Check container logs for more detailed error information:

```bash
# Get container ID
docker ps

# View logs
docker logs <container_id>

# Follow logs in real-time
docker logs -f <container_id>
```

### Directory Structure Best Practices

When using Hermes in production:

1. **Use dedicated directories**: Don't use system directories like `/var/www` directly
2. **Set proper permissions**: Ensure the container user can read/write
3. **Use volume mounts**: Mount host directories into container paths for better isolation
4. **Enable API token security**: Always use API tokens in production
5. **Regular backups**: The extracted files are only as safe as your backup strategy

### Production Setup Examples

#### Docker Command Line

```bash
# Create dedicated directory
sudo mkdir -p /opt/hermes/data
sudo chown -R 1000:1000 /opt/hermes/data

# Generate secure API token
export HERMES_API_TOKEN=$(openssl rand -hex 32)
echo "Save this token securely: $HERMES_API_TOKEN"

# Run container with full security
docker run -d \
  --name hermes \
  -v /opt/hermes/data:/app/data \
  -e HERMES_BASE_DIRECTORY="/app/data" \
  -e HERMES_API_TOKEN="$HERMES_API_TOKEN" \
  -p 8000:8000 \
  --restart unless-stopped \
  docker.cloudsmith.io/hermesbaby/hermes/hermes:latest
```

#### Docker Compose

Create a `docker-compose.yml` file:

```yaml
version: '3.8'
services:
  hermes:
    image: docker.cloudsmith.io/hermesbaby/hermes/hermes:latest
    container_name: hermes
    environment:
      - HERMES_BASE_DIRECTORY=/app/data
      - HERMES_API_TOKEN=${HERMES_API_TOKEN}  # Set in .env file
    ports:
      - "8000:8000"
    volumes:
      - hermes_data:/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s

volumes:
  hermes_data:
    driver: local
```

Create a `.env` file:

```bash
# Generate and save API token
HERMES_API_TOKEN=your-generated-token-here
```

Then run:

```bash
# Generate token and save to .env
echo "HERMES_API_TOKEN=$(openssl rand -hex 32)" > .env

# Start the service
docker-compose up -d

# Test with the token from .env
source .env
curl -X PUT -F "file=@test.tar.gz" \
  -H "Authorization: Bearer $HERMES_API_TOKEN" \
  http://localhost:8000/test/upload
```

### Systemd Service Setup

For production environments, it's recommended to run Hermes as a systemd service for automatic startup and management:

#### Automatic Installation

Use the provided installation script:

```bash
# Download and make executable
curl -O https://raw.githubusercontent.com/hermesbaby/hermes/main/install-hermes-service.sh
chmod +x install-hermes-service.sh

# Run as root
sudo ./install-hermes-service.sh
```

#### Manual Installation

Create the service files manually:

```bash
# Generate API token
export HERMES_API_TOKEN=$(openssl rand -hex 32)
echo "Save this token: $HERMES_API_TOKEN"

# Create environment directory and file
sudo mkdir -p /etc/hermes
sudo chmod 700 /etc/hermes
echo "HERMES_API_TOKEN=$HERMES_API_TOKEN" | sudo tee /etc/hermes/hermes.env
sudo chmod 600 /etc/hermes/hermes.env

# Create dedicated system user
sudo useradd -r -s /bin/false -c "Hermes Archive Service" -d /nonexistent hermes

# Get user IDs
HERMES_UID=$(id -u hermes)
HERMES_GID=$(id -g hermes)

# Create systemd service file
sudo tee /etc/systemd/system/hermes.service << EOF
[Unit]
Description=Hermes Archive Extraction Service
After=docker.service
Requires=docker.service

[Service]
Type=forking
RemainAfterExit=yes
EnvironmentFile=/etc/hermes/hermes.env
ExecStartPre=-/usr/bin/docker stop hermes
ExecStartPre=-/usr/bin/docker rm hermes
ExecStart=/usr/bin/docker run -d \\
    --name hermes \\
    --user $HERMES_UID:$HERMES_GID \\
    -v /var/www/html:/www-root \\
    -e HERMES_BASE_DIRECTORY="/www-root" \\
    -e HERMES_API_TOKEN="\${HERMES_API_TOKEN}" \\
    -p 8000:8000 \\
    --restart unless-stopped \\
    docker.cloudsmith.io/hermesbaby/hermes/hermes:latest
ExecStop=/usr/bin/docker stop hermes
ExecStopPost=/usr/bin/docker rm hermes
TimeoutStartSec=0
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Set up data directory with proper ownership
sudo mkdir -p /var/www/html
sudo chown -R hermes:hermes /var/www/html
sudo chmod -R 755 /var/www/html

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable hermes
sudo systemctl start hermes
```

#### Service Management

```bash
# Start/stop/restart the service
sudo systemctl start hermes
sudo systemctl stop hermes
sudo systemctl restart hermes

# Check service status
sudo systemctl status hermes

# View logs
sudo journalctl -u hermes -f

# Test the service
curl http://localhost:8000/health

# Test upload with API token
source /etc/hermes/hermes.env
curl -X PUT -F "file=@test.tar.gz" \
  -H "Authorization: Bearer $HERMES_API_TOKEN" \
  http://localhost:8000/test/upload
```

#### Additional Management Tasks

```bash
# Update to latest Docker image
sudo docker pull docker.cloudsmith.io/hermesbaby/hermes/hermes:latest
sudo systemctl restart hermes

# View API token
sudo cat /etc/hermes/hermes.env

# Check container status
sudo docker ps | grep hermes
sudo docker logs hermes

# Remove service completely
sudo systemctl stop hermes
sudo systemctl disable hermes
sudo rm /etc/systemd/system/hermes.service
sudo rm -rf /etc/hermes
sudo systemctl daemon-reload
```

### Environment Variables Reference

#### Required Variables
- **`HERMES_BASE_DIRECTORY`**: Base directory for file extraction (required)

#### Optional Variables
- **`HERMES_API_TOKEN`**: API token for securing PUT requests (highly recommended for production)

#### Example Configurations

```bash
# Minimal setup (development only)
docker run -d \
  -e HERMES_BASE_DIRECTORY="/tmp/hermes" \
  -p 8000:8000 \
  docker.cloudsmith.io/hermesbaby/hermes/hermes:latest

# Production setup with security
docker run -d \
  -v /opt/hermes:/app/data \
  -e HERMES_BASE_DIRECTORY="/app/data" \
  -e HERMES_API_TOKEN="$(openssl rand -hex 32)" \
  -p 8000:8000 \
  --restart unless-stopped \
  docker.cloudsmith.io/hermesbaby/hermes/hermes:latest
```