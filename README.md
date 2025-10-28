# HermesBaby-Hermes

**Hermes** is a lightweight FastAPI service that acts as a universal PUT endpoint echo service. It's designed to accept PUT requests to any endpoint and echo back the requested path, making it useful for testing, debugging, and webhook development.

## What This Docker Image Does

The Hermes Docker image provides:

- **Universal PUT Echo Service**: Accepts PUT requests to any endpoint path and returns the endpoint path along with the HTTP method
- **Health Check Endpoint**: Provides a `/health` endpoint for monitoring and container orchestration
- **FastAPI-based**: Built on FastAPI with automatic API documentation
- **Production Ready**: Includes proper security configuration, non-root user, and health checks

### Key Features

- 🌐 **Catch-all PUT endpoints**: Any PUT request to `/path/to/anything` returns `{"endpoint": "/path/to/anything", "method": "PUT"}`
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

### Universal PUT Echo

```http
PUT /{any_path}
```

**Examples:**

```bash
# Simple path
curl -X PUT http://localhost:8000/users
# Returns: {"endpoint": "/users", "method": "PUT"}

# Nested path
curl -X PUT http://localhost:8000/api/v1/users/123
# Returns: {"endpoint": "/api/v1/users/123", "method": "PUT"}

# Root path
curl -X PUT http://localhost:8000/
# Returns: {"endpoint": "/", "method": "PUT"}

# With JSON body
curl -X PUT -H "Content-Type: application/json" \
     -d '{"data": "test"}' \
     http://localhost:8000/webhook/callback
# Returns: {"endpoint": "/webhook/callback", "method": "PUT"}
```

### API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## Use Cases

### Webhook Testing
Perfect for testing webhook integrations during development:

```bash
# Your application sends webhook to hermes
curl -X PUT http://localhost:8000/webhooks/payment/completed \
     -H "Content-Type: application/json" \
     -d '{"payment_id": "12345", "status": "completed"}'
```

### API Development & Debugging
Use as a mock service to verify your API client is making correct requests:

```bash
# Test your API client against hermes
curl -X PUT http://localhost:8000/api/v2/users/update/profile
```

### Load Testing
Test PUT endpoint performance and routing logic.

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
```

## Configuration

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

## Support & Contributing

- **Issues**: Report bugs and feature requests on GitHub
- **Contributing**: Pull requests welcome
- **Documentation**: Full API docs available at `/docs` when running

---

**Version**: 1976.06.04.1  
**Maintainer**: basejumpa <basejumpa@encouraged-coders.de>
