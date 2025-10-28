import pytest
import os
import pathlib
import tempfile
from fastapi.testclient import TestClient
from hermesbaby.hermes.main import app, BASE_DIRECTORY

# Create a test client
client = TestClient(app)


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


class TestPutEndpoints:
    """Test PUT endpoints that create paths on the filesystem"""

    def test_put_root_endpoint(self):
        """Test PUT request to root endpoint / works via catch-all handler"""
        response = client.put("/")

        assert response.status_code == 200
        data = response.json()
        assert data["endpoint"] == "/"
        assert data["method"] == "PUT"
        assert "created_path" in data
        assert data["status"] == "created"

    def test_put_single_path(self):
        """Test PUT request to single path endpoint"""
        response = client.put("/users")

        assert response.status_code == 200
        data = response.json()
        assert data["endpoint"] == "/users"
        assert data["method"] == "PUT"
        assert "created_path" in data
        assert data["status"] == "created"
        assert data["created_path"].endswith("/users")

    def test_put_nested_path(self):
        """Test PUT request to nested path endpoint"""
        response = client.put("/api/v1/users")

        assert response.status_code == 200
        data = response.json()
        assert data["endpoint"] == "/api/v1/users"
        assert data["method"] == "PUT"
        assert "created_path" in data
        assert data["status"] == "created"
        assert data["created_path"].endswith("/api/v1/users")

    def test_put_path_with_numbers(self):
        """Test PUT request to path with numbers"""
        response = client.put("/users/123")

        assert response.status_code == 200
        data = response.json()
        assert data["endpoint"] == "/users/123"
        assert data["method"] == "PUT"
        assert "created_path" in data
        assert data["status"] == "created"
        assert data["created_path"].endswith("/users/123")

    def test_put_path_with_special_chars(self):
        """Test PUT request to path with special characters"""
        response = client.put("/api/v1/users-data_test")

        assert response.status_code == 200
        data = response.json()
        assert data["endpoint"] == "/api/v1/users-data_test"
        assert data["method"] == "PUT"
        assert "created_path" in data
        assert data["status"] == "created"
        assert data["created_path"].endswith("/api/v1/users-data_test")

    def test_put_deep_nested_path(self):
        """Test PUT request to deeply nested path"""
        response = client.put("/api/v1/organizations/123/users/456/profiles")

        assert response.status_code == 200
        data = response.json()
        assert data["endpoint"] == "/api/v1/organizations/123/users/456/profiles"
        assert data["method"] == "PUT"
        assert "created_path" in data
        assert data["status"] == "created"
        assert data["created_path"].endswith(
            "/api/v1/organizations/123/users/456/profiles")

    def test_put_with_json_body(self):
        """Test PUT request with JSON body - should still create path"""
        json_data = {"name": "test", "value": 123}
        response = client.put("/data", json=json_data)

        assert response.status_code == 200
        data = response.json()
        assert data["endpoint"] == "/data"
        assert data["method"] == "PUT"
        assert "created_path" in data
        assert data["status"] == "created"

    def test_put_with_headers(self):
        """Test PUT request with custom headers - should still create path"""
        headers = {"X-Custom-Header": "test-value"}
        response = client.put("/custom", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["endpoint"] == "/custom"
        assert data["method"] == "PUT"
        assert "created_path" in data
        assert data["status"] == "created"

    def test_directory_actually_created(self):
        """Test that directories are actually created on the filesystem"""
        test_path = "/test/filesystem/creation"
        response = client.put(test_path)

        assert response.status_code == 200
        data = response.json()
        created_path = data["created_path"]

        # Verify the directory actually exists
        assert os.path.exists(created_path)
        assert os.path.isdir(created_path)

        # Clean up the test directory
        import shutil
        test_base = pathlib.Path(BASE_DIRECTORY) / "test"
        if test_base.exists():
            shutil.rmtree(test_base)


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

    def test_put_root_handled_by_catch_all(self):
        """Test PUT request to root endpoint is handled by catch-all handler"""
        response = client.put("/")
        assert response.status_code == 200
        data = response.json()
        assert data["endpoint"] == "/"
        assert data["method"] == "PUT"
        assert "created_path" in data
        assert data["status"] == "created"


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
def test_put_various_endpoints(endpoint):
    """Parametrized test for various PUT endpoints (including root)"""
    response = client.put(endpoint)

    assert response.status_code == 200
    data = response.json()
    assert data["endpoint"] == endpoint
    assert data["method"] == "PUT"
    assert "created_path" in data
    assert data["status"] == "created"
