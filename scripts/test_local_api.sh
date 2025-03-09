#!/bin/bash

# Load environment variables from .env if it exists
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

# Configuration - update these values as needed
API_URL="https://slack-extract-ibivi3p6p-rageagainstthemachine101s-projects.vercel.app"
API_PASSWORD=${API_PASSWORD:-"test_password"}
USER_ID="UNCMCAQ12"
START_DATE="2025-03-07"
END_DATE="2025-03-09"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Testing Local Slack Extractor API ===${NC}"
echo -e "${YELLOW}Using API URL: ${API_URL}${NC}"
echo -e "${YELLOW}Using User ID: ${USER_ID}${NC}"
echo -e "${YELLOW}Date Range: ${START_DATE} to ${END_DATE}${NC}"
echo ""

# Set curl options based on debug mode
CURL_OPTS="-s"

# 1. Health Check
echo -e "${YELLOW}1. Testing Health Check Endpoint...${NC}"
HEALTH_RESPONSE=$(curl $CURL_OPTS "${API_URL}/api/health" \
  -H "Accept: application/json" \
  -H "x-vercel-protection-bypass: ${VERCEL_AUTOMATION_BYPASS_SECRET}")

echo -e "${GREEN}Health Response:${NC}"
echo "$HEALTH_RESPONSE"
echo ""

# Check if the response is HTML
if [[ "$HEALTH_RESPONSE" == *"<!DOCTYPE html>"* || "$HEALTH_RESPONSE" == *"<html"* ]]; then
  echo -e "${RED}Received HTML response instead of JSON. Vercel protection bypass might not be working.${NC}"
  exit 1
fi

# 2. Download Messages
echo -e "${YELLOW}2. Testing Download Endpoint...${NC}"
DOWNLOAD_RESPONSE=$(curl $CURL_OPTS -X POST \
  "${API_URL}/api/download" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "X-API-Password: ${API_PASSWORD}" \
  -H "x-vercel-protection-bypass: ${VERCEL_AUTOMATION_BYPASS_SECRET}" \
  -d "{\"user_id\":\"${USER_ID}\",\"start_date\":\"${START_DATE}\",\"end_date\":\"${END_DATE}\"}")

echo -e "${GREEN}Download Response (Raw):${NC}"
echo "$DOWNLOAD_RESPONSE"
echo ""

# Check if the response is HTML
if [[ "$DOWNLOAD_RESPONSE" == *"<!DOCTYPE html>"* || "$DOWNLOAD_RESPONSE" == *"<html"* ]]; then
  echo -e "${RED}Received HTML response instead of JSON. Vercel protection bypass might not be working.${NC}"
  exit 1
fi

# Extract job_id from the response
echo -e "${GREEN}Attempting to parse JSON response...${NC}"
JOB_ID=$(echo "$DOWNLOAD_RESPONSE" | python -c "import sys, json; print(json.load(sys.stdin).get('job_id', ''))")

if [ -z "$JOB_ID" ]; then
  echo -e "${RED}Failed to get job_id from download response${NC}"
  exit 1
fi

echo -e "${GREEN}Extracted Job ID: ${JOB_ID}${NC}"
echo ""

# 3. Extract Messages
echo -e "${YELLOW}3. Testing Extract Endpoint...${NC}"
EXTRACT_RESPONSE=$(curl $CURL_OPTS -X POST \
  "${API_URL}/api/extract" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "X-API-Password: ${API_PASSWORD}" \
  -H "x-vercel-protection-bypass: ${VERCEL_AUTOMATION_BYPASS_SECRET}" \
  -d "{\"job_id\":\"${JOB_ID}\"}")

echo -e "${GREEN}Extract Response (Raw):${NC}"
echo "$EXTRACT_RESPONSE"
echo ""

# Check if the response is HTML
if [[ "$EXTRACT_RESPONSE" == *"<!DOCTYPE html>"* || "$EXTRACT_RESPONSE" == *"<html"* ]]; then
  echo -e "${RED}Received HTML response instead of JSON. Vercel protection bypass might not be working.${NC}"
  exit 1
fi

echo -e "${GREEN}Extract Response (Formatted):${NC}"
echo "$EXTRACT_RESPONSE" | python -m json.tool

# Extract file URL if available
FILE_URL=$(echo "$EXTRACT_RESPONSE" | python -c "import sys, json; print(json.load(sys.stdin).get('output_file_url', ''))")

if [ -n "$FILE_URL" ]; then
  echo -e "${GREEN}File URL: ${FILE_URL}${NC}"
  
  # 4. Download the file
  echo -e "${YELLOW}4. Testing File Download...${NC}"
  FILE_RESPONSE=$(curl $CURL_OPTS -I \
    "${API_URL}${FILE_URL}" \
    -H "Accept: application/json" \
    -H "X-API-Password: ${API_PASSWORD}" \
    -H "x-vercel-protection-bypass: ${VERCEL_AUTOMATION_BYPASS_SECRET}")
  
  echo -e "${GREEN}File Response Headers:${NC}"
  echo "$FILE_RESPONSE"
  
  echo -e "${YELLOW}To download the file, run:${NC}"
  echo -e "curl -o extracted_messages.json \"${API_URL}${FILE_URL}\" -H \"X-API-Password: ${API_PASSWORD}\" -H \"Accept: application/json\" -H \"x-vercel-protection-bypass: ${VERCEL_AUTOMATION_BYPASS_SECRET}\""
fi

echo ""
echo -e "${YELLOW}=== Test Complete ===${NC}"
