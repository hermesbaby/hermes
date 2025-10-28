import pytest
import os
import pathlib
import tempfile
import tarfile
import io
import shutil
from fastapi.testclient import TestClient
from hermesbaby.hermes.main import app, BASE_DIRECTORY

# Create a test client
client = TestClient(app)


def create_test_tarball(files_dict):
    """Create a test tar.gz file with specified files and content"""
    tar_buffer = io.BytesIO()

    with tarfile.open(fileobj=tar_buffer, mode='w:gz') as tar:
        for filename, content in files_dict.items():
            # Create file-like object from content
            content_bytes = content.encode(
                'utf-8') if isinstance(content, str) else content
            file_buffer = io.BytesIO(content_bytes)

            # Create TarInfo object
            tarinfo = tarfile.TarInfo(name=filename)
            tarinfo.size = len(content_bytes)

            # Add to tar
            tar.addfile(tarinfo, file_buffer)

    tar_buffer.seek(0)
    return tar_buffer.getvalue()


class TestHealthEndpoint:
    """Test the health endpoint"""

    def test_health_get_success(self):
        """Test GET /health returns successful health check"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "hermes"
        assert "version" in data
        assert isinstance(data["version"], str)


class TestPutTarballEndpoints:
    """Test PUT endpoints that extract tar.gz files"""

    def test_put_simple_tarball(self):
        """Test PUT request with a simple tar.gz file"""
        # Create test tarball with a simple file
        test_files = {
            "test.txt": "Hello, World!"
        }
        tarball_content = create_test_tarball(test_files)

        files = {"file": ("test.tar.gz", io.BytesIO(
            tarball_content), "application/gzip")}
        response = client.put("/test-simple", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["endpoint"] == "/test-simple"
        assert data["method"] == "PUT"
        assert "created_path" in data
        assert data["status"] == "extracted"
        assert data["filename"] == "test.tar.gz"
        assert "extracted_items" in data
        assert "test.txt" in data["extracted_items"]

        # Verify the file was actually extracted
        created_path = pathlib.Path(data["created_path"])
        extracted_file = created_path / "test.txt"
        assert extracted_file.exists()
        assert extracted_file.read_text() == "Hello, World!"

        # Clean up
        if created_path.exists():
            shutil.rmtree(created_path)

    def test_put_nested_structure_tarball(self):
        """Test PUT request with tar.gz containing nested directory structure"""
        test_files = {
            "app/main.py": "print('Hello from main!')",
            "app/utils/helper.py": "def help(): pass",
            "config/settings.json": '{"debug": true}',
            "README.md": "# Test Project"
        }
        tarball_content = create_test_tarball(test_files)

        files = {"file": ("nested.tar.gz", io.BytesIO(
            tarball_content), "application/gzip")}
        response = client.put("/projects/myapp", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "extracted"
        assert data["filename"] == "nested.tar.gz"

        # Verify nested structure was created
        created_path = pathlib.Path(data["created_path"])
        assert (created_path / "app" / "main.py").exists()
        assert (created_path / "app" / "utils" / "helper.py").exists()
        assert (created_path / "config" / "settings.json").exists()
        assert (created_path / "README.md").exists()

        # Verify file contents
        assert (created_path / "app" /
                "main.py").read_text() == "print('Hello from main!')"
        assert (created_path / "config" /
                "settings.json").read_text() == '{"debug": true}'

        # Clean up
        if created_path.exists():
            shutil.rmtree(created_path)

    def test_put_replaces_existing_content(self):
        """Test that PUT request replaces existing content at the path"""
        # First, create some existing content
        test_path = pathlib.Path(BASE_DIRECTORY) / "replace-test"
        test_path.mkdir(parents=True, exist_ok=True)
        (test_path / "old_file.txt").write_text("This should be removed")
        (test_path / "old_dir").mkdir(exist_ok=True)
        (test_path / "old_dir" / "nested.txt").write_text("Also should be removed")

        # Now upload new content via tar.gz
        test_files = {
            "new_file.txt": "New content here",
            "new_dir/new_nested.txt": "New nested content"
        }
        tarball_content = create_test_tarball(test_files)

        files = {"file": ("replacement.tar.gz", io.BytesIO(
            tarball_content), "application/gzip")}
        response = client.put("/replace-test", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "extracted"

        # Verify old content is gone and new content exists
        created_path = pathlib.Path(data["created_path"])
        assert not (created_path / "old_file.txt").exists()
        assert not (created_path / "old_dir").exists()
        assert (created_path / "new_file.txt").exists()
        assert (created_path / "new_dir" / "new_nested.txt").exists()

        # Clean up
        if created_path.exists():
            shutil.rmtree(created_path)

    def test_put_invalid_file_type(self):
        """Test PUT request with non-tar.gz file returns error"""
        # Create a regular text file
        files = {"file": ("test.txt", io.BytesIO(
            b"Not a tarball"), "text/plain")}
        response = client.put("/invalid-test", files=files)

        assert response.status_code == 400
        data = response.json()
        assert "must be a tar.gz" in data["detail"]

    def test_put_tgz_extension(self):
        """Test PUT request with .tgz extension works"""
        test_files = {
            "test.txt": "TGZ test content"
        }
        tarball_content = create_test_tarball(test_files)

        files = {"file": ("test.tgz", io.BytesIO(
            tarball_content), "application/gzip")}
        response = client.put("/tgz-test", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "extracted"
        assert data["filename"] == "test.tgz"

        # Clean up
        created_path = pathlib.Path(data["created_path"])
        if created_path.exists():
            shutil.rmtree(created_path)

    def test_put_unsafe_paths_rejected(self):
        """Test that tar.gz files with unsafe paths are rejected"""
        # Create tarball with unsafe path
        tar_buffer = io.BytesIO()

        with tarfile.open(fileobj=tar_buffer, mode='w:gz') as tar:
            # Try to create a file with absolute path (unsafe)
            content = b"Malicious content"
            file_buffer = io.BytesIO(content)
            # Absolute path - unsafe
            tarinfo = tarfile.TarInfo(name="/etc/passwd")
            tarinfo.size = len(content)
            tar.addfile(tarinfo, file_buffer)

        tar_buffer.seek(0)
        files = {"file": ("malicious.tar.gz", tar_buffer, "application/gzip")}
        response = client.put("/security-test", files=files)

        assert response.status_code == 400
        data = response.json()
        assert "Unsafe path" in data["detail"]

    def test_put_no_file_provided(self):
        """Test PUT request without file returns validation error"""
        response = client.put("/no-file-test")

        assert response.status_code == 422  # FastAPI validation error


class TestOtherHttpMethods:
    """Test that other HTTP methods don't interfere with PUT endpoints"""

    def test_get_undefined_endpoint_fails(self):
        """Test GET request to endpoint with PUT handler returns 405 Method Not Allowed"""
        response = client.get("/undefined")
        assert response.status_code == 405

    def test_post_undefined_endpoint_fails(self):
        """Test POST request to endpoint with PUT handler returns 405 Method Not Allowed"""
        response = client.post("/undefined")
        assert response.status_code == 405

    def test_delete_undefined_endpoint_fails(self):
        """Test DELETE request to endpoint with PUT handler returns 405 Method Not Allowed"""
        response = client.delete("/undefined")
        assert response.status_code == 405

    def test_patch_undefined_endpoint_fails(self):
        """Test PATCH request to endpoint with PUT handler returns 405 Method Not Allowed"""
        response = client.patch("/undefined")
        assert response.status_code == 405


