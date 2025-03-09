#!/bin/bash
# Test script for the new content API endpoint
# This demonstrates how a Slack bot can access file content without downloading

# Load environment variables from .env if it exists
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

# Set variables
API_URL="http://localhost:8000/api"
API_PASSWORD=${API_PASSWORD:-"test_password"}
USER_ID="UNCMCAQ12"
START_DATE="2025-03-07"
END_DATE="2025-03-09"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Testing Content API Endpoint ===${NC}"
echo -e "${YELLOW}Using API URL: ${API_URL}${NC}"
echo -e "${YELLOW}Using User ID: ${USER_ID}${NC}"
echo -e "${YELLOW}Date Range: ${START_DATE} to ${END_DATE}${NC}"
echo ""

# Step 1: Download messages (this would be done by your main app)
echo -e "${YELLOW}Step 1: Downloading messages...${NC}"
DOWNLOAD_RESPONSE=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -H "X-API-Password: $API_PASSWORD" \
  -d "{\"user_id\": \"$USER_ID\", \"start_date\": \"$START_DATE\", \"end_date\": \"$END_DATE\"}" \
  $API_URL/download)

echo -e "${GREEN}Download Response:${NC}"
echo "$DOWNLOAD_RESPONSE" | python -c "import sys, json; print(json.dumps(json.loads(sys.stdin.read()), indent=4, ensure_ascii=False))"
echo ""

# Extract job_id from the response
JOB_ID=$(echo "$DOWNLOAD_RESPONSE" | python -c "import sys, json; print(json.load(sys.stdin).get('job_id', ''))")

if [ -z "$JOB_ID" ]; then
  echo -e "${RED}Failed to get job_id from download response${NC}"
  exit 1
fi

echo -e "${GREEN}Extracted Job ID: ${JOB_ID}${NC}"
echo ""

# Step 2: Extract messages
echo -e "${YELLOW}Step 2: Extracting messages...${NC}"
EXTRACT_RESPONSE=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -H "X-API-Password: $API_PASSWORD" \
  -d "{\"job_id\": \"$JOB_ID\"}" \
  $API_URL/extract)

echo -e "${GREEN}Extract Response:${NC}"
echo "$EXTRACT_RESPONSE" | python -c "import sys, json; print(json.dumps(json.loads(sys.stdin.read()), indent=4, ensure_ascii=False))"
echo ""

# Extract content URL from the response
CONTENT_URL=$(echo "$EXTRACT_RESPONSE" | python -c "import sys, json; print(json.load(sys.stdin).get('output_content_url', ''))")

if [ -z "$CONTENT_URL" ]; then
  echo -e "${RED}Failed to get content_url from extract response${NC}"
  exit 1
fi

echo -e "${GREEN}Content URL: ${CONTENT_URL}${NC}"
echo ""

# Step 3: Access the content via the new API endpoint (this is what your Slack bot would do)
echo -e "${YELLOW}Step 3: Accessing content via API (as a Slack bot would)...${NC}"
# Fix the URL path - remove the duplicate /api prefix
FULL_URL=$(echo "$API_URL$CONTENT_URL" | sed 's|/api/api/|/api/|')
echo -e "${GREEN}Requesting URL: ${FULL_URL}${NC}"

CONTENT_RESPONSE=$(curl -s \
  -H "X-API-Password: $API_PASSWORD" \
  $FULL_URL)

# Display the response (this is the JSON data your Slack bot would receive)
echo -e "${GREEN}Content Response (JSON):${NC}"
echo "$CONTENT_RESPONSE" | python -c "import sys, json; print(json.dumps(json.loads(sys.stdin.read()), indent=4, ensure_ascii=False))"

echo -e "\n${YELLOW}Your Slack bot can now parse this JSON response and use the content without downloading a file!${NC}"
