"""
Mock responses for Slack API testing.
"""
from datetime import datetime, timedelta

# Mock successful auth test response
MOCK_AUTH_TEST_RESPONSE = {
    "ok": True,
    "url": "https://test-team.slack.com/",
    "team": "Test Team",
    "user": "test_bot",
    "team_id": "T12345",
    "user_id": "U12345",
    "bot_id": "B12345",
    "response_metadata": {
        "scopes": [
            "channels:history",
            "channels:read",
            "chat:write",
            "groups:history",
            "groups:read",
            "im:history",
            "im:read",
            "mpim:history",
            "mpim:read",
            "users:read"
        ]
    }
}

# Mock conversations list response
MOCK_CONVERSATIONS_LIST_RESPONSE = {
    "ok": True,
    "channels": [
        {
            "id": "C12345",
            "name": "general",
            "is_channel": True,
            "is_group": False,
            "is_im": False,
            "is_mpim": False,
            "is_private": False,
            "created": 1609459200,  # 2021-01-01
            "creator": "U67890",
            "is_archived": False,
            "is_member": True,
            "topic": {
                "value": "General channel",
                "creator": "U67890",
                "last_set": 1609459200
            },
            "purpose": {
                "value": "This channel is for team-wide communication",
                "creator": "U67890",
                "last_set": 1609459200
            }
        },
        {
            "id": "C67890",
            "name": "random",
            "is_channel": True,
            "is_group": False,
            "is_im": False,
            "is_mpim": False,
            "is_private": False,
            "created": 1609459200,  # 2021-01-01
            "creator": "U67890",
            "is_archived": False,
            "is_member": True,
            "topic": {
                "value": "Random stuff",
                "creator": "U67890",
                "last_set": 1609459200
            },
            "purpose": {
                "value": "A place for non-work-related flimflam",
                "creator": "U67890",
                "last_set": 1609459200
            }
        }
    ],
    "response_metadata": {
        "next_cursor": ""
    }
}

# Mock conversations history response
def generate_mock_conversations_history(user_id="U12345", count=5, oldest=None, latest=None):
    """Generate mock conversation history with messages from the specified user."""
    now = datetime.now()
    
    # Default to last 7 days if not specified
    if not oldest:
        oldest_time = (now - timedelta(days=7)).timestamp()
    else:
        oldest_time = float(oldest)
        
    if not latest:
        latest_time = now.timestamp()
    else:
        latest_time = float(latest)
    
    # Generate messages with timestamps between oldest and latest
    time_range = latest_time - oldest_time
    messages = []
    
    for i in range(count):
        # Create a timestamp within the range
        msg_ts = oldest_time + (time_range * (i / count))
        
        messages.append({
            "type": "message",
            "user": user_id,
            "text": f"Test message {i+1}",
            "ts": str(msg_ts),
            "team": "T12345",
            "thread_ts": None if i % 3 != 0 else str(msg_ts - 0.001),  # Every 3rd message is in a thread
            "reply_count": 0 if i % 3 != 0 else 2,
            "reactions": [] if i % 2 == 0 else [
                {
                    "name": "thumbsup",
                    "users": ["U67890"],
                    "count": 1
                }
            ]
        })
    
    return {
        "ok": True,
        "messages": messages,
        "has_more": False,
        "response_metadata": {
            "next_cursor": ""
        }
    }

# Mock users info response
MOCK_USERS_INFO_RESPONSE = {
    "ok": True,
    "user": {
        "id": "U12345",
        "team_id": "T12345",
        "name": "testuser",
        "real_name": "Test User",
        "profile": {
            "real_name": "Test User",
            "display_name": "testuser",
            "email": "test@example.com",
            "image_24": "https://secure.gravatar.com/avatar/test.jpg",
            "image_32": "https://secure.gravatar.com/avatar/test.jpg",
            "image_48": "https://secure.gravatar.com/avatar/test.jpg",
            "image_72": "https://secure.gravatar.com/avatar/test.jpg",
            "image_192": "https://secure.gravatar.com/avatar/test.jpg",
            "image_512": "https://secure.gravatar.com/avatar/test.jpg"
        },
        "is_admin": False,
        "is_owner": False,
        "is_primary_owner": False,
        "is_restricted": False,
        "is_ultra_restricted": False,
        "is_bot": False,
        "is_app_user": False,
        "updated": 1609459200
    }
}