class TestApiMetadata:
    """Test API metadata and configuration"""

    def test_openapi_schema_accessible(self):
        """Test that OpenAPI schema is accessible"""
        response = client.get("/openapi.json")
        assert response.status_code == 200

        schema = response.json()
        assert schema["info"]["title"] == "Hermes API"
        assert "paths" in schema
        assert "/health" in schema["paths"]

    def test_docs_accessible(self):
        """Test that API documentation is accessible"""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


@pytest.mark.parametrize("endpoint", [
    "/",
    "/test",
    "/api/v1/test",
    "/users/123/profile",
    "/very/deep/nested/path/structure",
    "/path-with-dashes",
    "/path_with_underscores",
    "/123numbers456",
])
def test_put_various_endpoints_with_tarball(endpoint):
    """Parametrized test for various PUT endpoints with tar.gz files"""
    test_files = {
        "README.md": f"Test content for {endpoint}",
        "data/info.txt": "Some nested data"
    }
    tarball_content = create_test_tarball(test_files)

    files = {"file": ("test.tar.gz", io.BytesIO(
        tarball_content), "application/gzip")}
    response = client.put(endpoint, files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["endpoint"] == endpoint
    assert data["method"] == "PUT"
    assert "created_path" in data
    assert data["status"] == "extracted"
    assert data["filename"] == "test.tar.gz"

    # Clean up
    created_path = pathlib.Path(data["created_path"])
    if created_path.exists():
        shutil.rmtree(created_path)
