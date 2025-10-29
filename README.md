# HermesBaby-Hermes

**Hermes** is a lightweight FastAPI service that acts as a universal PUT endpoint for archive file extraction. It accepts PUT requests with archive files (tar.gz, ZIP, 7z) to any endpoint path, creates the corresponding directory structure on the local filesystem, and extracts the archive contents with their internal directory structure, making it useful for dynamic file system provisioning, deployment, and development workflows.

## What This Docker Image Does

The Hermes Docker image provides:

- **Universal PUT Archive Extraction Service**: Accepts PUT requests with archive files (tar.gz, ZIP, 7z) to any endpoint path, creates directory structure, and extracts archive contents
- **Multiple Archive Format Support**: Supports tar.gz, .tgz, ZIP, and 7z archive formats
- **Health Check Endpoint**: Provides a `/health` endpoint for monitoring and container orchestration
- **FastAPI-based**: Built on FastAPI with automatic API documentation
- **Production Ready**: Includes proper security configuration, non-root user, and health checks

### Key Features

- 🌐 **Catch-all PUT endpoints**: Any PUT request with archive file to `/path/to/anything` creates directory structure and extracts archive contents
- � **Multiple Archive Formats**: Supports tar.gz, .tgz, ZIP (.zip), and 7z (.7z) archive formats
- �📁 **Filesystem Integration**: Creates actual directories on the local filesystem under a configured base directory and extracts archive contents
- 🔄 **Content Replacement**: Automatically removes existing content at target path before extraction to ensure clean deployment
- 🔐 **Security Validation**: Validates file types and rejects archives with unsafe paths (absolute paths, `..` traversal)
- 🏥 **Built-in health checks**: `/health` endpoint returns service status and version
- 📚 **Auto-generated docs**: OpenAPI/Swagger documentation at `/docs`
- 🔒 **Security-focused**: Runs as non-root user with minimal attack surface
- 🐳 **Multi-architecture**: Supports both AMD64 and ARM64 architectures

## Installation

### Using Docker Hub (Recommended)

```bash
# Pull the latest version
docker pull docker.cloudsmith.io/hermesbaby/hermes/hermes:latest

# Or pull a specific version
docker pull docker.cloudsmith.io/hermesbaby/hermes/hermes:v1976.06.04.1
```

### Building from Source

```bash
# Clone the repository
git clone https://github.com/hermesbaby/hermes.git
cd hermes

# Build the Docker image
docker build -t hermes:local .
```

## Usage

### Quick Start

```bash
# Run the container with required environment variable
docker run -e HERMES_BASE_DIRECTORY="/app/data" -p 8000:8000 docker.cloudsmith.io/hermesbaby/hermes/hermes:latest

# Test the service
curl http://localhost:8000/health

# Test with a tar.gz file upload (no token required in this example)
echo "Hello World" > test.txt
tar -czf test.tar.gz test.txt
curl -X PUT -F "file=@test.tar.gz" http://localhost:8000/test/upload

# Test with a ZIP file upload
echo "Hello from ZIP" > test.txt
zip test.zip test.txt
curl -X PUT -F "file=@test.zip" http://localhost:8000/test/upload-zip

# Test with a 7z file upload (requires 7z command-line tool)
echo "Hello from 7z" > test.txt
7z a test.7z test.txt
curl -X PUT -F "file=@test.7z" http://localhost:8000/test/upload-7z

# If token is configured, use authentication:
# curl -X PUT -F "file=@test.tar.gz" -H "Authorization: Bearer your-token" http://localhost:8000/test/upload
```

⚠️ **Important**: The `HERMES_BASE_DIRECTORY` environment variable is **required**. The service will not start without it.

### Running with Docker Compose

Create a `docker-compose.yml` file:

```yaml
version: '3.8'
services:
  hermes:
    image: docker.cloudsmith.io/hermesbaby/hermes/hermes:latest
    environment:
      - HERMES_BASE_DIRECTORY=/app/data
      - HERMES_API_TOKEN=your-secure-token-here  # Optional: Enable API token security
    ports:
      - "8000:8000"
    volumes:
      - hermes_data:/app/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s

volumes:
  hermes_data:
```

