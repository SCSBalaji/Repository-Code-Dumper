# Repository Code Dumper

A web application that clones any public GitHub repository and dumps all file contents into a single downloadable file (Markdown or Plain Text).

## 🚀 Features

- **Simple Interface**: Paste a GitHub URL, select format, click generate
- **Multiple Output Formats**: Markdown (`.md`) or Plain Text (`.txt`)
- **Smart File Processing**: 
  - Skips binary files (images, executables, archives)
  - Excludes common non-essential directories (`node_modules`, `.git`, `venv`)
  - Preserves exact file paths and contents
- **Language Detection**: Automatic syntax highlighting for code blocks in Markdown output
- **Enhanced API Response**: 
  - Structured file index with metadata (language, line count, size, status)
  - Optional content inclusion in API response
  - Request tracking with correlation IDs
- **Security Features**:
  - Optional API key authentication
  - Configurable rate limiting
  - Request tracking and monitoring
- **Production Ready**: 
  - Enhanced health checks with system diagnostics
  - CORS support
  - Error standardization
  - Size limits for protection
- **No Account Required**: Works with any public GitHub repository

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Local Development](#local-development)
- [Docker Deployment](#docker-deployment)
- [API Documentation](#api-documentation)
- [API Usage Guide](#api-usage-guide)
- [Testing](#testing)
- [Configuration](#configuration)
- [Deployment](#deployment)
- [Google Cloud Deployment](#google-cloud-deployment)

## 🏃 Quick Start

### Using Docker (Recommended)

```bash
# Clone this repository
git clone https://github.com/yourusername/Repository-Code-Dumper.git
cd Repository-Code-Dumper

# Start the application
docker-compose up --build

# Access the application
# Frontend: http://localhost
# Backend API: http://localhost:8000
```

### Local Development

See the [Local Development](#local-development) section for detailed instructions.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      User Browser                            │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                  React Frontend                       │    │
│  │  • Repo URL Input                                     │    │
│  │  • Format Selector                                    │    │
│  │  • Download Button                                    │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP POST /process-repo
                              │ GET /download/{filename}
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                           │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                  API Layer                            │    │
│  │  • URL Validation                                     │    │
│  │  • Request/Response Handling                          │    │
│  │  • Error Management                                   │    │
│  └─────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │               Repository Processor                    │    │
│  │  • Git Clone (shallow)                               │    │
│  │  • Filesystem Walk                                    │    │
│  │  • Binary Detection                                   │    │
│  │  • Content Extraction                                 │    │
│  └─────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                Output Formatter                       │    │
│  │  • Markdown Generation                                │    │
│  │  • Plain Text Generation                              │    │
│  │  • Language Detection                                 │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## 💻 Local Development

### Prerequisites

- Python 3.11+
- Node.js 18+
- Git

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create outputs directory
mkdir -p outputs

# Set environment variable
export OUTPUT_DIR=./outputs

# Run the development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start the development server
npm start
```

The frontend will be available at `http://localhost:3000`

> **Note**: The frontend is configured to proxy API requests to `http://localhost:8000` during development.

## 🐳 Docker Deployment

See [DOCKER_SETUP.md](./DOCKER_SETUP.md) for detailed Docker deployment instructions.

### Quick Docker Commands

```bash
# Build and start all services
docker-compose up --build -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Rebuild a specific service
docker-compose up --build backend
```

## 📚 API Documentation

### Endpoints

#### `GET /`
Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "message": "Repository Code Dumper API is running"
}
```

#### `GET /health`
Enhanced health check for monitoring and diagnostics.

**Response:**
```json
{
  "status": "healthy",
  "git_available": true,
  "disk_space_ok": true,
  "output_dir_writable": true,
  "version": "1.0.0",
  "details": {
    "free_space_mb": 15234.56,
    "output_dir": "/app/outputs"
  }
}
```

#### `POST /process-repo`
Process a GitHub repository and generate output file.

**Request Body:**
```json
{
  "repo_url": "https://github.com/owner/repo",
  "format": "markdown",  // or "text"
  "include_content": false  // optional: include full content in response
}
```

**Response:**
```json
{
  "status": "success",
  "repo_url": "https://github.com/owner/repo",
  "download_url": "/download/output_abc12345.md",
  "message": "Successfully processed 42 files",
  "file_count": 42,
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "file_index": [
    {
      "path": "src/main.py",
      "language": "Python",
      "line_count": 150,
      "size_bytes": 4523,
      "status": "processed"
    }
  ],
  "content": null  // only included if include_content=true and file size allows
}
```

**Headers:**
- `X-API-Key`: (Optional) API key for authentication if enabled
- `X-Request-ID`: Request correlation ID (auto-generated if not provided)

**Response Headers:**
- `X-Request-ID`: Request correlation ID
- `X-RateLimit-Limit`: Maximum requests per window
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Window`: Window duration in seconds

**Error Responses:**
- `400`: Invalid URL or repository not accessible
- `401`: Missing or invalid API key (if authentication enabled)
- `403`: Forbidden - invalid API key
- `422`: Invalid request format
- `429`: Rate limit exceeded
- `500`: Internal server error

**Error Response Format:**
```json
{
  "status": "error",
  "error": {
    "error_code": "INVALID_URL",
    "error_type": "validation_error",
    "message": "Invalid GitHub repository URL",
    "details": null,
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

#### `GET /download/{filename}`
Download a generated output file.

**Response:** File download

#### `DELETE /download/{filename}`
Delete a generated output file.

**Response:**
```json
{
  "status": "success",
  "message": "File deleted"
}
```

### Interactive API Documentation

When the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📖 API Usage Guide

For detailed instructions on using the API after deployment, including authentication, rate limiting, and code examples in multiple languages, see [API_USAGE.md](./API_USAGE.md).

## 🧪 Testing

### Running Backend Tests

```bash
cd backend

# Create virtual environment and install dependencies
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_validators.py

# Run with coverage
pytest --cov=app --cov-report=html
```

### Test Structure

```
backend/tests/
├── __init__.py
├── test_validators.py      # URL validation tests
├── test_output_formatter.py # Output formatting tests
├── test_repo_processor.py   # Repository processing tests
└── test_api.py              # API endpoint tests
```

### Test Categories

1. **Unit Tests** (`test_validators.py`, `test_output_formatter.py`, `test_repo_processor.py`)
   - URL validation
   - Binary file detection
   - Output formatting
   - Directory filtering

2. **Integration Tests** (`test_api.py`)
   - API endpoint responses
   - Error handling
   - Request validation

## ⚙️ Configuration

### Environment Variables

#### Basic Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `OUTPUT_DIR` | Directory for generated files | `/app/outputs` |
| `PYTHONUNBUFFERED` | Python output buffering | `1` |
| `REACT_APP_API_URL` | Backend API URL for frontend | (empty for proxy) |

#### Security & Authentication

| Variable | Description | Default |
|----------|-------------|---------|
| `ENABLE_API_AUTH` | Enable API key authentication | `false` |
| `CODE_DUMPER_API_KEY` | API key for authentication | (empty) |

#### Rate Limiting

| Variable | Description | Default |
|----------|-------------|---------|
| `RATE_LIMIT_ENABLED` | Enable rate limiting | `false` |
| `RATE_LIMIT_REQUESTS` | Max requests per window | `100` |
| `RATE_LIMIT_WINDOW` | Window duration in seconds | `60` |

#### Performance & Limits

| Variable | Description | Default |
|----------|-------------|---------|
| `CLONE_TIMEOUT` | Git clone timeout in seconds | `120` |
| `MAX_RESPONSE_SIZE` | Max response size for content inclusion | `52428800` (50MB) |

#### CORS Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `ALLOWED_ORIGINS` | Comma-separated list of allowed origins | `*` |

### Processing Limits

| Limit | Value |
|-------|-------|
| Max Repository Size | 50 MB |
| Max File Size | 10 MB |
| Max File Count | 5,000 files |
| Clone Timeout | 120 seconds |

### Skipped Directories

The following directories are automatically skipped:
- `.git`
- `node_modules`
- `venv`, `.venv`, `env`, `.env`
- `__pycache__`, `.pytest_cache`
- `dist`, `build`
- And more...

### Binary File Extensions

Binary files are detected by:
1. File extension (`.png`, `.jpg`, `.exe`, `.zip`, etc.)
2. Null byte detection in file content

## 🚀 Deployment

See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed deployment instructions including:

- VPS deployment
- Domain/subdomain setup
- SSL/TLS configuration
- Production optimizations

## ☁️ Google Cloud Deployment

For comprehensive Google Cloud Platform deployment instructions with GUI-based setup, subdomain configuration, and resource requirements, see [GCloud_Deploy.md](./GCloud_Deploy.md).

## 📁 Project Structure

```
Repository-Code-Dumper/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI application
│   │   ├── validators.py         # URL validation
│   │   ├── repo_processor.py     # Repository processing
│   │   └── output_formatter.py   # Output formatting
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_validators.py
│   │   ├── test_output_formatter.py
│   │   ├── test_repo_processor.py
│   │   └── test_api.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── pytest.ini
├── frontend/
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── components/
│   │   │   ├── RepoInput.js
│   │   │   ├── FormatSelector.js
│   │   │   └── DownloadButton.js
│   │   ├── App.js
│   │   ├── index.js
│   │   └── index.css
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
├── docker-compose.yml
├── README.md
├── DOCKER_SETUP.md
├── DEPLOYMENT.md
└── .gitignore
```

## 🔒 Security Considerations

- Only public GitHub repositories are supported
- URL validation prevents non-GitHub URLs
- Directory traversal protection on download endpoint
- Size limits prevent resource exhaustion
- Temporary files are cleaned up after processing

## 📝 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request
