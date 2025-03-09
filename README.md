# Slack Extractor Web App

A web application for downloading and extracting Slack messages, built with FastAPI.

## Features

- **Download Messages**: Retrieve messages for a specific Slack user within a date range
- **Extract Messages**: Process and format downloaded messages

## Tech Stack

- **Backend**: FastAPI
- **Package Manager**: Poetry
- **Deployment**: Vercel

## Project Structure

```
slack_extractor_web/
├── api/                      # FastAPI backend
│   ├── models/               # Pydantic data models
│   ├── routes/               # API endpoints
│   ├── services/             # Business logic
│   └── utils/                # Helper functions
├── extracts/                 # Storage for extracted messages
├── pyproject.toml            # Poetry configuration
└── vercel.json               # Vercel deployment configuration
```

## Setup and Installation

### Prerequisites

- Python 3.8+
- Poetry
- Slack Bot Token with appropriate scopes

### Local Development

1. Clone the repository:
   ```
   git clone <repository-url>
   cd slack_extractor_web
   ```

2. Install dependencies:
   ```
   poetry install
   ```

3. Create a `.env` file with the following variables:
   ```
   SLACK_BOT_TOKEN=your_slack_bot_token
   LOG_LEVEL=INFO  # Optional
   ```

4. Run the development server:
   ```
   poetry run uvicorn api.main:app --reload
   ```

5. Access the application at `http://localhost:8000`

### Deployment to Vercel

1. Make sure you have the Vercel CLI installed:
   ```
   npm install -g vercel
   ```

2. Deploy to Vercel:
   ```
   vercel
   ```

3. Set up the environment variables in the Vercel dashboard.

## Usage

1. **Sign In**: Use the "Sign In" button to authenticate with Supabase
2. **Download Messages**:
   - Enter a Slack User ID
   - Select start and end dates
   - Click "Download Messages"
3. **Extract Messages**:
   - The Job ID will be auto-filled from the previous step
   - Optionally specify a date range filter
   - Click "Extract Messages"
4. **View Results**:
   - See a preview of extracted messages
   - Download the full extraction as a text file

## API Endpoints

- `POST /api/download`: Download messages for a user within a date range
- `POST /api/extract`: Extract and format previously downloaded messages
- `GET /api/files/{file_id}`: Download an extracted file
- `GET /api/health`: Check if the service is running

## Authentication

The application uses Supabase Authentication:
- JWT tokens are used to secure API endpoints
- Frontend stores the session token and includes it in API requests
- Backend validates tokens before processing requests

## License

[MIT License](LICENSE)
