#!/usr/bin/env python
"""
Debugging tool for testing the FastAPI endpoints directly.
This script allows you to test the API endpoints without going through a web browser.
"""
import os
import sys
import json
import logging
import argparse
import requests
from datetime import date
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def test_health(base_url):
    """Test the health endpoint."""
    url = f"{base_url}/api/health"
    logger.info(f"Testing health endpoint: {url}")
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        logger.info(f"✅ Health check successful: {response.json()}")
        return True
    except Exception as e:
        logger.error(f"❌ Health check failed: {str(e)}")
        return False


def test_download(base_url, user_id, start_date, end_date, password):
    """Test the download endpoint."""
    url = f"{base_url}/api/download"
    logger.info(f"Testing download endpoint: {url}")
    
    headers = {"X-API-Password": password}
    payload = {
        "user_id": user_id,
        "start_date": start_date,
        "end_date": end_date
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        result = response.json()
        logger.info(f"✅ Download successful: {result}")
        return result.get("job_id")
    except requests.exceptions.HTTPError as e:
        logger.error(f"❌ Download failed with status {e.response.status_code}: {e.response.text}")
        return None
    except Exception as e:
        logger.error(f"❌ Download failed: {str(e)}")
        return None


def test_extract(base_url, job_id, start_date, end_date, password):
    """Test the extract endpoint."""
    url = f"{base_url}/api/extract"
    logger.info(f"Testing extract endpoint: {url}")
    
    headers = {"X-API-Password": password}
    payload = {
        "job_id": job_id,
        "start_date": start_date,
        "end_date": end_date
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        result = response.json()
        logger.info(f"✅ Extract successful: {result}")
        return result.get("output_file_url")
    except requests.exceptions.HTTPError as e:
        logger.error(f"❌ Extract failed with status {e.response.status_code}: {e.response.text}")
        return None
    except Exception as e:
        logger.error(f"❌ Extract failed: {str(e)}")
        return None


def test_file_download(base_url, file_url, password, output_file=None):
    """Test downloading a file from the files endpoint."""
    url = f"{base_url}{file_url}"
    logger.info(f"Testing file download: {url}")
    
    headers = {"X-API-Password": password}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Save to file if requested
        if output_file:
            with open(output_file, 'wb') as f:
                f.write(response.content)
            logger.info(f"✅ File downloaded and saved to {output_file}")
        else:
            # Print preview of content
            content = response.text
            preview = content[:500] + "..." if len(content) > 500 else content
            logger.info(f"✅ File downloaded. Preview:\n{preview}")
        
        return True
    except requests.exceptions.HTTPError as e:
        logger.error(f"❌ File download failed with status {e.response.status_code}: {e.response.text}")
        return False
    except Exception as e:
        logger.error(f"❌ File download failed: {str(e)}")
        return False


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Debug tool for testing FastAPI endpoints")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL of the API")
    parser.add_argument("--password", help="API password for authentication")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Health check command
    health_parser = subparsers.add_parser("health", help="Test the health endpoint")
    
    # Download command
    download_parser = subparsers.add_parser("download", help="Test the download endpoint")
    download_parser.add_argument("user_id", help="Slack user ID to download messages for")
    download_parser.add_argument("start_date", help="Start date in YYYY-MM-DD format")
    download_parser.add_argument("end_date", help="End date in YYYY-MM-DD format")
    
    # Extract command
    extract_parser = subparsers.add_parser("extract", help="Test the extract endpoint")
    extract_parser.add_argument("job_id", help="Job ID from a previous download")
    extract_parser.add_argument("--start-date", help="Optional start date filter in YYYY-MM-DD format")
    extract_parser.add_argument("--end-date", help="Optional end date filter in YYYY-MM-DD format")
    
    # File download command
    file_parser = subparsers.add_parser("file", help="Test downloading a file")
    file_parser.add_argument("file_url", help="File URL from extract response")
    file_parser.add_argument("--output", "-o", help="Output file to save downloaded content to")
    
    # End-to-end test command
    e2e_parser = subparsers.add_parser("e2e", help="Run an end-to-end test")
    e2e_parser.add_argument("user_id", help="Slack user ID to download messages for")
    e2e_parser.add_argument("start_date", help="Start date in YYYY-MM-DD format")
    e2e_parser.add_argument("end_date", help="End date in YYYY-MM-DD format")
    e2e_parser.add_argument("--output", "-o", help="Output file to save downloaded content to")
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv(override=True)
    
    # Get password from args or environment
    password = args.password or os.getenv("API_PASSWORD")
    if not password and args.command not in ["health"]:
        logger.error("❌ API password is required. Provide it with --password or set API_PASSWORD environment variable.")
        return
    
    # Execute the requested command
    if args.command == "health":
        test_health(args.url)
    
    elif args.command == "download":
        test_download(args.url, args.user_id, args.start_date, args.end_date, password)
    
    elif args.command == "extract":
        test_extract(args.url, args.job_id, args.start_date, args.end_date, password)
    
    elif args.command == "file":
        test_file_download(args.url, args.file_url, password, args.output)
    
    elif args.command == "e2e":
        # Run an end-to-end test: download -> extract -> get file
        logger.info("Running end-to-end test")
        
        # Step 1: Download
        job_id = test_download(args.url, args.user_id, args.start_date, args.end_date, password)
        if not job_id:
            logger.error("❌ End-to-end test failed at download step")
            return
        
        # Step 2: Extract
        file_url = test_extract(args.url, job_id, args.start_date, args.end_date, password)
        if not file_url:
            logger.error("❌ End-to-end test failed at extract step")
            return
        
        # Step 3: Download file
        success = test_file_download(args.url, file_url, password, args.output)
        if success:
            logger.info("✅ End-to-end test completed successfully")
        else:
            logger.error("❌ End-to-end test failed at file download step")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
