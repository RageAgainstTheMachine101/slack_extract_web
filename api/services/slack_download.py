import os
import json
import time
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from api.utils.helpers import get_slack_token, date_to_timestamp

class SlackDownloadService:
    def __init__(self):
        """Initialize the Slack download service with a WebClient."""
        self.token = get_slack_token()
        self.client = WebClient(token=self.token)
        self.logger = logging.getLogger(__name__)

    def check_token_scopes(self) -> bool:
        """Check and log the scopes available for the current token."""
        try:
            response = self.client.auth_test()
            if hasattr(response, 'data') and 'response_metadata' in response.data:
                scopes = response.data['response_metadata'].get('scopes', [])
                self.logger.info(f"Token scopes: {scopes}")
            else:
                self.logger.warning("Could not determine token scopes from response")
            return True
        except SlackApiError as e:
            self.logger.error(f"Error checking token: {e.response['error']}")
            if 'needed' in e.response:
                self.logger.error(f"Missing scopes: {e.response['needed']}")
            return False

    def fetch_messages(self, channel_id: str, oldest: Optional[float] = None, latest: Optional[float] = None) -> List[Dict[str, Any]]:
        """Fetch all messages from a channel within a date range."""
        all_messages = []
        cursor = None
        retry_delay = 1
        
        while True:
            try:
                result = self.client.conversations_history(
                    channel=channel_id,
                    cursor=cursor,
                    limit=200,
                    oldest=oldest,
                    latest=latest
                )
                messages = result["messages"]
                all_messages.extend(messages)
                cursor = result.get("response_metadata", {}).get("next_cursor")

                if not cursor:
                    break

                self.logger.info(f"Downloaded {len(all_messages)} messages from channel {channel_id}")
                retry_delay = 1  # Reset retry delay on success
            except SlackApiError as e:
                if e.response.status_code == 429:
                    self.logger.warning("Rate limited. Retrying...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                elif e.response["error"] == "missing_scope":
                    self.logger.error(f"Missing required scope to read channel {channel_id}. Error: {e}")
                    return all_messages  # Stop processing this channel
                elif e.response["error"] == "channel_not_found":
                    self.logger.error(f"Channel {channel_id} not found.")
                    return all_messages
                elif e.response["error"] == "not_in_channel":
                    self.logger.info(f"Bot is not in channel {channel_id}. Attempting to join...")
                    try:
                        self.client.conversations_join(channel=channel_id)
                        self.logger.info(f"Bot successfully joined channel {channel_id}")
                        # Retry after joining
                        continue
                    except SlackApiError as join_error:
                        self.logger.error(f"Failed to join channel {channel_id}: {join_error}")
                        return all_messages
                else:
                    self.logger.error(f"Error downloading messages from channel {channel_id}. Error: {e}")
                    break
            except Exception as e:
                self.logger.error(f"Unexpected error downloading messages from channel {channel_id}. Error: {e}")
                break

        return all_messages

    def get_users_conversations(self, user_id: str) -> List[Dict[str, str]]:
        """Get all channels that a user is a member of."""
        cache_file = f"channel_cache_{user_id}.json"
        
        # Try to use cached channel list if available and recent
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r") as f:
                    cache_data = json.load(f)
                    cached_user_id = cache_data.get("user_id")
                    cached_channels = cache_data.get("channels")
                    cache_time = cache_data.get("timestamp", 0)
                    
                    # Use cache if it's for the same user and less than 1 day old
                    if cached_user_id == user_id and time.time() - cache_time < 86400:
                        self.logger.info("Using cached channel list")
                        return cached_channels
            except json.JSONDecodeError:
                self.logger.warning("Error decoding cache file, fetching new channel list")

        # Fetch channels from Slack API
        channels = []
        cursor = None
        
        while True:
            try:
                response = self.client.users_conversations(
                    user=user_id, 
                    types="public_channel,private_channel", 
                    cursor=cursor
                )
                channels.extend([{"id": channel["id"], "name": channel["name"]} for channel in response["channels"]])
                cursor = response.get("response_metadata", {}).get("next_cursor")
                
                if not cursor:
                    break
            except SlackApiError as e:
                self.logger.error(f"Error fetching channels for user {user_id}: {e}")
                break

        # Save to cache
        with open(cache_file, "w") as f:
            json.dump({
                "user_id": user_id, 
                "channels": channels,
                "timestamp": time.time()
            }, f)

        return channels

    def add_message_metadata(self, message: Dict[str, Any], channel_id: str, channel_name: str) -> Dict[str, Any]:
        """Add channel info and permalink to a message."""
        message['channel'] = channel_id
        message['channel_name'] = channel_name
        
        # Get permalink for the message
        try:
            permalink_response = self.client.chat_getPermalink(
                channel=channel_id, 
                message_ts=message['ts']
            )
            if permalink_response['ok']:
                message['permalink'] = permalink_response['permalink']
        except SlackApiError as e:
            self.logger.error(f"Error getting permalink for message: {e}")
            message['permalink'] = None
            
        return message

    def download_user_messages(self, user_id: str, start_date: datetime.date, end_date: datetime.date) -> Dict[str, Any]:
        """Download messages from a specified Slack user within a given date range."""
        start_ts = date_to_timestamp(start_date)
        # Add one day to include messages from the end date
        end_ts = date_to_timestamp(end_date) + 86400  
        
        channels = self.get_users_conversations(user_id)
        if not channels:
            self.logger.error("No channels found or error getting channels")
            return {"status": "error", "messages": [], "error": "No channels found"}
        
        all_messages = []
        channel_count = 0
        total_channels = len(channels)
        
        for channel in channels:
            channel_count += 1
            channel_id = channel["id"]
            channel_name = channel["name"]
            
            self.logger.info(f"Processing channel {channel_count}/{total_channels}: {channel_name}")
            
            messages = self.fetch_messages(channel_id, oldest=start_ts, latest=end_ts)
            if messages:
                # Filter messages by user_id and add channel info
                user_messages = [msg for msg in messages if msg.get('user') == user_id]
                
                for message in user_messages:
                    # Add channel info and permalink
                    message = self.add_message_metadata(message, channel_id, channel_name)
                    all_messages.append(message)
                    
                    # If the message is a thread starter, fetch its replies
                    if message.get('thread_ts') and message.get('reply_count', 0) > 0:
                        try:
                            replies_result = self.client.conversations_replies(
                                channel=channel_id, 
                                ts=message['thread_ts']
                            )
                            
                            # Add replies that are from the user
                            for reply in replies_result.get('messages', []):
                                if reply.get('user') == user_id and reply.get('ts') != message.get('ts'):
                                    reply = self.add_message_metadata(reply, channel_id, channel_name)
                                    all_messages.append(reply)
                        except SlackApiError as e:
                            self.logger.error(f"Error fetching replies: {e}")
        
        return {
            "status": "success",
            "messages": all_messages,
            "user_id": user_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_messages": len(all_messages)
        }