Then run:

```bash
docker-compose up -d
```

### Systemd Service Installation (Production)

For production deployments, install Hermes as a systemd service:

```bash
# Download the installation script
curl -O https://raw.githubusercontent.com/hermesbaby/hermes/main/install-hermes-service.sh
chmod +x install-hermes-service.sh

# Run as root to install with default settings
sudo ./install-hermes-service.sh

# Or customize the installation with environment variables
sudo HERMES_DATA_DIR=/custom/path ./install-hermes-service.sh
sudo HERMES_API_TOKEN=mytoken HERMES_DATA_DIR=/opt/hermes ./install-hermes-service.sh
```

**Installation Options:**
- **Default installation**: Uses `/var/www/html` as data directory and generates a random API token
- **Custom data directory**: Set `HERMES_DATA_DIR` environment variable before running
- **Custom API token**: Set `HERMES_API_TOKEN` environment variable before running
- **Both custom**: Set both environment variables for full customization

The installation script automatically detects your container runtime (Docker or Podman) and configures the service accordingly.

This will:
- Create a dedicated `hermes` system user
- Generate a secure API token (or use provided one)
- Configure data directory (default: `/var/www/html`, or custom path)
- Set up systemd service with auto-start
- Configure proper file permissions and ownership
- Detect and configure for Docker or Podman
- Start and test the service

**Container Runtime Support:**
- ✅ **Docker**: Full support with `docker.service` dependencies
- ✅ **Podman**: Full support with `network-online.target` dependencies

**Service Management:**
```bash
sudo systemctl start hermes     # Start service
sudo systemctl stop hermes      # Stop service
sudo systemctl restart hermes   # Restart service
sudo systemctl status hermes    # Check status
sudo journalctl -u hermes -f    # View logs
```

**Post-Installation Configuration:**
```bash
# View current configuration (API token and data directory)
sudo cat /etc/hermes/hermes.env

# Update API token or data directory after installation
sudo nano /etc/hermes/hermes.env
sudo systemctl restart hermes

# If changing data directory, also update ownership
sudo chown -R $(id -u hermes):$(id -g hermes) /new/data/path
sudo chmod -R 755 /new/data/path
```

### Environment Configuration

The service runs on port 8000 by default and **requires** the `HERMES_BASE_DIRECTORY` environment variable to be set.

#### Required Environment Variables

- **`HERMES_BASE_DIRECTORY`**: **Required**. The base directory where extracted files will be stored. The service will not start without this variable.

#### Optional Environment Variables

- **`HERMES_API_TOKEN`**: **Optional**. API token for securing PUT requests. When set, all PUT requests must include a valid token via `Authorization: Bearer <token>` or `X-API-Token: <token>` header. Health endpoint remains unprotected.

#### Systemd Service Environment Variables

When using the systemd service installation script, these environment variables can be set before installation:

- **`HERMES_DATA_DIR`**: **Optional**. Custom data directory for the systemd service (defaults to `/var/www/html`). Set this before running the installation script to customize the data directory location.
- **`HERMES_API_TOKEN`**: **Optional**. Custom API token for the systemd service. If not provided, a secure random token is generated automatically.

**Example:**
```bash
# Install with custom data directory
sudo HERMES_DATA_DIR=/opt/hermes-data ./install-hermes-service.sh

# Install with both custom token and data directory
sudo HERMES_API_TOKEN=my-secure-token HERMES_DATA_DIR=/opt/hermes ./install-hermes-service.sh
```

#### Usage Examples

```bash
# Run with required base directory configuration
docker run -e HERMES_BASE_DIRECTORY="/app/data" -p 8000:8000 docker.cloudsmith.io/hermesbaby/hermes/hermes:latest

# Run with API token security enabled
docker run \
  -e HERMES_BASE_DIRECTORY="/app/data" \
  -e HERMES_API_TOKEN="your-secret-token-here" \
  -p 8000:8000 \
  docker.cloudsmith.io/hermesbaby/hermes/hermes:latest

# Run on a different port with custom base directory
docker run -e HERMES_BASE_DIRECTORY="/var/hermes" -p 3000:8000 docker.cloudsmith.io/hermesbaby/hermes/hermes:latest

# Run with additional environment variables
docker run \
  -e HERMES_BASE_DIRECTORY="/data/extractions" \
  -e HERMES_API_TOKEN="secure-token-123" \
  -e PYTHONUNBUFFERED=1 \
  -p 8000:8000 \
  docker.cloudsmith.io/hermesbaby/hermes/hermes:latest
```

