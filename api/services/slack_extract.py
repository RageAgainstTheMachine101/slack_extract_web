import logging
import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from api.utils.helpers import get_slack_token, date_to_timestamp, is_vercel_environment
from api.utils.memory_storage import save_extract_data_to_memory

class SlackExtractService:
    def __init__(self):
        """Initialize the Slack extract service with a WebClient."""
        self.token = get_slack_token()
        self.client = WebClient(token=self.token)
        self.logger = logging.getLogger(__name__)
        self.channel_cache = {}  # Cache for channel information

    def get_channel_info(self, channel_id: str) -> Dict[str, str]:
        """Get information about a Slack channel."""
        # Return from cache if available
        if channel_id in self.channel_cache:
            return self.channel_cache[channel_id]
        
        try:
            self.logger.debug(f"Fetching info for channel {channel_id}")
            result = self.client.conversations_info(channel=channel_id)
            channel = result["channel"]
            channel_name = channel.get("name", "unknown")
            
            channel_info = {
                "name": channel_name,
                "topic": channel.get("topic", {}).get("value", ""),
                "purpose": channel.get("purpose", {}).get("value", "")
            }
            
            # Cache the result
            self.channel_cache[channel_id] = channel_info
            return channel_info
            
        except SlackApiError as e:
            self.logger.warning(f"Failed to get info for channel {channel_id}: {str(e)}")
            # Create a minimal channel info object for the cache
            channel_info = {"name": channel_id, "topic": "", "purpose": ""}
            self.channel_cache[channel_id] = channel_info
            return channel_info

    def filter_messages_by_date(
        self, 
        messages: List[Dict[str, Any]], 
        start_date: Optional[datetime.date] = None, 
        end_date: Optional[datetime.date] = None
    ) -> List[Dict[str, Any]]:
        """Filter messages by date range."""
        if not start_date and not end_date:
            return messages
            
        start_ts = date_to_timestamp(start_date) if start_date else None
        # Add one day to include messages from the end date
        end_ts = date_to_timestamp(end_date) + 86400 if end_date else None
        
        filtered_messages = []
        for message in messages:
            if 'ts' in message:
                timestamp = float(message['ts'])
                if (start_ts is None or start_ts <= timestamp) and (end_ts is None or timestamp <= end_ts):
                    filtered_messages.append(message)
                    
        return filtered_messages

    def format_message(self, message: Dict[str, Any]) -> str:
        """Format a Slack message with channel info and permalink."""
        formatted_text = ""
        
        # Add channel info if available
        if 'channel' in message:
            channel_id = message['channel']
            channel_data = self.get_channel_info(channel_id)
            
            formatted_text += f"[Channel: #{channel_data['name']}]\n"
            if channel_data['topic']:
                formatted_text += f"Topic: {channel_data['topic']}\n"
            if channel_data['purpose']:
                formatted_text += f"Purpose: {channel_data['purpose']}\n"
        
        # Add date
        if 'ts' in message:
            timestamp = float(message['ts'])
            message_date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
            formatted_text += f"Date: {message_date}\n"
        
        # Add permalink if available
        if 'permalink' in message:
            formatted_text += f"Link: {message['permalink']}\n"
        
        # Add message text
        if 'text' in message:
            formatted_text += f"Message: {message['text']}"
            
        return formatted_text

    def extract_messages(
        self, 
        messages: List[Dict[str, Any]], 
        start_date: Optional[datetime.date] = None, 
        end_date: Optional[datetime.date] = None
    ) -> Tuple[List[str], int]:
        """Extract and format messages from the given list, optionally filtering by date."""
        self.logger.info("Starting message extraction process")
        
        if start_date:
            self.logger.info(f"Filtering messages from {start_date.isoformat()}")
        if end_date:
            self.logger.info(f"Filtering messages until {end_date.isoformat()}")
            
        # Filter messages by date if needed
        filtered_messages = self.filter_messages_by_date(messages, start_date, end_date)
        self.logger.info(f"Filtered {len(filtered_messages)} messages from {len(messages)} total messages")
        
        # Format the filtered messages
        formatted_messages = []
        for message in filtered_messages:
            # Skip channel_join messages
            if message.get('subtype') == 'channel_join':
                continue
                
            if 'text' in message and message['text']:
                formatted_text = self.format_message(message)
                formatted_messages.append(formatted_text)
                
        self.logger.info(f"Formatted {len(formatted_messages)} messages")
        return formatted_messages, len(formatted_messages)

    def save_to_file(self, formatted_messages: List[str], file_path: str) -> bool:
        """Save formatted messages to a text file or in-memory storage."""
        try:
            if is_vercel_environment():
                # Extract the filename from the path
                extract_id = os.path.basename(file_path).split('.')[0]
                self.logger.info(f"Saving formatted messages to in-memory storage with key {extract_id}")
                
                # Join messages with double newlines for readability
                content = '\n\n'.join(formatted_messages)
                
                # Save to in-memory storage
                save_extract_data_to_memory(extract_id, content)
                return True
            else:
                # Use filesystem storage locally
                self.logger.info(f"Writing formatted messages to {file_path}")
                with open(file_path, 'w', encoding='utf-8') as txt_file:
                    for text in formatted_messages:
                        txt_file.write(text + '\n\n')  # Add two newlines between messages for readability
                return True
        except Exception as e:
            self.logger.error(f"Error writing to file or memory: {e}")
            return False
