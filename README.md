# HermesBaby-Hermes

The central place of docs-as-code based information in corporate environments

## Devcontainer

This folder contains the **development container** configuration for working on Hermes
using **VS Code Devcontainers** or **GitHub Codespaces**.

### Features

- Python 3.12 base image
- Poetry for dependency management
- Docker client support (build/test images inside the container)
- Preinstalled VS Code extensions: Python, Pylance, Docker, GitHub Actions, Jupyter

### Usage

#### Local (VS Code + Docker Desktop / WSL2)

1. Ensure Docker is running.
2. Open this repo in VS Code.
3. Use the **"Reopen in Container"** prompt.

#### GitHub Codespaces

1. Open the repo in Codespaces.
2. The container will be built automatically.
3. Poetry will install dependencies on first start.

#### Running the App

Inside the devcontainer, run:

```bash
poetry install

poetry run uvicorn hermesbaby.hermes.main:app --reload --host 0.0.0.0 --port 8000
```

The FastAPI app will be available on <http://localhost:8000>
