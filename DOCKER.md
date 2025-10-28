# Docker Image Publishing Setup

This repository is configured to automatically build and publish Docker images to Cloudsmith.io using GitHub Actions.

## Repository Setup

The Docker images are published to: `docker.cloudsmith.io/hermesbaby/hermes/hermes`

## Required GitHub Secrets

To enable automatic publishing, you need to set up the following secrets in your GitHub repository:

1. Go to your GitHub repository
2. Navigate to Settings → Secrets and variables → Actions
3. Add the following repository secrets:

### CLOUDSMITH_USER
Your Cloudsmith username (usually your Cloudsmith account username)

### CLOUDSMITH_API_KEY
Your Cloudsmith API key with push permissions to the repository.

To get your API key:
1. Log in to [Cloudsmith.io](https://cloudsmith.io)
2. Go to Account Settings → API Keys
3. Create a new API key with appropriate permissions
4. Copy the key and add it as `CLOUDSMITH_API_KEY` secret

## How it Works

The GitHub Actions workflow (`.github/workflows/release.yml`) will:

1. **Trigger on:**
   - Push to `main` or `develop` branches
   - Push of version tags (e.g., `v1.0.0`)
   - Pull requests to `main` or `develop`

2. **Build Process:**
   - Uses Docker Buildx for multi-platform builds (AMD64 and ARM64)
   - Builds the Docker image using the `Dockerfile`
   - Tags images based on branch/tag/PR context

3. **Image Tags:**
   - `latest` - for main branch
   - Branch name - for branch pushes
   - `v1.2.3`, `v1.2`, `v1` - for semantic version tags
   - `main-abc123` - SHA-based tags
   - `pr-123` - for pull requests

4. **Security:**
   - Runs Trivy vulnerability scanning
   - Uploads security results to GitHub Security tab

## Manual Docker Usage

You can also build and run the image locally:

```bash
# Build the image
docker build -t hermes:local .

# Run the container
docker run -p 8000:8000 hermes:local

# Test the health endpoint
curl http://localhost:8000/health
```

## Pulling Published Images

Once published, you can pull images from Cloudsmith:

```bash
# Pull the latest image
docker pull docker.cloudsmith.io/hermesbaby/hermes/hermes:latest

# Pull a specific version
docker pull docker.cloudsmith.io/hermesbaby/hermes/hermes:v1.0.0

# Run the pulled image
docker run -p 8000:8000 docker.cloudsmith.io/hermesbaby/hermes/hermes:latest
```

## Troubleshooting

### Build Failures
- Check that all dependencies in `pyproject.toml` are correct
- Ensure the Dockerfile builds successfully locally first

### Authentication Issues
- Verify `CLOUDSMITH_USER` and `CLOUDSMITH_API_KEY` secrets are set correctly
- Ensure the API key has push permissions to the repository
- Check that the repository namespace `hermesbaby/hermes` exists in Cloudsmith

### Access Issues
- Make sure your Cloudsmith repository is configured to allow the authentication method you're using
- Verify the repository is public or that you have appropriate access rights