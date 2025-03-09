## 1. Overview

**Goal**: Transform the existing “script-based” Slack Messages Extractor into a **web application** that:
1. Provides an HTTP API (using **FastAPI**).
2. Is deployable on **Vercel** as a serverless application.

---

## 2. Architectural Approach

### 2.1 High-Level Components

1. **FastAPI Backend**  
   - Exposes endpoints to:
     - Download messages (`/download`)  
     - Extract and filter messages (`/extract`)
   - Incorporates existing Python logic from `download_messages.py` and `extract_messages.py`.
   - Manages interactions with Slack via the Slack API.
   - Offers additional endpoints for health checks, logs retrieval, etc.
   - **Protects endpoints using a strong password** (via environment variable).

2. **Deployment on Vercel**  
   - Single repository containing:
     - `api` folder for **FastAPI**.
   - Vercel’s environment variables store the **Slack Bot Token** and **API Password**.
   - Uses serverless functions or container-based deployment (depending on size and dependencies).

### 2.1 Data Flow

1. **User** inputs user ID, date range, etc., and clicks “Download Messages”.
2. **Frontend** sends a POST request to `/api/download`, **including** the password in the request headers.
3. **FastAPI**:
   - Retrieves Slack Bot Token from environment variables.
   - Calls the Slack API to download messages (existing logic from `download_messages.py`).
   - Returns a success/fail response (including a job ID or direct JSON data).
4. **User** can then trigger “Extract Messages” by calling `/api/extract`.
5. **FastAPI**:
   - Verifies the password from the request headers.
   - Uses the existing logic from `extract_messages.py` to process the JSON data.
   - Returns extracted/filtered messages or a downloadable file.

---

## 3. Detailed Feature Specification

### 3.1 FastAPI Backend

#### 3.1.1 Project Structure

```
slack_extractor/
├── api/
│   ├── main.py               # FastAPI entry point
│   ├── routes/
│   │   ├── download.py       # /download endpoint
│   │   ├── extract.py        # /extract endpoint
│   ├── services/
│   │   ├── slack_download.py # logic from download_messages.py
│   │   ├── slack_extract.py  # logic from extract_messages.py
│   ├── models/               # Pydantic models for request/response
│   ├── utils/                # date parsing, logging, etc.
└── ...
```

- **`main.py`**  
  Creates and configures the FastAPI application. Sets up CORS if needed and includes password verification in the routes.

- **`routes/`**  
  - Each endpoint file implements password-based authentication to ensure only valid requests can call the endpoints.

- **`services/`**  
  - Contains the core logic for Slack API interactions (adapted from `download_messages.py` and `extract_messages.py`).  

- **`models/`**  
  - Pydantic models for request/response data validation.

- **`utils/`**  
  - Utility functions such as date parsing, Slack token scope checks, logging, etc.

#### 3.1.2 Authentication Enforcement

- Use password for API calls.

#### 3.1.3 Endpoints

1. `POST /download`  
   **Purpose**: Download Slack messages for a specified user ID and date range.  
   **Request Body** (JSON):
   ```json
   {
     "user_id": "U123456",
     "start_date": "YYYY-MM-DD",
     "end_date": "YYYY-MM-DD"
   }
   ```
   **Response** (JSON):
   ```json
   {
     "status": "success",
     "message_count": 100,
     "job_id": "uuid-1234"
   }
   ```
   - Returns a `job_id` to correlate subsequent extraction calls.

2. `POST /extract`  
   **Purpose**: Extract and transform previously downloaded messages within a date range.  
   **Request Body** (JSON):
   ```json
   {
     "job_id": "uuid-1234",
     "start_date": "YYYY-MM-DD",
     "end_date": "YYYY-MM-DD"
   }
   ```
   **Response** (JSON):
   ```json
   {
     "status": "success",
     "extracted_message_count": 50,
     "output_file_url": "https://..."
   }
   ```
   - Uses the `job_id` to retrieve the previously downloaded raw JSON, filters messages by date, adds channel metadata, etc.

