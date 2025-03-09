#!/bin/bash

# Set environment variables (modify as needed)
export SLACK_BOT_TOKEN=${SLACK_BOT_TOKEN:-"xoxb-your-slack-bot-token"}
export API_PASSWORD=${API_PASSWORD:-"test_password"}
export LOG_LEVEL=${LOG_LEVEL:-"INFO"}

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Starting Slack Extractor API Locally ===${NC}"
echo -e "${GREEN}API will be available at: http://localhost:8000${NC}"
echo -e "${GREEN}API Password: $API_PASSWORD${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""

# Run the FastAPI server using uvicorn
cd "$(dirname "$0")/.." && python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
