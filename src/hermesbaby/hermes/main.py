from fastapi import FastAPI, Request, HTTPException, File, UploadFile
import os
import pathlib
import importlib.metadata
import tarfile
import shutil
import tempfile
from typing import Optional

__version__ = importlib.metadata.version("hermesbaby.hermes")
app = FastAPI(title="Hermes API", version=__version__)

# Hardcoded base directory where paths will be created
BASE_DIRECTORY = "/tmp/hermes_files"


@app.get("/health")
async def health():
    return {"status": "ok", "service": "hermes", "version": __version__}


@app.put("/{path:path}")
async def extract_tarball(path: str, file: UploadFile = File(...)):
    """Accept PUT requests with tar.gz files and extract them to the specified path"""
    try:
        # Validate that the uploaded file is a tar.gz file
        if not file.filename or not (file.filename.endswith('.tar.gz') or file.filename.endswith('.tgz')):
            raise HTTPException(
                status_code=400,
                detail="File must be a tar.gz or .tgz file"
            )

        # Construct the full path by joining base directory with the requested path
        full_path = pathlib.Path(BASE_DIRECTORY) / path.lstrip('/')

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
