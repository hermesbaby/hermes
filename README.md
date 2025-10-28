# HermesBaby-Hermes

**Hermes** is a lightweight FastAPI service that acts as a universal PUT endpoint for tar.gz file extraction. It accepts PUT requests with tar.gz files to any endpoint path, creates the corresponding directory structure on the local filesystem, and extracts the archive contents with their internal directory structure, making it useful for dynamic file system provisioning, deployment, and development workflows.

## What This Docker Image Does

The Hermes Docker image provides:

- **Universal PUT Tar.gz Extraction Service**: Accepts PUT requests with tar.gz files to any endpoint path, creates directory structure, and extracts archive contents
- **Health Check Endpoint**: Provides a `/health` endpoint for monitoring and container orchestration
- **FastAPI-based**: Built on FastAPI with automatic API documentation
- **Production Ready**: Includes proper security configuration, non-root user, and health checks

### Key Features

- 🌐 **Catch-all PUT endpoints**: Any PUT request with tar.gz file to `/path/to/anything` creates directory structure and extracts archive contents
- 📁 **Filesystem Integration**: Creates actual directories on the local filesystem under a configured base directory and extracts tar.gz contents
- 🔄 **Content Replacement**: Automatically removes existing content at target path before extraction to ensure clean deployment
- 🔐 **Security Validation**: Validates file types (tar.gz/tgz only) and rejects archives with unsafe paths (absolute paths, `..` traversal)
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

### Environment Configuration

The service runs on port 8000 by default and **requires** the `HERMES_BASE_DIRECTORY` environment variable to be set.

#### Required Environment Variables

- **`HERMES_BASE_DIRECTORY`**: **Required**. The base directory where extracted files will be stored. The service will not start without this variable.

#### Optional Environment Variables

- **`HERMES_API_TOKEN`**: **Optional**. API token for securing PUT requests. When set, all PUT requests must include a valid token via `Authorization: Bearer <token>` or `X-API-Token: <token>` header. Health endpoint remains unprotected.

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

### Universal PUT Tar.gz Extraction

```http
PUT /{any_path}
Content-Type: multipart/form-data
Authorization: Bearer <token>  # Required if HERMES_API_TOKEN is set
# OR
X-API-Token: <token>           # Alternative token header
```

#### Authentication

When `HERMES_API_TOKEN` environment variable is configured, all PUT requests require authentication using one of:

1. **Bearer Token** (recommended): `Authorization: Bearer <your-token>`
2. **Custom Header**: `X-API-Token: <your-token>`

If both headers are provided, the Bearer token takes precedence. The health endpoint (`/health`) remains unprotected.

**Examples:**

```bash
# Simple tar.gz upload - creates directory and extracts contents (no token required)
curl -X PUT -F "file=@my-app.tar.gz" http://localhost:8000/applications/myapp

# With Bearer token authentication
curl -X PUT -F "file=@my-app.tar.gz" \
  -H "Authorization: Bearer your-secret-token" \
  http://localhost:8000/applications/myapp

# With X-API-Token header authentication
curl -X PUT -F "file=@my-app.tar.gz" \
  -H "X-API-Token: your-secret-token" \
  http://localhost:8000/applications/myapp
# Returns: {
#   "endpoint": "/applications/myapp", 
#   "method": "PUT", 
#   "created_path": "/app/data/applications/myapp",
#   "status": "extracted",
#   "filename": "my-app.tar.gz",
#   "file_size": 1234,
#   "extracted_items": ["src", "config", "README.md"]
# }

# Nested path with complex archive structure (with token)
curl -X PUT -F "file=@project.tar.gz" \
  -H "Authorization: Bearer your-secret-token" \
  http://localhost:8000/deployments/v1/webapp
# Returns: {
#   "endpoint": "/deployments/v1/webapp", 
#   "method": "PUT", 
#   "created_path": "/app/data/deployments/v1/webapp",
#   "status": "extracted",
#   "filename": "project.tar.gz",
#   "file_size": 5678,
#   "extracted_items": ["app", "static", "templates", "requirements.txt"]
# }

# Root path extraction (with X-API-Token header)
curl -X PUT -F "file=@archive.tar.gz" \
  -H "X-API-Token: your-secret-token" \
  http://localhost:8000/
# Returns: {
#   "endpoint": "/", 
#   "method": "PUT", 
#   "created_path": "/app/data",
#   "status": "extracted",
#   "filename": "archive.tar.gz",
#   "file_size": 9012,
#   "extracted_items": ["data", "logs", "config.json"]
# }

# .tgz files are also supported (no token example)
curl -X PUT -F "file=@backup.tgz" http://localhost:8000/backups/daily
```

**Extraction Details:**

