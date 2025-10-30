from fastapi import FastAPI, Request, HTTPException, File, UploadFile, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
import pathlib
import importlib.metadata
import tarfile
import zipfile
import shutil
import tempfile
from typing import Optional, Annotated, Tuple, List
from pydantic_settings import BaseSettings
import py7zr

__version__ = importlib.metadata.version("hermesbaby.hermes")


class Settings(BaseSettings):
    """Configuration settings for Hermes API"""
    base_directory: str  # Required field with no default
    # Optional API token for securing PUT requests
    api_token: Optional[str] = None
    # Optional temporary directory for uploaded files (defaults to base_directory if not set)
    temp_directory: Optional[str] = None

    model_config = {
        "env_prefix": "HERMES_",
        "case_sensitive": False
    }


# Initialize settings - this will raise an error if HERMES_BASE_DIRECTORY is not set
settings = Settings()

app = FastAPI(title="Hermes API", version=__version__)

# Security scheme for API token
security = HTTPBearer(auto_error=False)


def get_archive_type(filename: str) -> str:
    """Determine the archive type from filename extension"""
    if not filename:
        return "unknown"

    filename_lower = filename.lower()
    if filename_lower.endswith('.tar.gz') or filename_lower.endswith('.tgz'):
        return "tar.gz"
    elif filename_lower.endswith('.zip'):
        return "zip"
    elif filename_lower.endswith('.7z'):
        return "7z"
    else:
        return "unknown"


def validate_archive_paths(paths: List[str], archive_type: str) -> None:
    """Validate that archive paths are safe to extract"""
    for path in paths:
        # Check for absolute paths
        if os.path.isabs(path):
            raise HTTPException(
                status_code=400,
                detail=f"Unsafe path in {archive_type} archive: {path} (absolute path)"
            )

        # Check for directory traversal
        if '..' in path or path.startswith('../'):
            raise HTTPException(
                status_code=400,
                detail=f"Unsafe path in {archive_type} archive: {path} (directory traversal)"
            )


def extract_tar_gz(temp_file_path: str, extract_path: pathlib.Path) -> List[str]:
    """Extract tar.gz archive and return list of extracted items"""
    extracted_items = []

    with tarfile.open(temp_file_path, 'r:gz') as tar:
        # Get all member names for security validation
        member_names = [member.name for member in tar.getmembers()]
        validate_archive_paths(member_names, "tar.gz")

        # Extract all contents to the target directory
        tar.extractall(path=extract_path, filter='data')
        extracted_items = member_names

    return extracted_items


def extract_zip(temp_file_path: str, extract_path: pathlib.Path) -> List[str]:
    """Extract ZIP archive and return list of extracted items"""
    extracted_items = []

    with zipfile.ZipFile(temp_file_path, 'r') as zip_file:
        # Get all file names for security validation
        file_names = zip_file.namelist()
        validate_archive_paths(file_names, "ZIP")

        # Extract all contents to the target directory
        zip_file.extractall(path=extract_path)
        extracted_items = file_names

    return extracted_items


def extract_7z(temp_file_path: str, extract_path: pathlib.Path) -> List[str]:
    """Extract 7z archive and return list of extracted items"""
    extracted_items = []

    with py7zr.SevenZipFile(temp_file_path, mode='r') as archive:
        # Get all file names for security validation
        file_names = archive.getnames()
        validate_archive_paths(file_names, "7z")

        # Extract all contents to the target directory
        archive.extractall(path=extract_path)
        extracted_items = file_names

    return extracted_items


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
async def extract_archive(
    path: str,
    file: UploadFile = File(...),
    _: None = Depends(verify_api_token)
):
    """Accept PUT requests with archive files (tar.gz, .tgz, .zip, .7z) and extract them to the specified path"""
    try:
        # Determine archive type and validate
        archive_type = get_archive_type(file.filename)
        if archive_type == "unknown":
            raise HTTPException(
                status_code=400,
                detail="File must be a supported archive format: .tar.gz, .tgz, .zip, or .7z"
            )

        # Construct the full path by joining base directory with the requested path
        full_path = pathlib.Path(settings.base_directory) / path.lstrip('/')

        # Validate that the base directory exists and is writable
        base_path = pathlib.Path(settings.base_directory)
        if not base_path.exists():
            raise HTTPException(
                status_code=500,
                detail=f"Base directory does not exist: {settings.base_directory}. Please ensure the directory is properly mounted and accessible."
            )

        if not os.access(base_path, os.W_OK):
            raise HTTPException(
                status_code=500,
                detail=f"Base directory is not writable: {settings.base_directory}. Please check directory permissions."
            )

        # Validate that the temp directory exists and is writable
        temp_dir = settings.temp_directory or settings.base_directory
        temp_path = pathlib.Path(temp_dir)
        if not temp_path.exists():
            raise HTTPException(
                status_code=500,
                detail=f"Temporary directory does not exist: {temp_dir}. Please ensure the directory is properly mounted and accessible."
            )

        if not os.access(temp_path, os.W_OK):
            raise HTTPException(
                status_code=500,
                detail=f"Temporary directory is not writable: {temp_dir}. Please check directory permissions."
            )

        # Remove existing content if the path exists
        if full_path.exists():
            if full_path.is_file():
                full_path.unlink()
            elif full_path.is_dir():
                shutil.rmtree(full_path)

        # Create the directory structure (including intermediate directories)
        try:
            full_path.mkdir(parents=True, exist_ok=True)
        except PermissionError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Permission denied creating directory: {full_path}. Error: {str(e)}. Please check directory permissions and ensure the container has write access."
            )

        # Determine appropriate file suffix for temporary file
        suffix_map = {
            "tar.gz": ".tar.gz",
            "zip": ".zip",
            "7z": ".7z"
        }
        temp_suffix = suffix_map.get(archive_type, ".tmp")

        # Create a temporary file to save the uploaded archive
        # Use the configured temp directory or fall back to base directory to avoid container /tmp space issues
        temp_dir = settings.temp_directory or settings.base_directory
        with tempfile.NamedTemporaryFile(delete=False, suffix=temp_suffix, dir=temp_dir) as temp_file:
            # Read and write the uploaded file content
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        try:
            # Extract the archive based on its type
            if archive_type == "tar.gz":
                extracted_paths = extract_tar_gz(temp_file_path, full_path)
            elif archive_type == "zip":
                extracted_paths = extract_zip(temp_file_path, full_path)
            elif archive_type == "7z":
                extracted_paths = extract_7z(temp_file_path, full_path)
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported archive format: {archive_type}"
                )

            # Get list of extracted files/directories at the root level for response
            extracted_items = list(full_path.iterdir())
            extracted_names = [item.name for item in extracted_items]

            return {
                "endpoint": f"/{path}",
                "method": "PUT",
                "created_path": str(full_path),
                "status": "extracted",
                "archive_type": archive_type,
                "filename": file.filename,
                "file_size": len(content),
                "extracted_items": extracted_names,
                "total_extracted_paths": len(extracted_paths)
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
            detail=f"Failed to extract archive: {str(e)}"
        )
