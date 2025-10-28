import pytest
from fastapi.testclient import TestClient
from hermesbaby.hermes.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def sample_endpoints():
    """Sample endpoints for testing (including root handled by catch-all)"""
    return [
        "/",
        "/users",
        "/api/v1/data",
        "/organizations/123",
        "/users/456/profile",
        "/very/deep/nested/path",
    ]
