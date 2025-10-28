import pytest
import os
import pathlib
import tempfile
import tarfile
import zipfile
import io
import shutil
import subprocess
import sys
import importlib
from unittest.mock import patch
from fastapi.testclient import TestClient
import py7zr

# Test configuration
TEST_BASE_DIRECTORY = "/tmp/hermes_test"
TEST_API_TOKEN = "test-secret-token-12345"

# Mock the settings for tests - no token by default
with patch.dict(os.environ, {"HERMES_BASE_DIRECTORY": TEST_BASE_DIRECTORY}):
    from hermesbaby.hermes.main import app, settings

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


def create_test_zip(files_dict):
    """Create a test ZIP file with specified files and content"""
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for filename, content in files_dict.items():
            # Convert content to bytes if it's a string
            content_bytes = content.encode(
                'utf-8') if isinstance(content, str) else content
            # Add file to zip
            zip_file.writestr(filename, content_bytes)

    zip_buffer.seek(0)
    return zip_buffer.getvalue()


def create_test_7z(files_dict):
    """Create a test 7z file with specified files and content"""
    # Create a temporary directory to hold files
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = pathlib.Path(temp_dir)

        # Create files in the temporary directory
        for filename, content in files_dict.items():
            file_path = temp_path / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)

            content_bytes = content.encode(
                'utf-8') if isinstance(content, str) else content
            file_path.write_bytes(content_bytes)

        # Create 7z archive in memory
        archive_buffer = io.BytesIO()

        with py7zr.SevenZipFile(archive_buffer, 'w') as archive:
            for filename in files_dict.keys():
                file_path = temp_path / filename
                archive.write(file_path, filename)

        archive_buffer.seek(0)
        return archive_buffer.getvalue()


class TestConfiguration:
    """Test configuration requirements"""

    def test_missing_base_directory_environment_variable(self):
        """Test that the application fails to start without HERMES_BASE_DIRECTORY"""
        # Temporarily remove the environment variable and try to import
        import subprocess
        import sys
        import os

        # Get the project root directory dynamically
        project_root = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)))

        # Run a subprocess that tries to import without the env var
        # Create clean environment without HERMES_BASE_DIRECTORY
        clean_env = {k: v for k, v in os.environ.items()
                     if not k.startswith('HERMES_')}
        result = subprocess.run([
            sys.executable, "-c",
            "from hermesbaby.hermes.main import settings"
        ], capture_output=True, text=True, cwd=project_root, env=clean_env)

        # Should fail with non-zero exit code
        assert result.returncode != 0

        # Should contain validation error message
        assert "ValidationError" in result.stderr
        assert "base_directory" in result.stderr
        assert "Field required" in result.stderr

    def test_custom_base_directory_from_env(self):
        """Test that custom base directory is properly loaded from environment"""
        import subprocess
        import sys
        import os

        # Get the project root directory dynamically
        project_root = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)))

        # Run a subprocess with custom environment variable
        env = {"HERMES_BASE_DIRECTORY": "/custom/test/path"}
        result = subprocess.run([
            sys.executable, "-c",
            "from hermesbaby.hermes.main import settings; print(settings.base_directory)"
        ], capture_output=True, text=True, cwd=project_root, env={**os.environ, **env})

        # Should succeed
        assert result.returncode == 0
        assert "/custom/test/path" in result.stdout


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


