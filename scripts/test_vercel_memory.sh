#!/bin/bash

# Configuration - update these values as needed
API_URL="http://localhost:8000"
API_PASSWORD=${API_PASSWORD:-"test_password"}
USER_ID="UNCMCAQ12"
START_DATE="2025-03-07"
END_DATE="2025-03-09"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Testing Slack Extractor API with In-Memory Storage (Vercel Mode) ===${NC}"
echo -e "${YELLOW}Using API URL: ${API_URL}${NC}"
echo -e "${YELLOW}Using User ID: ${USER_ID}${NC}"
echo -e "${YELLOW}Date Range: ${START_DATE} to ${END_DATE}${NC}"
echo ""

# Start the API server with VERCEL environment variable set
echo -e "${YELLOW}Starting API server in Vercel mode...${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop the server when testing is complete${NC}"
echo ""

# Run the server in the background with VERCEL=1
VERCEL=1 python -m api.main &
SERVER_PID=$!

# Give the server time to start
echo -e "${YELLOW}Waiting for server to start...${NC}"
sleep 3

# 1. Health Check
echo -e "${YELLOW}1. Testing Health Check Endpoint...${NC}"
HEALTH_RESPONSE=$(curl -s "${API_URL}/api/health")
echo -e "${GREEN}Health Response:${NC}"
echo $HEALTH_RESPONSE | python -m json.tool
echo ""

# 2. Download Messages
echo -e "${YELLOW}2. Testing Download Endpoint...${NC}"
DOWNLOAD_RESPONSE=$(curl -s -X POST \
  "${API_URL}/api/download" \
  -H "Content-Type: application/json" \
  -H "X-API-Password: ${API_PASSWORD}" \
  -d "{\"user_id\":\"${USER_ID}\",\"start_date\":\"${START_DATE}\",\"end_date\":\"${END_DATE}\"}")

echo -e "${GREEN}Download Response:${NC}"
echo $DOWNLOAD_RESPONSE | python -m json.tool

# Extract job_id from the response
JOB_ID=$(echo $DOWNLOAD_RESPONSE | python -c "import sys, json; print(json.load(sys.stdin).get('job_id', ''))")

if [ -z "$JOB_ID" ]; then
  echo -e "${RED}Failed to get job_id from download response${NC}"
  # Kill the server before exiting
  kill $SERVER_PID
  exit 1
fi

echo -e "${GREEN}Extracted Job ID: ${JOB_ID}${NC}"
echo ""

# 3. Extract Messages
echo -e "${YELLOW}3. Testing Extract Endpoint...${NC}"
EXTRACT_RESPONSE=$(curl -s -X POST \
  "${API_URL}/api/extract" \
  -H "Content-Type: application/json" \
  -H "X-API-Password: ${API_PASSWORD}" \
  -d "{\"job_id\":\"${JOB_ID}\"}")

echo -e "${GREEN}Extract Response:${NC}"
echo $EXTRACT_RESPONSE | python -m json.tool

# Extract file URL if available
FILE_URL=$(echo $EXTRACT_RESPONSE | python -c "import sys, json; print(json.load(sys.stdin).get('output_file_url', ''))")

if [ -n "$FILE_URL" ]; then
  echo -e "${GREEN}File URL: ${FILE_URL}${NC}"
  
  # 4. Download the file
  echo -e "${YELLOW}4. Testing File Download...${NC}"
  FILE_RESPONSE=$(curl -s -I \
    "${API_URL}${FILE_URL}" \
    -H "X-API-Password: ${API_PASSWORD}")
  
  echo -e "${GREEN}File Response Headers:${NC}"
  echo "$FILE_RESPONSE"
  
  # Actually download the file to verify content
  echo -e "${YELLOW}Downloading the file to verify content...${NC}"
  curl -s -o "vercel_test_extracted_messages.txt" \
    "${API_URL}${FILE_URL}" \
    -H "X-API-Password: ${API_PASSWORD}"
  
  echo -e "${GREEN}File downloaded as: vercel_test_extracted_messages.txt${NC}"
  echo -e "${YELLOW}First few lines of the file:${NC}"
  head -n 10 vercel_test_extracted_messages.txt
fi

echo ""
echo -e "${YELLOW}=== Test Complete ===${NC}"

# Kill the server
echo -e "${YELLOW}Stopping the server...${NC}"
kill $SERVER_PID
echo -e "${GREEN}Server stopped${NC}"
