import pytest
import os
import pathlib
import shutil
from unittest.mock import patch
from fastapi.testclient import TestClient

# Mock the settings for tests before importing the app
with patch.dict(os.environ, {"HERMES_BASE_DIRECTORY": "/tmp/hermes_test"}):
    from hermesbaby.hermes.main import app


@pytest.fixture(scope="session", autouse=True)
def setup_test_directories():
    """Set up test directories that are needed for the tests to run"""
    test_base_dir = pathlib.Path("/tmp/hermes_test")

    # Create the test base directory if it doesn't exist
    test_base_dir.mkdir(parents=True, exist_ok=True)

    yield

    # Clean up after all tests are done
    if test_base_dir.exists():
        shutil.rmtree(test_base_dir)


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
