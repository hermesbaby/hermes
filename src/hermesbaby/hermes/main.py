from fastapi import FastAPI, Request, HTTPException
import os
import pathlib
import importlib.metadata

__version__ = importlib.metadata.version("hermesbaby.hermes")
app = FastAPI(title="Hermes API", version=__version__)

# Hardcoded base directory where paths will be created
BASE_DIRECTORY = "/tmp/hermes_files"


@app.get("/health")
async def health():
    return {"status": "ok", "service": "hermes", "version": __version__}


@app.put("/{path:path}")
async def create_path(path: str, request: Request):
    """Accept PUT requests to any endpoint and create the path on the local filesystem"""
    try:
        # Construct the full path by joining base directory with the requested path
        full_path = pathlib.Path(BASE_DIRECTORY) / path.lstrip('/')

        # Create the directory structure (including intermediate directories)
        full_path.mkdir(parents=True, exist_ok=True)

        return {
            "endpoint": f"/{path}",
            "method": "PUT",
            "created_path": str(full_path),
            "status": "created"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create path: {str(e)}")