- **Base Directory**: All directories are created under the configured `HERMES_BASE_DIRECTORY` environment variable
- **Content Replacement**: Existing content at the target path is completely removed before extraction
- **Archive Structure Preserved**: Internal directory structure of the tar.gz is maintained after extraction
- **File Type Validation**: Only `.tar.gz` and `.tgz` files are accepted
- **Security Filtering**: Archives with absolute paths (`/etc/passwd`) or directory traversal (`../`) are rejected
- **Automatic Cleanup**: Temporary files are automatically cleaned up after extraction

### API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## Use Cases

### Application Deployment
Perfect for deploying packaged applications with their complete directory structure:

```bash
# Deploy a web application with all its assets (secured with token)
curl -X PUT -F "file=@webapp-v2.1.tar.gz" \
  -H "Authorization: Bearer $HERMES_API_TOKEN" \
  http://localhost:8000/deployments/webapp/v2.1
# Extracts: $HERMES_BASE_DIRECTORY/deployments/webapp/v2.1/
#   ├── static/css/
#   ├── static/js/
#   ├── templates/
#   ├── app.py
#   └── requirements.txt
```

### Configuration Management
Deploy configuration bundles to specific environments:

```bash
# Deploy environment-specific configurations (with API token)
curl -X PUT -F "file=@prod-config.tar.gz" \
  -H "X-API-Token: $HERMES_API_TOKEN" \
  http://localhost:8000/config/production
curl -X PUT -F "file=@staging-config.tar.gz" \
  -H "X-API-Token: $HERMES_API_TOKEN" \
  http://localhost:8000/config/staging
# Each creates complete configuration directory structure
```

### Content Publishing
Publish website content or documentation with full directory structure:

```bash
# Publish documentation site
curl -X PUT -F "file=@docs-site.tar.gz" http://localhost:8000/sites/documentation
# Extracts: $HERMES_BASE_DIRECTORY/sites/documentation/
#   ├── index.html
#   ├── api/
#   ├── guides/
#   └── assets/
```

### Development Workflows
Deploy development builds with their complete project structure:

```bash
# Deploy a development build for testing
curl -X PUT -F "file=@feature-branch.tar.gz" http://localhost:8000/dev/feature-xyz
# Creates complete development environment structure
```

### Backup Restoration
Restore archived content to specific locations:

```bash
# Restore from backup archive
curl -X PUT -F "file=@backup-2024-10-28.tar.gz" http://localhost:8000/restore/2024-10-28
# Restores complete backed-up directory structure
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
# Note: PUT requests require tar.gz file uploads, plain PUT requests will return 422

# Test with actual tar.gz file (include token if configured)
echo "test content" > test.txt
tar -czf test.tar.gz test.txt
curl -X PUT -F "file=@test.tar.gz" \
  -H "Authorization: Bearer your-token-here" \
  http://localhost:8000/test/endpoint

# Verify directory was created (inside container)
docker exec <container_id> ls -la /app/test/test/endpoint/
```

## Configuration

### Extraction Configuration

- **Base Directory**: Configured via the required `HERMES_BASE_DIRECTORY` environment variable
- **Directory Permissions**: Created with default permissions (755)
- **Path Handling**: Safely handles nested paths, special characters, and edge cases
- **Content Replacement**: Existing content is completely removed before new extraction
- **Archive Validation**: Only tar.gz and .tgz files accepted, with security path validation
- **Structure Preservation**: Complete internal directory structure of archives is maintained

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

## Migration from Directory Creation Service

**⚠️ Breaking Change**: This version changes the behavior from simple directory creation to tar.gz file extraction.

**Previous behavior** (directory creation):
```json
{
  "endpoint": "/users",
  "method": "PUT", 
  "created_path": "/tmp/hermes_files/users",
  "status": "created"
}
```

**New behavior** (tar.gz extraction):
```json
{
  "endpoint": "/users",
  "method": "PUT", 
  "created_path": "$HERMES_BASE_DIRECTORY/users",
  "status": "extracted",
  "filename": "archive.tar.gz",
  "file_size": 1234,
  "extracted_items": ["file1.txt", "subdir"]
}
```

**Key Changes:**
- PUT requests now require a tar.gz file upload via `multipart/form-data`
- The service extracts the archive contents to the target path
- Existing content at the target path is removed before extraction
- Response includes extraction details like filename, file size, and extracted items

If you need the old directory creation behavior, please use an earlier version of the service.

## Support & Contributing

- **Issues**: Report bugs and feature requests on GitHub
- **Contributing**: Pull requests welcome
- **Documentation**: Full API docs available at `/docs` when running

---

**Version**: 1976.06.04.1  
**Maintainer**: basejumpa <basejumpa@encouraged-coders.de>