3. `GET /health`  
   **Purpose**: A simple health check endpoint, returning status code 200 if the service is running.

#### 3.1.4 Environment Variables

1. **`SLACK_BOT_TOKEN`**  
   - Stored as a Vercel **Environment Variable**.  
   - Accessed by the Slack client in `services/slack_download.py` and `services/slack_extract.py`.

2. **`API_PASSWORD`**  
   - For password-based protection of endpoints.

#### 3.1.5 Error Handling & Logging

- Use FastAPI’s built-in exception handling for:
  - Missing token
  - Date parsing errors
  - Rate limit responses from Slack 
- If password verification fails, respond with 401.
- Log important events (start, end, errors, etc.) using Python’s `logging` library or a structured logger.

---

## 4. Deployment on Vercel

### 4.1 Repository Structure

One approach is to keep everything in a single repository:

```
slack_extractor/
├── api/                  # FastAPI code
│   ├── main.py
│   └── ...
├── pyproject.toml        # Poetry config
├── poetry.lock           # Poetry lock file
├── vercel.json           # Vercel configuration
```

- **`vercel.json`** configures:
  - The route rewrites (e.g. `"/api/download"` -> point to the FastAPI serverless function).
  - Build commands for Python (use a serverless Python runtime or Docker).

### 4.2 Environment Variables Configuration

Within Vercel’s project settings, define:

1. **`SLACK_BOT_TOKEN`**  
2. **`API_PASSWORD`**  

### 4.3 Build & Deployment Process

1. **Vercel** detects the presence of `vercel.json`. 
2. It installs dependencies for the Python part (`pyproject.toml` and `poetry.lock`).
3. The **FastAPI** code is packaged into a serverless function or container.  
4. Vercel deploys them under the same domain (e.g. `your-app.vercel.app`).

---

## 5. Summary
- **Backend** verifies the API password before allowing `/download` or `/extract`.
- The new app is a backend-only solution with password protection, ensuring only authorized users can download or extract messages.

---

## 6. Writing and Running Tests with Pytest

### 6.1 Test Structure

Create a `tests/` folder in the project root:

```
slack_extractor/
├── api/
├── tests/
│   ├── __init__.py
│   ├── test_download.py
│   ├── test_extract.py
│   ├── conftest.py       # Common fixtures
```

### 6.2 Sample Test Code

**`tests/conftest.py`**
```python
import pytest
from fastapi.testclient import TestClient
from api.main import app  # Import your FastAPI app

@pytest.fixture
def client():
    return TestClient(app)
```

**`tests/test_download.py`**
```python
import os

def test_download_success(client, monkeypatch):
    # Mock environment variable
    monkeypatch.setenv("API_PASSWORD", "test_password")

    response = client.post(
        "/api/download",
        json={
            "user_id": "U123456",
            "start_date": "2023-01-01",
            "end_date": "2023-01-31"
        },
        headers={"Authorization": "Bearer test_password"}
    )

    assert response.status_code == 200
    assert response.json()["status"] == "success"
```

**`tests/test_extract.py`**
```python
def test_extract_failure(client, monkeypatch):
    monkeypatch.setenv("API_PASSWORD", "test_password")

    response = client.post(
        "/api/extract",
        json={
            "job_id": "invalid_id",
            "start_date": "2023-01-01",
            "end_date": "2023-01-31"
        },
        headers={"Authorization": "Bearer test_password"}
    )

    assert response.status_code == 400  # Example error code
```

### 6.3 Running the Tests

To run tests with `pytest`, execute the following command in the terminal:

```bash
pytest tests/
```

To see detailed output, use:

```bash
pytest -v
```

If you want to run only specific tests:

```bash
pytest tests/test_download.py
```

### 6.4 Additional Recommendations
- Include `pytest` in your `pyproject.toml` dependencies.
- Use `pytest-cov` for code coverage analysis:

```bash
pytest --cov=api tests/
```
