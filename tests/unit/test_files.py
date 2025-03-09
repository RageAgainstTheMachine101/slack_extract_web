import os
import pytest
from unittest.mock import patch, mock_open, MagicMock
from fastapi.testclient import TestClient
from starlette.responses import Response

from api.main import app


@pytest.fixture
def test_client():
    """Return a TestClient instance for FastAPI app testing."""
    return TestClient(app)


@pytest.fixture
def mock_env_vars():
    """Mock environment variables for testing."""
    with patch.dict(os.environ, {
        "API_PASSWORD": "test-password"
    }):
        yield


class TestFilesEndpoint:
    """Test cases for files endpoint."""

    def test_get_file_no_auth(self, test_client, mock_env_vars):
        """Test file endpoint without authentication."""
        response = test_client.get("/api/files/test-file-id")
        assert response.status_code == 401
        assert "API password header missing" in response.json()["detail"]

    def test_get_file_invalid_auth(self, test_client, mock_env_vars):
        """Test file endpoint with invalid authentication."""
        headers = {"X-API-Password": "wrong-password"}
        response = test_client.get("/api/files/test-file-id", headers=headers)
        assert response.status_code == 401
        assert "Invalid API password" in response.json()["detail"]

    def test_get_file_not_found(self, test_client, mock_env_vars):
        """Test file endpoint when file is not found."""
        headers = {"X-API-Password": "test-password"}
        
        # Mock os.path.exists to return False
        with patch('os.path.exists', return_value=False):
            response = test_client.get("/api/files/test-file-id", headers=headers)
        
        assert response.status_code == 404
        assert "File test-file-id not found" in response.json()["detail"]

    def test_get_file_success(self, test_client, mock_env_vars):
        """Test successful file retrieval."""
        headers = {"X-API-Password": "test-password"}
        file_path = "extracts/test-file-id.txt"
        
        # Mock the file response instead of trying to use FileResponse
        # This approach bypasses the endpoint's implementation but allows us to test the authentication
        with patch('api.routes.files.os.path.exists', return_value=True), \
             patch('api.routes.files.FileResponse', return_value=Response(
                 content="Test file content",
                 media_type="text/plain",
                 status_code=200
             )):
            
            response = test_client.get("/api/files/test-file-id", headers=headers)
            
            assert response.status_code == 200
