import pytest
from unittest.mock import patch, MagicMock
from datetime import date

from api.services.slack_download import SlackDownloadService
from tests.mocks.api_mocks import (
    MOCK_AUTH_TEST_RESPONSE,
    MOCK_CONVERSATIONS_LIST_RESPONSE,
    generate_mock_conversations_history,
    MOCK_USERS_INFO_RESPONSE
)


class TestSlackDownloadService:
    """Test cases for SlackDownloadService."""

    @pytest.fixture
    def mock_slack_client(self):
        """Create a mock Slack client."""
        with patch('api.services.slack_download.WebClient') as mock_client:
            # Setup mock responses
            mock_instance = mock_client.return_value
            
            # Auth test
            mock_instance.auth_test.return_value.data = MOCK_AUTH_TEST_RESPONSE
            
            # Conversations list
            mock_instance.conversations_list.return_value = MOCK_CONVERSATIONS_LIST_RESPONSE
            
            # Conversations history
            mock_instance.conversations_history.return_value = generate_mock_conversations_history()
            
            # Users info
            mock_instance.users_info.return_value = MOCK_USERS_INFO_RESPONSE
            
            # Users conversations
            mock_instance.users_conversations.return_value = {
                "ok": True,
                "channels": [
                    {"id": "C12345", "name": "general"},
                    {"id": "C67890", "name": "random"}
                ],
                "response_metadata": {"next_cursor": ""}
            }
            
            # Chat get permalink
            mock_instance.chat_getPermalink.return_value = {
                "ok": True,
                "permalink": "https://slack.com/archives/C12345/p1234567890"
            }
            
            # Conversations replies
            mock_instance.conversations_replies.return_value = {
                "ok": True,
                "messages": [],
                "has_more": False
            }
            
            yield mock_instance

    @pytest.fixture
    def download_service(self, mock_slack_client):
        """Create a SlackDownloadService with mocked client."""
        with patch('api.services.slack_download.get_slack_token', return_value="xoxb-test-token"):
            service = SlackDownloadService()
            # Replace the client with our mock
            service.client = mock_slack_client
            return service

    def test_check_token_scopes(self, download_service, mock_slack_client):
        """Test check_token_scopes method."""
        # Test successful case
        result = download_service.check_token_scopes()
        assert result is True
        mock_slack_client.auth_test.assert_called_once()
        
        # Reset the mock for the error case
        mock_slack_client.auth_test.reset_mock()
        
        # Test error case with a specific exception
        from slack_sdk.errors import SlackApiError
        mock_response = MagicMock()
        mock_response.__getitem__.side_effect = lambda x: "missing_scope" if x == "error" else None
        mock_slack_client.auth_test.side_effect = SlackApiError("API error", mock_response)
        
        result = download_service.check_token_scopes()
        assert result is False
        mock_slack_client.auth_test.assert_called_once()

    def test_fetch_messages(self, download_service, mock_slack_client):
        """Test fetch_messages method."""
        # Setup mock response
        mock_slack_client.conversations_history.return_value = generate_mock_conversations_history(count=10)
        
        # Test fetching messages
        messages = download_service.fetch_messages("C12345")
        assert len(messages) == 10
        mock_slack_client.conversations_history.assert_called_with(
            channel="C12345",
            cursor=None,
            limit=200,
            oldest=None,
            latest=None
        )
        
        # Test with date range
        oldest = 1609459200  # 2021-01-01
        latest = 1612137600  # 2021-02-01
        download_service.fetch_messages("C12345", oldest=oldest, latest=latest)
        mock_slack_client.conversations_history.assert_called_with(
            channel="C12345",
            cursor=None,
            limit=200,
            oldest=oldest,
            latest=latest
        )

    def test_download_user_messages(self, download_service, mock_slack_client):
        """Test download_user_messages method."""
        # Mock the file operations to avoid file system interactions
        with patch('os.path.exists', return_value=False), \
             patch('builtins.open', MagicMock()), \
             patch('json.dump', MagicMock()):
            
            # Setup mock responses for get_users_conversations
            mock_channels = [
                {"id": "C12345", "name": "general"},
                {"id": "C67890", "name": "random"}
            ]
            
            # Mock fetch_messages to return controlled data
            with patch.object(
                download_service, 
                'get_users_conversations', 
                return_value=mock_channels
            ), patch.object(
                download_service, 
                'fetch_messages', 
                return_value=generate_mock_conversations_history(count=5)["messages"]
            ), patch.object(
                download_service,
                'add_message_metadata',
                side_effect=lambda msg, cid, cname: {**msg, "channel": cid, "channel_name": cname, "permalink": "https://slack.com/archives/C12345/p1234567890"}
            ):
                
                # Test downloading messages
                start_date = date(2023, 1, 1)
                end_date = date(2023, 1, 31)
                result = download_service.download_user_messages("U12345", start_date, end_date)
                
                # Verify result structure
                assert result["status"] == "success"
                assert "total_messages" in result
                assert "messages" in result
                assert isinstance(result["messages"], list)
