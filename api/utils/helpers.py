import os
import logging
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def get_slack_token() -> str:
    """Get the Slack bot token from environment variables."""
    token = os.getenv('SLACK_BOT_TOKEN')
    if not token:
        logging.error('SLACK_BOT_TOKEN is missing in environment variables.')
        raise ValueError('SLACK_BOT_TOKEN is missing in environment variables.')
    return token


def date_to_timestamp(date_obj: datetime.date) -> float:
    """Convert a date object to a Unix timestamp."""
    dt = datetime.combine(date_obj, datetime.min.time())
    return dt.timestamp()


def generate_job_id() -> str:
    """Generate a unique job ID."""
    return str(uuid.uuid4())


def save_job_data(job_id: str, data: Any) -> str:
    """Save job data to a file and return the file path."""
    # Create a jobs directory if it doesn't exist
    os.makedirs('jobs', exist_ok=True)
    
    # Save the data to a file
    file_path = f"jobs/{job_id}.json"
    with open(file_path, 'w') as f:
        json.dump(data, f)
    
    return file_path


def load_job_data(job_id: str) -> Optional[Any]:
    """Load job data from a file."""
    file_path = f"jobs/{job_id}.json"
    if not os.path.exists(file_path):
        logging.error(f"Job data file not found: {file_path}")
        return None
    
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading job data: {e}")
        return None
