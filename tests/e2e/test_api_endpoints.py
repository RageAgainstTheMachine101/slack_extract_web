import json
import os
import pytest
from unittest.mock import patch, MagicMock, mock_open
from fastapi.testclient import TestClient

from api.main import app
from tests.mocks.api_mocks import (
    MOCK_AUTH_TEST_RESPONSE,
    generate_mock_conversations_history,
    MOCK_CONVERSATIONS_LIST_RESPONSE
)


@pytest.fixture
def test_client():
    """Return a TestClient instance for FastAPI app testing."""
    return TestClient(app)


@pytest.fixture
def mock_env_vars():
    """Mock environment variables for testing."""
    with patch.dict(os.environ, {
        "SLACK_BOT_TOKEN": "xoxb-test-token",
        "API_PASSWORD": "test-password"
    }):
        yield


@pytest.fixture
def mock_slack_services():
    """Mock Slack services for testing."""
    # Create mock instances to return
    mock_download = MagicMock()
    mock_download.check_token_scopes.return_value = True
    mock_download.download_user_messages.return_value = {
        "status": "success",
        "total_messages": 10,
        "messages": generate_mock_conversations_history()["messages"]
    }
    
    mock_extract = MagicMock()
    mock_extract.extract_messages.return_value = (
        ["Formatted message 1", "Formatted message 2"], 
        2
    )
    mock_extract.save_to_file.return_value = True
    
    yield mock_download, mock_extract


@pytest.fixture
def mock_file_operations():
    """Mock file operations for testing."""
    # Create a mock job data that will be returned by load_job_data
    mock_job_data = {
        "status": "success",
        "total_messages": 10,
        "messages": generate_mock_conversations_history()["messages"]
    }
    
    # Use a patcher to ensure the mock is applied correctly
    job_id_patcher = patch('api.routes.download.generate_job_id', return_value="test-job-id")
    save_job_patcher = patch('api.routes.download.save_job_data', return_value="jobs/test-job-id.json")
    load_job_patcher = patch('api.routes.extract.load_job_data', return_value=mock_job_data)
    makedirs_patcher = patch('os.makedirs', return_value=None)
    exists_patcher = patch('os.path.exists', return_value=True)
    
    # Start all patchers
    job_id_mock = job_id_patcher.start()
    save_job_mock = save_job_patcher.start()
    load_job_mock = load_job_patcher.start()
    makedirs_mock = makedirs_patcher.start()
    exists_mock = exists_patcher.start()
    
    yield
    
    # Stop all patchers
    job_id_patcher.stop()
    save_job_patcher.stop()
    load_job_patcher.stop()
    makedirs_patcher.stop()
    exists_patcher.stop()


class TestApiEndpoints:
    """Test cases for API endpoints."""

    def test_health_endpoint(self, test_client):
        """Test the health endpoint."""
        response = test_client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data

    def test_download_endpoint_no_auth(self, test_client, mock_env_vars):
        """Test download endpoint without authentication."""
        payload = {
            "user_id": "U12345",
            "start_date": "2023-01-01",
            "end_date": "2023-01-31"
        }
        response = test_client.post("/api/download", json=payload)
        assert response.status_code == 401
        assert "API password header missing" in response.json()["detail"]

    def test_download_endpoint_invalid_auth(self, test_client, mock_env_vars):
        """Test download endpoint with invalid authentication."""
        payload = {
            "user_id": "U12345",
            "start_date": "2023-01-01",
            "end_date": "2023-01-31"
        }
        headers = {"X-API-Password": "wrong-password"}
        response = test_client.post("/api/download", json=payload, headers=headers)
        assert response.status_code == 401
        assert "Invalid API password" in response.json()["detail"]

    def test_download_endpoint_success(self, test_client, mock_env_vars, mock_slack_services, mock_file_operations):
        """Test successful download endpoint."""
        payload = {
            "user_id": "U12345",
            "start_date": "2023-01-01",
            "end_date": "2023-01-31"
        }
        headers = {"X-API-Password": "test-password"}
        
        # Patch the SlackDownloadService class to return our mock instance
        with patch('api.routes.download.SlackDownloadService') as mock_service_class:
            mock_service_class.return_value = mock_slack_services[0]
            
            response = test_client.post("/api/download", json=payload, headers=headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["message_count"] == 10
            assert data["job_id"] == "test-job-id"
            assert "download_location" in data

    def test_extract_endpoint_no_auth(self, test_client, mock_env_vars):
        """Test extract endpoint without authentication."""
        payload = {
            "job_id": "test-job-id"
        }
        response = test_client.post("/api/extract", json=payload)
        assert response.status_code == 401
        assert "API password header missing" in response.json()["detail"]

    def test_extract_endpoint_invalid_auth(self, test_client, mock_env_vars):
        """Test extract endpoint with invalid authentication."""
        payload = {
            "job_id": "test-job-id"
        }
        headers = {"X-API-Password": "wrong-password"}
        response = test_client.post("/api/extract", json=payload, headers=headers)
        assert response.status_code == 401
        assert "Invalid API password" in response.json()["detail"]

    def test_extract_endpoint_success(self, test_client, mock_env_vars, mock_slack_services, mock_file_operations):
        """Test successful extract endpoint."""
        payload = {
            "job_id": "test-job-id",
            "start_date": "2023-01-01",
            "end_date": "2023-01-31"
        }
        headers = {"X-API-Password": "test-password"}
        
        # Patch the SlackExtractService class to return our mock instance
        with patch('api.routes.extract.SlackExtractService') as mock_service_class:
            mock_service_class.return_value = mock_slack_services[1]
            
            response = test_client.post("/api/extract", json=payload, headers=headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["extracted_message_count"] == 2
            assert "output_file_url" in data
            assert "messages" in data