## API Endpoints

### Health Check

```http
GET /health
```

**Response:**

```json
{
  "status": "ok",
  "service": "hermes",
  "version": "1976.06.04.1"
}
```

### Universal PUT Archive Extraction

```http
PUT /{any_path}
Content-Type: multipart/form-data
Authorization: Bearer <token>  # Required if HERMES_API_TOKEN is set
# OR
X-API-Token: <token>           # Alternative token header
```

**Supported Archive Formats:**
- **tar.gz** / **.tgz**: Standard tar.gz compressed archives
- **ZIP** / **.zip**: Standard ZIP compressed archives  
- **7z** / **.7z**: 7-Zip compressed archives

#### Authentication

When `HERMES_API_TOKEN` environment variable is configured, all PUT requests require authentication using one of:

1. **Bearer Token** (recommended): `Authorization: Bearer <your-token>`
2. **Custom Header**: `X-API-Token: <your-token>`

If both headers are provided, the Bearer token takes precedence. The health endpoint (`/health`) remains unprotected.

**Examples:**

```bash
# tar.gz upload - creates directory and extracts contents (no token required)
curl -X PUT -F "file=@my-app.tar.gz" http://localhost:8000/applications/myapp

# ZIP upload with Bearer token authentication
curl -X PUT -F "file=@my-app.zip" \
  -H "Authorization: Bearer your-secret-token" \
  http://localhost:8000/applications/myapp-zip

# 7z upload with X-API-Token header authentication
curl -X PUT -F "file=@my-app.7z" \
  -H "X-API-Token: your-secret-token" \
  http://localhost:8000/applications/myapp-7z
# Returns: {
#   "endpoint": "/applications/myapp-7z", 
#   "method": "PUT", 
#   "created_path": "/app/data/applications/myapp-7z",
#   "status": "extracted",
#   "archive_type": "7z",
#   "filename": "my-app.7z",
#   "file_size": 1234,
#   "extracted_items": ["src", "config", "README.md"],
#   "total_extracted_paths": 15
# }

# Nested path with complex archive structure (ZIP format)
curl -X PUT -F "file=@project.zip" \
  -H "Authorization: Bearer your-secret-token" \
  http://localhost:8000/deployments/v1/webapp
# Returns: {
#   "endpoint": "/deployments/v1/webapp", 
#   "method": "PUT", 
#   "created_path": "/app/data/deployments/v1/webapp",
#   "status": "extracted",
#   "archive_type": "zip",
#   "filename": "project.zip",
#   "file_size": 5678,
#   "extracted_items": ["app", "static", "templates", "requirements.txt"],
#   "total_extracted_paths": 25
# }

# Root path extraction (7z format with X-API-Token header)
curl -X PUT -F "file=@archive.7z" \
  -H "X-API-Token: your-secret-token" \
  http://localhost:8000/
# Returns: {
#   "endpoint": "/", 
#   "method": "PUT", 
#   "created_path": "/app/data",
#   "status": "extracted",
#   "archive_type": "7z",
#   "filename": "archive.7z",
#   "file_size": 9012,
#   "extracted_items": ["data", "logs", "config.json"],
#   "total_extracted_paths": 30
# }

# All supported formats (.tar.gz, .tgz, .zip, .7z)
curl -X PUT -F "file=@backup.tgz" http://localhost:8000/backups/daily-tgz
curl -X PUT -F "file=@backup.zip" http://localhost:8000/backups/daily-zip
curl -X PUT -F "file=@backup.7z" http://localhost:8000/backups/daily-7z
```

**Extraction Details:**

