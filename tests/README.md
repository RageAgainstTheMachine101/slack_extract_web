# Slack Extractor Tests

This directory contains tests for the Slack Extractor web application.

## Test Structure

- **Unit Tests** (`tests/unit/`): Tests individual components in isolation
- **End-to-End Tests** (`tests/e2e/`): Tests the entire application flow
- **Mocks** (`tests/mocks/`): Contains mock data for testing

## Running Tests

### Prerequisites

Make sure you have all development dependencies installed:

```bash
poetry install
```

### Running All Tests

```bash
poetry run pytest
```

### Running Specific Test Categories

```bash
# Run only unit tests
poetry run pytest tests/unit/

# Run only end-to-end tests
poetry run pytest tests/e2e/

# Run tests with coverage report
poetry run pytest --cov=api --cov-report=term-missing
```

### Test Configuration

The test configuration is defined in:
- `pytest.ini` - Main pytest configuration
- `pyproject.toml` - Additional pytest configuration in the `[tool.pytest.ini_options]` section

## Debugging Tools

Debugging tools are available in the `scripts/debugging_tools/` directory:

- `test_slack_api.py`: CLI tool for testing Slack API interactions directly
- `test_api_endpoints.py`: CLI tool for testing the FastAPI endpoints

### Using the Debugging Tools

#### Testing Slack API

```bash
# Check if the Slack token is valid
python scripts/debugging_tools/test_slack_api.py check

# Download messages for a user
python scripts/debugging_tools/test_slack_api.py download U12345 2023-01-01 2023-01-31 --output messages.json

# Extract messages from a downloaded file
python scripts/debugging_tools/test_slack_api.py extract messages.json --start-date 2023-01-15 --output formatted.txt
```

#### Testing API Endpoints

```bash
# Test the health endpoint
python scripts/debugging_tools/test_api_endpoints.py health

# Test the download endpoint
python scripts/debugging_tools/test_api_endpoints.py --password your-api-password download U12345 2023-01-01 2023-01-31

# Run an end-to-end test
python scripts/debugging_tools/test_api_endpoints.py --password your-api-password e2e U12345 2023-01-01 2023-01-31 --output messages.txt
```

## Mock Data

The `tests/mocks/api_mocks.py` file contains mock responses for Slack API testing. These mocks are used in the unit tests to avoid making actual API calls during testing.

## Environment Variables

Tests use environment variables from `.env` file. For testing, you can create a `.env.test` file with test values:

```
SLACK_BOT_TOKEN=xoxb-test-token
API_PASSWORD=test-password
LOG_LEVEL=INFO
```
