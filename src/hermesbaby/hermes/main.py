from fastapi import FastAPI, Request, HTTPException, File, UploadFile, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
import pathlib
import importlib.metadata
import tarfile
import shutil
import tempfile
from typing import Optional, Annotated
from pydantic_settings import BaseSettings

__version__ = importlib.metadata.version("hermesbaby.hermes")


class Settings(BaseSettings):
    """Configuration settings for Hermes API"""
    base_directory: str  # Required field with no default
    # Optional API token for securing PUT requests
    api_token: Optional[str] = None

    model_config = {
        "env_prefix": "HERMES_",
        "case_sensitive": False
    }


# Initialize settings - this will raise an error if HERMES_BASE_DIRECTORY is not set
settings = Settings()

app = FastAPI(title="Hermes API", version=__version__)

# Security scheme for API token
security = HTTPBearer(auto_error=False)


async def verify_api_token(
    authorization: Annotated[Optional[HTTPAuthorizationCredentials], Depends(
        security)] = None,
    x_api_token: Annotated[Optional[str], Header(alias="X-API-Token")] = None
) -> None:
    """
    Verify API token if configured.

    Accepts token via:
    1. Authorization: Bearer <token>
    2. X-API-Token: <token>

    Raises HTTPException if token is required but invalid/missing.
    """
    # If no API token is configured, allow all requests
    if not settings.api_token:
        return

    # Extract token from either Authorization header or X-API-Token header
    provided_token = None
    if authorization and authorization.credentials:
        provided_token = authorization.credentials
    elif x_api_token:
        provided_token = x_api_token

    # If token is required but not provided, raise 401
    if not provided_token:
        raise HTTPException(
            status_code=401,
            detail="API token required. Provide via 'Authorization: Bearer <token>' or 'X-API-Token: <token>' header.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Verify token matches configured token
    if provided_token != settings.api_token:
        raise HTTPException(
            status_code=401,
            detail="Invalid API token",
            headers={"WWW-Authenticate": "Bearer"}
        )


@app.get("/health")
async def health():
    return {"status": "ok", "service": "hermes", "version": __version__}


@app.put("/{path:path}")
async def extract_tarball(
    path: str,
    file: UploadFile = File(...),
    _: None = Depends(verify_api_token)
):
    """Accept PUT requests with tar.gz files and extract them to the specified path"""
    try:
        # Validate that the uploaded file is a tar.gz file
        if not file.filename or not (file.filename.endswith('.tar.gz') or file.filename.endswith('.tgz')):
            raise HTTPException(
                status_code=400,
                detail="File must be a tar.gz or .tgz file"
            )

        # Construct the full path by joining base directory with the requested path
        full_path = pathlib.Path(settings.base_directory) / path.lstrip('/')

        # Remove existing content if the path exists
        if full_path.exists():
            if full_path.is_file():
                full_path.unlink()
            elif full_path.is_dir():
                shutil.rmtree(full_path)

        # Create the directory structure (including intermediate directories)
        full_path.mkdir(parents=True, exist_ok=True)

        # Create a temporary file to save the uploaded tar.gz
        with tempfile.NamedTemporaryFile(delete=False, suffix='.tar.gz') as temp_file:
            # Read and write the uploaded file content
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        try:
            # Extract the tar.gz file to the target directory
            with tarfile.open(temp_file_path, 'r:gz') as tar:
                # Security check: ensure all members are safe to extract
                for member in tar.getmembers():
                    if member.name.startswith('/') or '..' in member.name:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Unsafe path in archive: {member.name}"
                        )

                # Extract all contents to the target directory
                tar.extractall(path=full_path, filter='data')

            # Get list of extracted files/directories for response
            extracted_items = list(full_path.iterdir())
            extracted_names = [item.name for item in extracted_items]

            return {
                "endpoint": f"/{path}",
                "method": "PUT",
                "created_path": str(full_path),
                "status": "extracted",
                "filename": file.filename,
                "file_size": len(content),
                "extracted_items": extracted_names
            }

        finally:
            # Clean up the temporary file
            os.unlink(temp_file_path)

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to extract tarball: {str(e)}"
        )