- **Base Directory**: All directories are created under the configured `HERMES_BASE_DIRECTORY` environment variable
- **Content Replacement**: Existing content at the target path is completely removed before extraction
- **Archive Structure Preserved**: Internal directory structure of all archive formats is maintained after extraction
- **File Type Validation**: Supports `.tar.gz`, `.tgz`, `.zip`, and `.7z` archive formats
- **Security Filtering**: Archives with absolute paths (`/etc/passwd`) or directory traversal (`../`) are rejected for all formats
- **Automatic Cleanup**: Temporary files are automatically cleaned up after extraction
- **Response Enhancement**: Returns archive type, total extracted paths count, and other metadata

### API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## Use Cases

### Application Deployment
Perfect for deploying packaged applications with their complete directory structure using any supported archive format:

```bash
# Deploy a web application with all its assets (tar.gz format, secured with token)
curl -X PUT -F "file=@webapp-v2.1.tar.gz" \
  -H "Authorization: Bearer $HERMES_API_TOKEN" \
  http://localhost:8000/deployments/webapp/v2.1

# Deploy using ZIP format
curl -X PUT -F "file=@webapp-v2.1.zip" \
  -H "Authorization: Bearer $HERMES_API_TOKEN" \
  http://localhost:8000/deployments/webapp/v2.1-zip

# Deploy using 7z format for better compression
curl -X PUT -F "file=@webapp-v2.1.7z" \
  -H "Authorization: Bearer $HERMES_API_TOKEN" \
  http://localhost:8000/deployments/webapp/v2.1-7z

# All formats extract to the same structure:
# $HERMES_BASE_DIRECTORY/deployments/webapp/v2.1/
#   ├── static/css/
#   ├── static/js/
#   ├── templates/
#   ├── app.py
#   └── requirements.txt
```

### Configuration Management
Deploy configuration bundles to specific environments using any archive format:

```bash
# Deploy environment-specific configurations (various formats with API token)
curl -X PUT -F "file=@prod-config.tar.gz" \
  -H "X-API-Token: $HERMES_API_TOKEN" \
  http://localhost:8000/config/production

curl -X PUT -F "file=@staging-config.zip" \
  -H "X-API-Token: $HERMES_API_TOKEN" \
  http://localhost:8000/config/staging

curl -X PUT -F "file=@dev-config.7z" \
  -H "X-API-Token: $HERMES_API_TOKEN" \
  http://localhost:8000/config/development
# Each creates complete configuration directory structure
```

### Content Publishing
Publish website content or documentation with full directory structure using any archive format:

```bash
# Publish documentation site (ZIP format for easy creation from Windows)
curl -X PUT -F "file=@docs-site.zip" http://localhost:8000/sites/documentation

# Publish using 7z for maximum compression
curl -X PUT -F "file=@large-site.7z" http://localhost:8000/sites/large-documentation

# Traditional tar.gz format
curl -X PUT -F "file=@docs-site.tar.gz" http://localhost:8000/sites/traditional-docs

# All formats extract to: $HERMES_BASE_DIRECTORY/sites/documentation/
#   ├── index.html
#   ├── api/
#   ├── guides/
#   └── assets/
```

### Development Workflows
Deploy development builds with their complete project structure using any archive format:

```bash
# Deploy a development build for testing (various formats)
curl -X PUT -F "file=@feature-branch.tar.gz" http://localhost:8000/dev/feature-xyz-tarball
curl -X PUT -F "file=@feature-branch.zip" http://localhost:8000/dev/feature-xyz-zip  
curl -X PUT -F "file=@feature-branch.7z" http://localhost:8000/dev/feature-xyz-7z
# All create complete development environment structure
```

### Backup Restoration
Restore archived content to specific locations using any supported archive format:

```bash
# Restore from backup archives (format flexibility)
curl -X PUT -F "file=@backup-2024-10-28.tar.gz" http://localhost:8000/restore/2024-10-28-tarball
curl -X PUT -F "file=@backup-2024-10-28.zip" http://localhost:8000/restore/2024-10-28-zip
curl -X PUT -F "file=@backup-2024-10-28.7z" http://localhost:8000/restore/2024-10-28-7z
# All restore complete backed-up directory structures
```

