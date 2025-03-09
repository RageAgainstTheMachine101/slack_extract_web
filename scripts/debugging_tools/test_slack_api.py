#!/usr/bin/env python
"""
Debugging tool for testing Slack API interactions directly.
This script allows you to test the Slack API functionality without going through the FastAPI endpoints.
"""
import os
import sys
import json
import logging
import argparse
from datetime import date, datetime, timedelta
from dotenv import load_dotenv

# Add the parent directory to the path so we can import the API modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.services.slack_download import SlackDownloadService
from api.services.slack_extract import SlackExtractService


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def check_token():
    """Check if the Slack token is configured and has the required scopes."""
    service = SlackDownloadService()
    if service.check_token_scopes():
        logger.info("✅ Slack token is valid and has the required scopes")
        return True
    else:
        logger.error("❌ Slack token is invalid or missing required scopes")
        return False


def download_messages(user_id, start_date_str, end_date_str, output_file=None):
    """Download messages for a user within a date range."""
    try:
        # Parse dates
        start_date = date.fromisoformat(start_date_str)
        end_date = date.fromisoformat(end_date_str)
        
        # Create service and download messages
        service = SlackDownloadService()
        result = service.download_user_messages(user_id, start_date, end_date)
        
        if result["status"] == "error":
            logger.error(f"❌ Error downloading messages: {result.get('error', 'Unknown error')}")
            return False
        
        # Print summary
        logger.info(f"✅ Successfully downloaded {result['total_messages']} messages")
        
        # Save to file if requested
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2)
            logger.info(f"✅ Saved messages to {output_file}")
        
        return result
    
    except Exception as e:
        logger.exception(f"❌ Error downloading messages: {str(e)}")
        return False


def extract_messages(messages_file, start_date_str=None, end_date_str=None, output_file=None):
    """Extract and format messages from a previously downloaded file."""
    try:
        # Load messages from file
        with open(messages_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        messages = data.get("messages", [])
        if not messages:
            logger.error("❌ No messages found in the input file")
            return False
        
        # Parse dates if provided
        start_date = date.fromisoformat(start_date_str) if start_date_str else None
        end_date = date.fromisoformat(end_date_str) if end_date_str else None
        
        # Create service and extract messages
        service = SlackExtractService()
        formatted_messages, count = service.extract_messages(messages, start_date, end_date)
        
        # Print summary
        logger.info(f"✅ Successfully extracted {count} messages")
        
        # Save to file if requested
        if output_file:
            service.save_to_file(formatted_messages, output_file)
            logger.info(f"✅ Saved formatted messages to {output_file}")
        else:
            # Print first 5 messages as preview
            preview_count = min(5, len(formatted_messages))
            logger.info(f"Preview of first {preview_count} messages:")
            for i in range(preview_count):
                logger.info(f"---\n{formatted_messages[i]}\n---")
        
        return formatted_messages
    
    except Exception as e:
        logger.exception(f"❌ Error extracting messages: {str(e)}")
        return False


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Debug tool for Slack API interactions")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Check token command
    check_parser = subparsers.add_parser("check", help="Check if the Slack token is valid")
    
    # Download command
    download_parser = subparsers.add_parser("download", help="Download messages for a user")
    download_parser.add_argument("user_id", help="Slack user ID to download messages for")
    download_parser.add_argument("start_date", help="Start date in YYYY-MM-DD format")
    download_parser.add_argument("end_date", help="End date in YYYY-MM-DD format")
    download_parser.add_argument("--output", "-o", help="Output file to save messages to")
    
    # Extract command
    extract_parser = subparsers.add_parser("extract", help="Extract and format messages")
    extract_parser.add_argument("input_file", help="Input file with downloaded messages")
    extract_parser.add_argument("--start-date", help="Optional start date filter in YYYY-MM-DD format")
    extract_parser.add_argument("--end-date", help="Optional end date filter in YYYY-MM-DD format")
    extract_parser.add_argument("--output", "-o", help="Output file to save formatted messages to")
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv(override=True)
    
    # Execute the requested command
    if args.command == "check":
        check_token()
    
    elif args.command == "download":
        download_messages(args.user_id, args.start_date, args.end_date, args.output)
    
    elif args.command == "extract":
        extract_messages(args.input_file, args.start_date, args.end_date, args.output)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
