# HermesBaby-Hermes

**Hermes** is a lightweight FastAPI service that acts as a universal PUT endpoint directory creation service. It accepts PUT requests to any endpoint path and creates the corresponding directory structure on the local filesystem, making it useful for dynamic file system provisioning, testing, and development workflows.

## What This Docker Image Does

The Hermes Docker image provides:

- **Universal PUT Directory Creation Service**: Accepts PUT requests to any endpoint path and creates the corresponding directory structure on the filesystem
- **Health Check Endpoint**: Provides a `/health` endpoint for monitoring and container orchestration
- **FastAPI-based**: Built on FastAPI with automatic API documentation
- **Production Ready**: Includes proper security configuration, non-root user, and health checks

### Key Features

- 🌐 **Catch-all PUT endpoints**: Any PUT request to `/path/to/anything` creates the directory structure and returns creation details
- 📁 **Filesystem Integration**: Creates actual directories on the local filesystem under a configured base directory
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
# Run the container
docker run -p 8000:8000 docker.cloudsmith.io/hermesbaby/hermes/hermes:latest

# Test the service
curl http://localhost:8000/health
```

### Running with Docker Compose

Create a `docker-compose.yml` file:

```yaml
version: '3.8'
services:
  hermes:
    image: docker.cloudsmith.io/hermesbaby/hermes/hermes:latest
    ports:
      - "8000:8000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
```

Then run:

```bash
docker-compose up -d
```

### Environment Configuration

The service runs on port 8000 by default. You can customize the deployment:

```bash
# Run on a different port
docker run -p 3000:8000 docker.cloudsmith.io/hermesbaby/hermes/hermes:latest

# Run with custom environment
docker run -e PYTHONUNBUFFERED=1 -p 8000:8000 docker.cloudsmith.io/hermesbaby/hermes/hermes:latest
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

### Universal PUT Directory Creation

```http
PUT /{any_path}
```

**Examples:**

```bash
# Simple path - creates directory structure
curl -X PUT http://localhost:8000/users
# Returns: {
#   "endpoint": "/users", 
#   "method": "PUT", 
#   "created_path": "/tmp/hermes_files/users",
#   "status": "created"
# }

# Nested path - creates full directory tree
curl -X PUT http://localhost:8000/api/v1/users/123
# Returns: {
#   "endpoint": "/api/v1/users/123", 
#   "method": "PUT", 
#   "created_path": "/tmp/hermes_files/api/v1/users/123",
#   "status": "created"
# }

# Root path
curl -X PUT http://localhost:8000/
# Returns: {
#   "endpoint": "/", 
#   "method": "PUT", 
#   "created_path": "/tmp/hermes_files",
#   "status": "created"
# }

# With JSON body - body is ignored, directory is still created
curl -X PUT -H "Content-Type: application/json" \
     -d '{"data": "test"}' \
     http://localhost:8000/webhook/callback
# Returns: {
#   "endpoint": "/webhook/callback", 
#   "method": "PUT", 
#   "created_path": "/tmp/hermes_files/webhook/callback",
#   "status": "created"
# }
```

**Directory Creation Details:**

- **Base Directory**: All directories are created under `/tmp/hermes_files/` (hardcoded)
- **Automatic Nesting**: Intermediate directories are created automatically (like `mkdir -p`)
- **Idempotent**: Multiple requests to the same path won't cause errors
- **Path Safety**: Input paths are sanitized and safely joined with the base directory

### API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## Use Cases

### Dynamic Directory Provisioning
Perfect for applications that need to create directory structures on-demand:

```bash
# Your application needs to create a directory structure
curl -X PUT http://localhost:8000/projects/2024/client-abc/assets/images
# Creates: /tmp/hermes_files/projects/2024/client-abc/assets/images/
```

### File System Prototyping
Use during development to quickly create directory structures for testing:

```bash
# Set up a complex directory structure for testing
curl -X PUT http://localhost:8000/app/data/users/profiles
curl -X PUT http://localhost:8000/app/data/users/settings  
curl -X PUT http://localhost:8000/app/logs/2024/10
# Creates complete directory tree structure
```

### Webhook-Driven Directory Creation
Create directories based on webhook events:

```bash
# Webhook creates directory based on event data
curl -X PUT http://localhost:8000/webhooks/user-123/profile-updated \
     -H "Content-Type: application/json" \
     -d '{"user_id": "123", "event": "profile_updated"}'
# Creates: /tmp/hermes_files/webhooks/user-123/profile-updated/
```

### Development & Testing
Test directory creation logic and verify filesystem operations:

```bash
# Test your application's directory creation needs
curl -X PUT http://localhost:8000/api/v2/organizations/456/projects/789/files
```

## Development

### Running Locally with Poetry

```bash
# Install dependencies
poetry install

# Run the development server
poetry run uvicorn hermesbaby.hermes.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=hermesbaby
```

### Testing the Docker Image

```bash
# Build and test locally
docker build -t hermes:test .
docker run -p 8000:8000 hermes:test

# Run tests against the running container
curl http://localhost:8000/health
curl -X PUT http://localhost:8000/test/endpoint

# Verify directory was created
ls -la /tmp/hermes_files/test/
```

## Configuration

### Directory Configuration

- **Base Directory**: `/tmp/hermes_files/` (hardcoded in the current version)
- **Directory Permissions**: Created with default permissions (755)
- **Path Handling**: Safely handles nested paths, special characters, and edge cases
- **Idempotent Operation**: Multiple requests to the same path are safe and won't cause errors

### Environment Variables

- `PYTHONUNBUFFERED=1`: Ensures Python output is not buffered
- `PYTHONDONTWRITEBYTECODE=1`: Prevents Python from writing .pyc files

### Health Check Configuration

The Docker image includes built-in health checks:

- **Interval**: 30 seconds
- **Timeout**: 30 seconds  
- **Start Period**: 5 seconds
- **Retries**: 3

## Security

- Runs as non-root user (`hermes`)
- Minimal base image (Python 3.12 slim)
- No unnecessary dependencies
- Regular security scanning with Trivy

## License

This project is dual-licensed:

- **MIT License** for software usage
- **CC BY-SA-4.0** for methodological usage

See `LICENSE.md` for full details.

## Migration from Echo Service

**⚠️ Breaking Change**: This version changes the behavior from echoing paths to actually creating directories on the filesystem.

**Previous behavior** (echo service):
```json
{"endpoint": "/users", "method": "PUT"}
```

**New behavior** (directory creation):
```json
{
  "endpoint": "/users",
  "method": "PUT", 
  "created_path": "/tmp/hermes_files/users",
  "status": "created"
}
```

If you need the old echo behavior, please use an earlier version of the service.

## Support & Contributing

- **Issues**: Report bugs and feature requests on GitHub
- **Contributing**: Pull requests welcome
- **Documentation**: Full API docs available at `/docs` when running

---

**Version**: 1976.06.04.1  
**Maintainer**: basejumpa <basejumpa@encouraged-coders.de>