## Development

### Running Locally with Poetry

```bash
# Install dependencies
poetry install

# Set required environment variable and run the development server
export HERMES_BASE_DIRECTORY="/tmp/hermes_dev"
# Optional: Enable API token authentication
export HERMES_API_TOKEN="dev-token-12345"
poetry run uvicorn hermesbaby.hermes.main:app --reload --host 0.0.0.0 --port 8000

# Run tests (environment variable is mocked in tests)
poetry run pytest

# Run with coverage
poetry run pytest --cov=hermesbaby
```

### Testing the Docker Image

```bash
# Build and test locally
docker build -t hermes:test .
docker run -e HERMES_BASE_DIRECTORY="/app/test" -p 8000:8000 hermes:test

# Run tests against the running container
curl http://localhost:8000/health
# Note: PUT requests require archive file uploads, plain PUT requests will return 422

# Test with different archive formats (include token if configured)
echo "test content" > test.txt

# Test tar.gz
tar -czf test.tar.gz test.txt
curl -X PUT -F "file=@test.tar.gz" \
  -H "Authorization: Bearer your-token-here" \
  http://localhost:8000/test/endpoint-tarball

# Test ZIP
zip test.zip test.txt
curl -X PUT -F "file=@test.zip" \
  -H "Authorization: Bearer your-token-here" \
  http://localhost:8000/test/endpoint-zip

# Test 7z (if 7z command is available)
7z a test.7z test.txt
curl -X PUT -F "file=@test.7z" \
  -H "Authorization: Bearer your-token-here" \
  http://localhost:8000/test/endpoint-7z

# Verify directories were created (inside container)
docker exec <container_id> ls -la /app/test/test/endpoint-*/
```

## Configuration

### Extraction Configuration

- **Base Directory**: Configured via the required `HERMES_BASE_DIRECTORY` environment variable
- **Directory Permissions**: Created with default permissions (755)
- **Path Handling**: Safely handles nested paths, special characters, and edge cases
- **Content Replacement**: Existing content is completely removed before new extraction
- **Archive Validation**: tar.gz, .tgz, ZIP, and 7z files accepted, with security path validation for all formats
- **Structure Preservation**: Complete internal directory structure of all archive formats is maintained

### Systemd Service Configuration Updates

After installing Hermes as a systemd service, you can update the configuration by modifying the environment file:

**Configuration File Location:** `/etc/hermes/hermes.env`

**Available Settings:**
- `HERMES_API_TOKEN`: API authentication token
- `HERMES_DATA_DIR`: Data directory path where archives are extracted

**Update Process:**
1. Edit the configuration file: `sudo nano /etc/hermes/hermes.env`
2. Restart the service: `sudo systemctl restart hermes`
3. If changing data directory, ensure proper ownership:
   ```bash
   sudo chown -R $(id -u hermes):$(id -g hermes) /new/data/path
   sudo chmod -R 755 /new/data/path
   ```

**Example Configuration Update:**
```bash
# View current configuration
sudo cat /etc/hermes/hermes.env

# Example output:
# HERMES_API_TOKEN=abc123def456...
# HERMES_DATA_DIR=/var/www/html

# Edit configuration
sudo nano /etc/hermes/hermes.env

# Change to:
# HERMES_API_TOKEN=my-new-secure-token
# HERMES_DATA_DIR=/opt/hermes-storage

# Apply changes
sudo chown -R $(id -u hermes):$(id -g hermes) /opt/hermes-storage
sudo chmod -R 755 /opt/hermes-storage
sudo systemctl restart hermes
```

### Container Image Updates

After installing Hermes as a systemd service, you can update to the latest container image version:

**Quick Update (Recommended):**
```bash
# Pull the latest container image
sudo podman pull docker.cloudsmith.io/hermesbaby/hermes/hermes:latest
# OR if using Docker:
sudo docker pull docker.cloudsmith.io/hermesbaby/hermes/hermes:latest

# Restart the service to use the new image
sudo systemctl restart hermes

# Verify the update
sudo systemctl status hermes
curl http://localhost:8000/health
```

