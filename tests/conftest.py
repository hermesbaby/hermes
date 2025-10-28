import pytest
import os
from unittest.mock import patch
from fastapi.testclient import TestClient

# Mock the settings for tests before importing the app
with patch.dict(os.environ, {"HERMES_BASE_DIRECTORY": "/tmp/hermes_test"}):
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