class TestPutArchiveEndpoints:
    """Test PUT endpoints that extract archive files (tar.gz, zip, 7z)"""

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
        assert data["archive_type"] == "tar.gz"
        assert data["filename"] == "test.tar.gz"
        assert "extracted_items" in data
        assert "test.txt" in data["extracted_items"]
        assert "total_extracted_paths" in data

        # Verify the file was actually extracted
        created_path = pathlib.Path(data["created_path"])
        extracted_file = created_path / "test.txt"
        assert extracted_file.exists()
        assert extracted_file.read_text() == "Hello, World!"

        # Clean up
        if created_path.exists():
            shutil.rmtree(created_path)

    def test_put_simple_zip(self):
        """Test PUT request with a simple ZIP file"""
        # Create test ZIP with a simple file
        test_files = {
            "test.txt": "Hello from ZIP!"
        }
        zip_content = create_test_zip(test_files)

        files = {"file": ("test.zip", io.BytesIO(
            zip_content), "application/zip")}
        response = client.put("/test-zip", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["endpoint"] == "/test-zip"
        assert data["method"] == "PUT"
        assert "created_path" in data
        assert data["status"] == "extracted"
        assert data["archive_type"] == "zip"
        assert data["filename"] == "test.zip"
        assert "extracted_items" in data
        assert "test.txt" in data["extracted_items"]
        assert "total_extracted_paths" in data

        # Verify the file was actually extracted
        created_path = pathlib.Path(data["created_path"])
        extracted_file = created_path / "test.txt"
        assert extracted_file.exists()
        assert extracted_file.read_text() == "Hello from ZIP!"

        # Clean up
        if created_path.exists():
            shutil.rmtree(created_path)

    def test_put_simple_7z(self):
        """Test PUT request with a simple 7z file"""
        # Create test 7z with a simple file
        test_files = {
            "test.txt": "Hello from 7z!"
        }
        sevenz_content = create_test_7z(test_files)

        files = {"file": ("test.7z", io.BytesIO(
            sevenz_content), "application/x-7z-compressed")}
        response = client.put("/test-7z", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["endpoint"] == "/test-7z"
        assert data["method"] == "PUT"
        assert "created_path" in data
        assert data["status"] == "extracted"
        assert data["archive_type"] == "7z"
        assert data["filename"] == "test.7z"
        assert "extracted_items" in data
        assert "test.txt" in data["extracted_items"]
        assert "total_extracted_paths" in data

        # Verify the file was actually extracted
        created_path = pathlib.Path(data["created_path"])
        extracted_file = created_path / "test.txt"
        assert extracted_file.exists()
        assert extracted_file.read_text() == "Hello from 7z!"

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
        assert data["archive_type"] == "tar.gz"
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

    def test_put_nested_structure_zip(self):
        """Test PUT request with ZIP containing nested directory structure"""
        test_files = {
            "app/main.py": "print('Hello from ZIP main!')",
            "app/utils/helper.py": "def help(): pass",
            "config/settings.json": '{"debug": true, "format": "zip"}',
            "README.md": "# Test ZIP Project"
        }
        zip_content = create_test_zip(test_files)

        files = {"file": ("nested.zip", io.BytesIO(
            zip_content), "application/zip")}
        response = client.put("/projects/zipapp", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "extracted"
        assert data["archive_type"] == "zip"
        assert data["filename"] == "nested.zip"

        # Verify nested structure was created
        created_path = pathlib.Path(data["created_path"])
        assert (created_path / "app" / "main.py").exists()
        assert (created_path / "app" / "utils" / "helper.py").exists()
        assert (created_path / "config" / "settings.json").exists()
        assert (created_path / "README.md").exists()

        # Verify file contents
        assert (created_path / "app" /
                "main.py").read_text() == "print('Hello from ZIP main!')"
        assert (created_path / "config" /
                "settings.json").read_text() == '{"debug": true, "format": "zip"}'

        # Clean up
        if created_path.exists():
            shutil.rmtree(created_path)

    def test_put_nested_structure_7z(self):
        """Test PUT request with 7z containing nested directory structure"""
        test_files = {
            "app/main.py": "print('Hello from 7z main!')",
            "app/utils/helper.py": "def help(): pass",
            "config/settings.json": '{"debug": true, "format": "7z"}',
            "README.md": "# Test 7z Project"
        }
        sevenz_content = create_test_7z(test_files)

        files = {"file": ("nested.7z", io.BytesIO(
            sevenz_content), "application/x-7z-compressed")}
        response = client.put("/projects/sevenzapp", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "extracted"
        assert data["archive_type"] == "7z"
        assert data["filename"] == "nested.7z"

        # Verify nested structure was created
        created_path = pathlib.Path(data["created_path"])
        assert (created_path / "app" / "main.py").exists()
        assert (created_path / "app" / "utils" / "helper.py").exists()
        assert (created_path / "config" / "settings.json").exists()
        assert (created_path / "README.md").exists()

        # Verify file contents
        assert (created_path / "app" /
                "main.py").read_text() == "print('Hello from 7z main!')"
        assert (created_path / "config" /
                "settings.json").read_text() == '{"debug": true, "format": "7z"}'

        # Clean up
        if created_path.exists():
            shutil.rmtree(created_path)

    def test_put_replaces_existing_content(self):
        """Test that PUT request replaces existing content at the path"""
        # First, create some existing content
        test_path = pathlib.Path(settings.base_directory) / "replace-test"
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
        assert data["archive_type"] == "tar.gz"

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
        """Test PUT request with unsupported file type returns error"""
        # Create a regular text file
        files = {"file": ("test.txt", io.BytesIO(
            b"Not an archive"), "text/plain")}
        response = client.put("/invalid-test", files=files)

        assert response.status_code == 400
        data = response.json()
        assert "supported archive format" in data["detail"]
        assert ".tar.gz" in data["detail"]
        assert ".zip" in data["detail"]
        assert ".7z" in data["detail"]

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
        assert data["archive_type"] == "tar.gz"
        assert data["filename"] == "test.tgz"

        # Clean up
        created_path = pathlib.Path(data["created_path"])
        if created_path.exists():
            shutil.rmtree(created_path)

    def test_put_unsafe_paths_rejected_tarball(self):
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
        response = client.put("/security-test-tar", files=files)

        assert response.status_code == 400
        data = response.json()
        assert "Unsafe path" in data["detail"]
        assert "tar.gz" in data["detail"]

    def test_put_unsafe_paths_rejected_zip(self):
        """Test that ZIP files with unsafe paths are rejected"""
        # Create ZIP with unsafe path (directory traversal)
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
            # Try to create a file with directory traversal (unsafe)
            zip_file.writestr("../../../etc/passwd", b"Malicious content")

        zip_buffer.seek(0)
        files = {"file": ("malicious.zip", zip_buffer, "application/zip")}
        response = client.put("/security-test-zip", files=files)

        assert response.status_code == 400
        data = response.json()
        assert "Unsafe path" in data["detail"]
        assert "ZIP" in data["detail"]

    def test_put_unsafe_paths_rejected_7z(self):
        """Test that 7z files with unsafe paths are rejected"""
        # Since py7zr already prevents creation of archives with unsafe paths,
        # we'll create a valid 7z with a file that has directory traversal in name
        # by using a different approach to simulate the security check

        # Create test content with a directory traversal pattern
        test_files = {
            "../malicious.txt": "Malicious content"
        }

        # This will work because we're just using the name as a directory in our temp structure
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)

            # Create nested structure that includes the problematic path as a directory name
            problem_dir = temp_path / ".." / "malicious.txt"
            problem_dir.parent.mkdir(parents=True, exist_ok=True)
            problem_dir.write_text("Malicious content")

            # Create 7z archive
            archive_buffer = io.BytesIO()

            with py7zr.SevenZipFile(archive_buffer, 'w') as archive:
                # Add the file with the problematic relative path
                archive.write(problem_dir, "../malicious.txt")

            archive_buffer.seek(0)
            files = {"file": ("malicious.7z", archive_buffer,
                              "application/x-7z-compressed")}
            response = client.put("/security-test-7z", files=files)

            assert response.status_code == 400
            data = response.json()
            assert "Unsafe path" in data["detail"]
            assert "7z" in data["detail"]

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


class TestApiTokenSecurity:
    """Test API token authentication for PUT endpoints"""

    def test_put_without_token_when_no_token_configured(self):
        """Test PUT request succeeds when no API token is configured"""
        # Ensure no token is configured in settings
        with patch.dict(os.environ, {"HERMES_BASE_DIRECTORY": TEST_BASE_DIRECTORY}, clear=True):
            from hermesbaby.hermes.main import app
            test_client = TestClient(app)

            test_files = {"test.txt": "No token required"}
            tarball_content = create_test_tarball(test_files)
            files = {"file": ("test.tar.gz", io.BytesIO(
                tarball_content), "application/gzip")}

            response = test_client.put("/no-token-test", files=files)
            assert response.status_code == 200

            # Clean up
            data = response.json()
            created_path = pathlib.Path(data["created_path"])
            if created_path.exists():
                shutil.rmtree(created_path)

    def test_put_without_token_when_token_required(self):
        """Test PUT request fails when API token is required but not provided"""
        # Configure API token
        with patch.dict(os.environ, {
            "HERMES_BASE_DIRECTORY": TEST_BASE_DIRECTORY,
            "HERMES_API_TOKEN": TEST_API_TOKEN
        }, clear=True):
            # Force reload the module to pick up new environment
            import hermesbaby.hermes.main as main_module
            importlib.reload(main_module)
            test_client = TestClient(main_module.app)

            test_files = {"test.txt": "Token required"}
            tarball_content = create_test_tarball(test_files)
            files = {"file": ("test.tar.gz", io.BytesIO(
                tarball_content), "application/gzip")}

            response = test_client.put("/token-required-test", files=files)
            assert response.status_code == 401
            assert "API token required" in response.json()["detail"]
            assert response.headers.get("WWW-Authenticate") == "Bearer"

    def test_put_with_valid_bearer_token(self):
        """Test PUT request succeeds with valid Bearer token"""
        with patch.dict(os.environ, {
            "HERMES_BASE_DIRECTORY": TEST_BASE_DIRECTORY,
            "HERMES_API_TOKEN": TEST_API_TOKEN
        }, clear=True):
            # Force reload the module to pick up new environment
            import hermesbaby.hermes.main as main_module
            importlib.reload(main_module)
            test_client = TestClient(main_module.app)

            test_files = {"test.txt": "Valid token"}
            tarball_content = create_test_tarball(test_files)
            files = {"file": ("test.tar.gz", io.BytesIO(
                tarball_content), "application/gzip")}
            headers = {"Authorization": f"Bearer {TEST_API_TOKEN}"}

            response = test_client.put(
                "/valid-token-test", files=files, headers=headers)
            assert response.status_code == 200

            data = response.json()
            assert data["status"] == "extracted"
            assert data["archive_type"] == "tar.gz"

            # Clean up
            created_path = pathlib.Path(data["created_path"])
            if created_path.exists():
                shutil.rmtree(created_path)

    def test_put_with_valid_x_api_token_header(self):
        """Test PUT request succeeds with valid X-API-Token header"""
        with patch.dict(os.environ, {
            "HERMES_BASE_DIRECTORY": TEST_BASE_DIRECTORY,
            "HERMES_API_TOKEN": TEST_API_TOKEN
        }, clear=True):
            # Force reload the module to pick up new environment
            import hermesbaby.hermes.main as main_module
            importlib.reload(main_module)
            test_client = TestClient(main_module.app)

            test_files = {"test.txt": "Valid X-API-Token"}
            tarball_content = create_test_tarball(test_files)
            files = {"file": ("test.tar.gz", io.BytesIO(
                tarball_content), "application/gzip")}
            headers = {"X-API-Token": TEST_API_TOKEN}

            response = test_client.put(
                "/x-api-token-test", files=files, headers=headers)
            assert response.status_code == 200

            data = response.json()
            assert data["status"] == "extracted"

            # Clean up
            created_path = pathlib.Path(data["created_path"])
            if created_path.exists():
                shutil.rmtree(created_path)

    def test_put_with_invalid_bearer_token(self):
        """Test PUT request fails with invalid Bearer token"""
        with patch.dict(os.environ, {
            "HERMES_BASE_DIRECTORY": TEST_BASE_DIRECTORY,
            "HERMES_API_TOKEN": TEST_API_TOKEN
        }, clear=True):
            # Force reload the module to pick up new environment
            import hermesbaby.hermes.main as main_module
            importlib.reload(main_module)
            test_client = TestClient(main_module.app)

            test_files = {"test.txt": "Invalid token"}
            tarball_content = create_test_tarball(test_files)
            files = {"file": ("test.tar.gz", io.BytesIO(
                tarball_content), "application/gzip")}
            headers = {"Authorization": "Bearer wrong-token"}

            response = test_client.put(
                "/invalid-token-test", files=files, headers=headers)
            assert response.status_code == 401
            assert "Invalid API token" in response.json()["detail"]

    def test_put_with_invalid_x_api_token_header(self):
        """Test PUT request fails with invalid X-API-Token header"""
        with patch.dict(os.environ, {
            "HERMES_BASE_DIRECTORY": TEST_BASE_DIRECTORY,
            "HERMES_API_TOKEN": TEST_API_TOKEN
        }, clear=True):
            # Force reload the module to pick up new environment
            import hermesbaby.hermes.main as main_module
            importlib.reload(main_module)
            test_client = TestClient(main_module.app)

            test_files = {"test.txt": "Invalid X-API-Token"}
            tarball_content = create_test_tarball(test_files)
            files = {"file": ("test.tar.gz", io.BytesIO(
                tarball_content), "application/gzip")}
            headers = {"X-API-Token": "wrong-token"}

            response = test_client.put(
                "/invalid-x-api-token-test", files=files, headers=headers)
            assert response.status_code == 401
            assert "Invalid API token" in response.json()["detail"]

    def test_bearer_token_takes_precedence_over_x_api_token(self):
        """Test that Bearer token is used when both headers are present"""
        with patch.dict(os.environ, {
            "HERMES_BASE_DIRECTORY": TEST_BASE_DIRECTORY,
            "HERMES_API_TOKEN": TEST_API_TOKEN
        }, clear=True):
            # Force reload the module to pick up new environment
            import hermesbaby.hermes.main as main_module
            importlib.reload(main_module)
            test_client = TestClient(main_module.app)

            test_files = {"test.txt": "Precedence test"}
            tarball_content = create_test_tarball(test_files)
            files = {"file": ("test.tar.gz", io.BytesIO(
                tarball_content), "application/gzip")}
            headers = {
                "Authorization": f"Bearer {TEST_API_TOKEN}",  # Valid
                "X-API-Token": "wrong-token"  # Invalid, but should be ignored
            }

            response = test_client.put(
                "/precedence-test", files=files, headers=headers)
            assert response.status_code == 200

            # Clean up
            data = response.json()
            created_path = pathlib.Path(data["created_path"])
            if created_path.exists():
                shutil.rmtree(created_path)

    def test_health_endpoint_not_protected(self):
        """Test that health endpoint is not protected by API token"""
        with patch.dict(os.environ, {
            "HERMES_BASE_DIRECTORY": TEST_BASE_DIRECTORY,
            "HERMES_API_TOKEN": TEST_API_TOKEN
        }, clear=True):
            # Force reload the module to pick up new environment
            import hermesbaby.hermes.main as main_module
            importlib.reload(main_module)
            test_client = TestClient(main_module.app)

            # Should work without any token
            response = test_client.get("/health")
            assert response.status_code == 200
            assert response.json()["status"] == "ok"

    def test_api_token_configuration_from_environment(self):
        """Test that API token is properly loaded from environment variable"""
        with patch.dict(os.environ, {
            "HERMES_BASE_DIRECTORY": TEST_BASE_DIRECTORY,
            "HERMES_API_TOKEN": "custom-env-token"
        }):
            from hermesbaby.hermes.main import Settings
            test_settings = Settings()
            assert test_settings.api_token == "custom-env-token"


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
@pytest.mark.parametrize("archive_info", [
    ("tar.gz", "test.tar.gz", "application/gzip", create_test_tarball),
    ("zip", "test.zip", "application/zip", create_test_zip),
    ("7z", "test.7z", "application/x-7z-compressed", create_test_7z),
])
def test_put_various_endpoints_with_archives(endpoint, archive_info):
    """Parametrized test for various PUT endpoints with different archive formats"""
    archive_type, filename, content_type, create_func = archive_info

    # Ensure clean environment with no API token for these tests
    with patch.dict(os.environ, {"HERMES_BASE_DIRECTORY": TEST_BASE_DIRECTORY}, clear=True):
        import hermesbaby.hermes.main as main_module
        importlib.reload(main_module)
        test_client = TestClient(main_module.app)

        test_files = {
            "README.md": f"Test content for {endpoint} with {archive_type}",
            "data/info.txt": f"Some nested data in {archive_type}"
        }
        archive_content = create_func(test_files)

        files = {"file": (filename, io.BytesIO(archive_content), content_type)}
        response = test_client.put(endpoint, files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["endpoint"] == endpoint
        assert data["method"] == "PUT"
        assert "created_path" in data
        assert data["status"] == "extracted"
        assert data["archive_type"] == archive_type
        assert data["filename"] == filename
        assert "total_extracted_paths" in data

        # Clean up
        created_path = pathlib.Path(data["created_path"])
        if created_path.exists():
            shutil.rmtree(created_path)