**Manual Update Process:**
```bash
# Stop the service
sudo systemctl stop hermes

# Pull the latest image
sudo podman pull docker.cloudsmith.io/hermesbaby/hermes/hermes:latest

# Start the service with the new image
sudo systemctl start hermes

# Check service status and version
sudo systemctl status hermes
curl -s http://localhost:8000/health | grep version
```

**Complete Update with Verification:**
```bash
echo "Updating Hermes container..."
sudo podman pull docker.cloudsmith.io/hermesbaby/hermes/hermes:latest
sudo systemctl restart hermes

echo "Verifying update..."
sudo systemctl status hermes --no-pager -l
curl http://localhost:8000/health

echo "Cleaning up old images (optional)..."
sudo podman image prune -f

echo "Update completed successfully!"
```

**Notes:**
- Your API token and configuration remain unchanged
- The service automatically uses the `:latest` tag, so pulling updates the image
- Both Docker and Podman are supported - use the appropriate command for your system
- Old unused images can be removed with `sudo podman image prune` or `sudo docker image prune`

### Environment Variables

#### Required Variables

- **`HERMES_BASE_DIRECTORY`**: **Required**. Base directory for all file extractions. The service will fail to start without this variable.

#### Optional Variables

- `PYTHONUNBUFFERED=1`: Ensures Python output is not buffered
- `PYTHONDONTWRITEBYTECODE=1`: Prevents Python from writing .pyc files

### Health Check Configuration

The Docker image includes built-in health checks:

- **Interval**: 30 seconds
- **Timeout**: 30 seconds  
- **Start Period**: 5 seconds
- **Retries**: 3

## Security

### API Token Authentication

Hermes supports optional API token authentication for PUT requests:

- **Configure via environment**: Set `HERMES_API_TOKEN` to enable authentication
- **Two authentication methods**: Bearer token (`Authorization: Bearer <token>`) or custom header (`X-API-Token: <token>`)
- **Health endpoint exemption**: `/health` endpoint remains unprotected for monitoring
- **Bearer precedence**: When both headers are provided, Bearer token takes precedence

```bash
# Generate a secure token
export HERMES_API_TOKEN=$(openssl rand -hex 32)

# Use in requests
curl -X PUT -F "file=@app.tar.gz" \
  -H "Authorization: Bearer $HERMES_API_TOKEN" \
  http://localhost:8000/deployments/app
```

### Container Security

- Runs as non-root user (`hermes`)
- Minimal base image (Python 3.12 slim)
- No unnecessary dependencies
- Regular security scanning with Trivy
- Path traversal protection for uploaded archives

## License

This project is dual-licensed:

- **MIT License** for software usage
- **CC BY-SA-4.0** for methodological usage

See `LICENSE.md` for full details.

## Troubleshooting

### Common Issues

**Permission Denied Error**: If you encounter permission errors like `{"detail":"Failed to extract archive: [Errno 13] Permission denied: '/var/www'"}`, see the [Troubleshooting Guide](TROUBLESHOOTING.md) for detailed solutions.

**Quick Fix for Permission Issues**:
```bash
# Use volume mounting (recommended)
docker run -d \
  -v /var/www/html/test:/app/data \
  -e HERMES_BASE_DIRECTORY="/app/data" \
  -p 8000:8000 \
  docker.cloudsmith.io/hermesbaby/hermes/hermes:latest
```

**Podman/Docker Service Issues**: If you encounter `Unit docker.service not found` errors during systemd service installation, this means you're using Podman instead of Docker. The installation script automatically detects this, but if you're having issues:

1. **For new installations**: Re-run the installation script - it will detect Podman automatically
2. **For existing installations**: The service file needs to be updated to use Podman instead of Docker dependencies

For more troubleshooting information, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

## Support & Contributing

- **Issues**: Report bugs and feature requests on GitHub
- **Contributing**: Pull requests welcome
- **Documentation**: Full API docs available at `/docs` when running

---

**Version**: 1976.06.04.1  
**Maintainer**: basejumpa <basejumpa@encouraged-coders.de>
