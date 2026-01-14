# API Usage Guide

Complete guide for using the Repository Code Dumper API after deployment. This guide covers authentication, endpoints, rate limiting, error handling, and provides code examples in multiple languages.

## 📋 Table of Contents

- [Base URL](#base-url)
- [Authentication](#authentication)
- [Rate Limiting](#rate-limiting)
- [API Endpoints](#api-endpoints)
- [Request & Response Format](#request--response-format)
- [Error Handling](#error-handling)
- [Code Examples](#code-examples)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Base URL

Replace `YOUR_DOMAIN` with your actual deployed domain:

```
https://YOUR_DOMAIN
```

Examples:
- `https://dump.yourdomain.com`
- `https://repo-dumper.example.com`
- `http://localhost:8000` (for local development)

## Authentication

### API Key Authentication

If API authentication is enabled on your deployment, you must include an API key in your requests.

#### Headers

```
X-API-Key: YOUR_API_KEY
```

#### Checking if Authentication is Required

Send a request to the root endpoint:

```bash
curl https://YOUR_DOMAIN/
```

**If authentication is required**, you'll receive a 401 response:
```json
{
  "status": "error",
  "error": {
    "error_code": "MISSING_API_KEY",
    "error_type": "authentication_error",
    "message": "API key is required. Provide it in the X-API-Key header.",
    "request_id": "..."
  }
}
```

**If authentication is NOT required**, you'll receive a 200 response:
```json
{
  "status": "ok",
  "message": "Repository Code Dumper API is running"
}
```

#### Obtaining an API Key

Contact your deployment administrator to obtain an API key. The key is configured via the `CODE_DUMPER_API_KEY` environment variable during deployment.

## Rate Limiting

### Default Limits

If rate limiting is enabled:
- **Requests**: 100 requests per window
- **Window**: 60 seconds

These values may vary based on your deployment configuration.

### Rate Limit Headers

Every response includes rate limit information in the headers:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Window: 60
```

- `X-RateLimit-Limit`: Maximum requests allowed per window
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Window`: Window duration in seconds

### Rate Limit Exceeded

When you exceed the rate limit, you'll receive a 429 response:

```json
{
  "status": "error",
  "error": {
    "error_code": "RATE_LIMIT_EXCEEDED",
    "error_type": "rate_limit_error",
    "message": "Rate limit exceeded. Maximum 100 requests per 60 seconds.",
    "request_id": "..."
  }
}
```

**What to do:**
- Wait for the current window to expire (check `X-RateLimit-Window` header)
- Implement exponential backoff in your application
- Optimize your request frequency

## API Endpoints

### 1. Root Endpoint

Health check and API status.

**Endpoint:** `GET /`

**Response:**
```json
{
  "status": "ok",
  "message": "Repository Code Dumper API is running"
}
```

**Example:**
```bash
curl https://YOUR_DOMAIN/
```

---

### 2. Enhanced Health Check

Detailed health information including system diagnostics.

**Endpoint:** `GET /health`

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

**Response Fields:**
- `status`: Overall health status (`healthy` or `unhealthy`)
- `git_available`: Whether git command is available
- `disk_space_ok`: Whether sufficient disk space is available (>100MB)
- `output_dir_writable`: Whether output directory is writable
- `version`: API version
- `details`: Additional diagnostic information

**Example:**
```bash
curl https://YOUR_DOMAIN/health
```

---

### 3. Process Repository

Process a GitHub repository and generate a code dump file.

**Endpoint:** `POST /process-repo`

**Request Headers:**
```
Content-Type: application/json
X-API-Key: YOUR_API_KEY (if authentication is enabled)
X-Request-ID: optional-correlation-id (optional)
```

**Request Body:**
```json
{
  "repo_url": "https://github.com/owner/repository",
  "format": "markdown",
  "include_content": false
}
```

**Request Fields:**
- `repo_url` (required): Full GitHub repository URL
- `format` (optional): Output format - `"markdown"` or `"text"` (default: `"markdown"`)
- `include_content` (optional): Include full dump content in response body (default: `false`)

**Response:**
```json
{
  "status": "success",
  "repo_url": "https://github.com/owner/repository",
  "download_url": "/download/output_abc123.md",
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
    },
    {
      "path": "README.md",
      "language": "Markdown",
      "line_count": 85,
      "size_bytes": 3241,
      "status": "processed"
    }
  ],
  "content": null
}
```

**Response Fields:**
- `status`: Processing status (`"success"`)
- `repo_url`: The repository URL that was processed
- `download_url`: Relative URL to download the generated file
- `message`: Human-readable status message
- `file_count`: Total number of files processed
- `request_id`: Request tracking identifier
- `file_index`: Array of file metadata objects
  - `path`: Relative file path from repository root
  - `language`: Detected programming language
  - `line_count`: Number of lines in the file
  - `size_bytes`: File size in bytes
  - `status`: Processing status (`"processed"`, `"binary"`, or `"error"`)
- `content`: Full dump content (only present if `include_content: true` and file size allows)

**Example:**
```bash
curl -X POST https://YOUR_DOMAIN/process-repo \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "repo_url": "https://github.com/octocat/Hello-World",
    "format": "markdown",
    "include_content": false
  }'
```

---

### 4. Download File

Download a generated output file.

**Endpoint:** `GET /download/{filename}`

**Parameters:**
- `filename`: Name of the file to download (obtained from `process-repo` response)

**Response:** File download with appropriate content type

**Example:**
```bash
# Download file
curl -O https://YOUR_DOMAIN/download/output_abc123.md

# Download with API key (if required)
curl -H "X-API-Key: YOUR_API_KEY" \
  -O https://YOUR_DOMAIN/download/output_abc123.md
```

---

### 5. Delete File

Delete a generated output file.

**Endpoint:** `DELETE /download/{filename}`

**Parameters:**
- `filename`: Name of the file to delete

**Response:**
```json
{
  "status": "success",
  "message": "File deleted",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Example:**
```bash
curl -X DELETE https://YOUR_DOMAIN/download/output_abc123.md \
  -H "X-API-Key: YOUR_API_KEY"
```

## Request & Response Format

### Request ID Tracking

Every request can include a correlation ID for tracking:

**Request Header:**
```
X-Request-ID: your-correlation-id
```

If not provided, the API will generate one automatically.

**Response Header:**
```
X-Request-ID: 550e8400-e29b-41d4-a716-446655440000
```

Use this ID for debugging and support requests.

### Content Type

All requests with a body must include:
```
Content-Type: application/json
```

### Response Format

All responses are in JSON format with the following structure:

**Success Response:**
```json
{
  "status": "success",
  // ... additional fields
}
```

**Error Response:**
```json
{
  "status": "error",
  "error": {
    "error_code": "ERROR_CODE",
    "error_type": "error_category",
    "message": "Human-readable error message",
    "details": {},
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

## Error Handling

### HTTP Status Codes

| Status Code | Meaning |
|------------|---------|
| 200 | Success |
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Missing API key |
| 403 | Forbidden - Invalid API key |
| 404 | Not Found - Resource doesn't exist |
| 422 | Validation Error - Invalid request format |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |

### Error Types

| Error Code | Error Type | Description | HTTP Status |
|-----------|-----------|-------------|------------|
| `INVALID_URL` | `validation_error` | Invalid GitHub repository URL | 400 |
| `PROCESSING_ERROR` | `processing_error` | Error processing repository | 400 |
| `MISSING_API_KEY` | `authentication_error` | API key not provided | 401 |
| `INVALID_API_KEY` | `authentication_error` | Invalid API key | 403 |
| `FILE_NOT_FOUND` | `not_found_error` | File doesn't exist | 404 |
| `INVALID_FILENAME` | `validation_error` | Invalid filename | 400 |
| `VALIDATION_ERROR` | `validation_error` | Request validation failed | 422 |
| `RATE_LIMIT_EXCEEDED` | `rate_limit_error` | Too many requests | 429 |
| `INTERNAL_ERROR` | `server_error` | Internal server error | 500 |

### Error Response Example

```json
{
  "status": "error",
  "error": {
    "error_code": "INVALID_URL",
    "error_type": "validation_error",
    "message": "Invalid GitHub repository URL. Please provide a valid GitHub repository URL.",
    "details": null,
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

## Code Examples

### Python

```python
import requests
import json

# Configuration
BASE_URL = "https://YOUR_DOMAIN"
API_KEY = "YOUR_API_KEY"  # Optional, if authentication is enabled

# Headers
headers = {
    "Content-Type": "application/json",
}

# Add API key if authentication is enabled
if API_KEY:
    headers["X-API-Key"] = API_KEY

def process_repository(repo_url, output_format="markdown", include_content=False):
    """Process a GitHub repository."""
    endpoint = f"{BASE_URL}/process-repo"
    
    payload = {
        "repo_url": repo_url,
        "format": output_format,
        "include_content": include_content
    }
    
    try:
        response = requests.post(endpoint, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        return None

def download_file(filename, output_path):
    """Download a generated file."""
    endpoint = f"{BASE_URL}/download/{filename}"
    
    try:
        response = requests.get(endpoint, headers=headers, stream=True)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"Downloaded to {output_path}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return False

# Example usage
if __name__ == "__main__":
    # Process repository
    result = process_repository("https://github.com/octocat/Hello-World")
    
    if result and result.get("status") == "success":
        print(f"Processed {result['file_count']} files")
        print(f"Download URL: {result['download_url']}")
        
        # Extract filename from download_url
        filename = result['download_url'].split('/')[-1]
        
        # Download the file
        download_file(filename, f"output/{filename}")
    else:
        print("Processing failed")
```

### JavaScript (Node.js)

```javascript
const axios = require('axios');
const fs = require('fs');
const path = require('path');

// Configuration
const BASE_URL = 'https://YOUR_DOMAIN';
const API_KEY = 'YOUR_API_KEY'; // Optional, if authentication is enabled

// Create axios instance with default config
const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    ...(API_KEY && { 'X-API-Key': API_KEY })
  }
});

async function processRepository(repoUrl, format = 'markdown', includeContent = false) {
  try {
    const response = await api.post('/process-repo', {
      repo_url: repoUrl,
      format: format,
      include_content: includeContent
    });
    
    return response.data;
  } catch (error) {
    console.error('Error:', error.message);
    if (error.response) {
      console.error('Response:', error.response.data);
    }
    return null;
  }
}

async function downloadFile(filename, outputPath) {
  try {
    const response = await api.get(`/download/${filename}`, {
      responseType: 'stream'
    });
    
    const writer = fs.createWriteStream(outputPath);
    response.data.pipe(writer);
    
    return new Promise((resolve, reject) => {
      writer.on('finish', () => {
        console.log(`Downloaded to ${outputPath}`);
        resolve(true);
      });
      writer.on('error', reject);
    });
  } catch (error) {
    console.error('Error:', error.message);
    return false;
  }
}

// Example usage
async function main() {
  // Process repository
  const result = await processRepository('https://github.com/octocat/Hello-World');
  
  if (result && result.status === 'success') {
    console.log(`Processed ${result.file_count} files`);
    console.log(`Download URL: ${result.download_url}`);
    
    // Extract filename from download_url
    const filename = result.download_url.split('/').pop();
    
    // Download the file
    await downloadFile(filename, `output/${filename}`);
  } else {
    console.log('Processing failed');
  }
}

main();
```

### cURL

```bash
#!/bin/bash

# Configuration
BASE_URL="https://YOUR_DOMAIN"
API_KEY="YOUR_API_KEY"  # Optional, if authentication is enabled

# Process repository
echo "Processing repository..."
RESPONSE=$(curl -s -X POST "$BASE_URL/process-repo" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "repo_url": "https://github.com/octocat/Hello-World",
    "format": "markdown",
    "include_content": false
  }')

echo "Response: $RESPONSE"

# Extract download URL using jq
DOWNLOAD_URL=$(echo "$RESPONSE" | jq -r '.download_url')

if [ "$DOWNLOAD_URL" != "null" ]; then
  echo "Download URL: $DOWNLOAD_URL"
  
  # Extract filename
  FILENAME=$(basename "$DOWNLOAD_URL")
  
  # Download file
  echo "Downloading file..."
  curl -H "X-API-Key: $API_KEY" \
    -o "output/$FILENAME" \
    "$BASE_URL$DOWNLOAD_URL"
  
  echo "Downloaded to output/$FILENAME"
else
  echo "Processing failed"
fi
```

### Go

```go
package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"path"
)

const (
	baseURL = "https://YOUR_DOMAIN"
	apiKey  = "YOUR_API_KEY" // Optional, if authentication is enabled
)

type ProcessRequest struct {
	RepoURL        string `json:"repo_url"`
	Format         string `json:"format"`
	IncludeContent bool   `json:"include_content"`
}

type ProcessResponse struct {
	Status      string `json:"status"`
	RepoURL     string `json:"repo_url"`
	DownloadURL string `json:"download_url"`
	Message     string `json:"message"`
	FileCount   int    `json:"file_count"`
	RequestID   string `json:"request_id"`
}

func processRepository(repoURL, format string, includeContent bool) (*ProcessResponse, error) {
	reqBody := ProcessRequest{
		RepoURL:        repoURL,
		Format:         format,
		IncludeContent: includeContent,
	}

	jsonData, err := json.Marshal(reqBody)
	if err != nil {
		return nil, err
	}

	req, err := http.NewRequest("POST", baseURL+"/process-repo", bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, err
	}

	req.Header.Set("Content-Type", "application/json")
	if apiKey != "" {
		req.Header.Set("X-API-Key", apiKey)
	}

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("API error: %s", string(body))
	}

	var result ProcessResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}

	return &result, nil
}

func downloadFile(filename, outputPath string) error {
	req, err := http.NewRequest("GET", baseURL+"/download/"+filename, nil)
	if err != nil {
		return err
	}

	if apiKey != "" {
		req.Header.Set("X-API-Key", apiKey)
	}

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("download failed with status: %d", resp.StatusCode)
	}

	out, err := os.Create(outputPath)
	if err != nil {
		return err
	}
	defer out.Close()

	_, err = io.Copy(out, resp.Body)
	return err
}

func main() {
	// Process repository
	result, err := processRepository("https://github.com/octocat/Hello-World", "markdown", false)
	if err != nil {
		fmt.Printf("Error: %v\n", err)
		return
	}

	fmt.Printf("Processed %d files\n", result.FileCount)
	fmt.Printf("Download URL: %s\n", result.DownloadURL)

	// Extract filename
	filename := path.Base(result.DownloadURL)

	// Download file
	outputPath := "output/" + filename
	if err := downloadFile(filename, outputPath); err != nil {
		fmt.Printf("Download error: %v\n", err)
		return
	}

	fmt.Printf("Downloaded to %s\n", outputPath)
}
```

### PHP

```php
<?php

// Configuration
$baseUrl = 'https://YOUR_DOMAIN';
$apiKey = 'YOUR_API_KEY'; // Optional, if authentication is enabled

function processRepository($repoUrl, $format = 'markdown', $includeContent = false) {
    global $baseUrl, $apiKey;
    
    $endpoint = $baseUrl . '/process-repo';
    
    $data = [
        'repo_url' => $repoUrl,
        'format' => $format,
        'include_content' => $includeContent
    ];
    
    $options = [
        'http' => [
            'header' => [
                "Content-Type: application/json",
                $apiKey ? "X-API-Key: $apiKey" : ""
            ],
            'method' => 'POST',
            'content' => json_encode($data)
        ]
    ];
    
    $context = stream_context_create($options);
    $response = file_get_contents($endpoint, false, $context);
    
    if ($response === false) {
        return null;
    }
    
    return json_decode($response, true);
}

function downloadFile($filename, $outputPath) {
    global $baseUrl, $apiKey;
    
    $endpoint = $baseUrl . '/download/' . $filename;
    
    $options = [
        'http' => [
            'header' => $apiKey ? "X-API-Key: $apiKey" : ""
        ]
    ];
    
    $context = stream_context_create($options);
    $content = file_get_contents($endpoint, false, $context);
    
    if ($content === false) {
        return false;
    }
    
    return file_put_contents($outputPath, $content);
}

// Example usage
$result = processRepository('https://github.com/octocat/Hello-World');

if ($result && $result['status'] === 'success') {
    echo "Processed {$result['file_count']} files\n";
    echo "Download URL: {$result['download_url']}\n";
    
    // Extract filename
    $filename = basename($result['download_url']);
    
    // Download file
    if (downloadFile($filename, "output/$filename")) {
        echo "Downloaded to output/$filename\n";
    } else {
        echo "Download failed\n";
    }
} else {
    echo "Processing failed\n";
}
```

## Best Practices

### 1. Handle Errors Gracefully

Always check response status and handle errors:

```python
response = requests.post(url, json=data)
if response.status_code == 200:
    result = response.json()
    if result['status'] == 'success':
        # Process success
        pass
else:
    # Handle error
    error_data = response.json()
    print(f"Error: {error_data['error']['message']}")
```

### 2. Respect Rate Limits

Monitor rate limit headers and implement backoff:

```python
def check_rate_limit(response):
    remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
    if remaining < 10:
        print("Warning: Approaching rate limit")
        time.sleep(5)  # Slow down requests
```

### 3. Use Request IDs for Tracking

Include request IDs for debugging:

```python
import uuid

headers = {
    'X-Request-ID': str(uuid.uuid4()),
    'X-API-Key': API_KEY
}

response = requests.post(url, headers=headers, json=data)
request_id = response.headers.get('X-Request-ID')
print(f"Request ID: {request_id}")
```

### 4. Implement Retry Logic

Add retry logic for transient failures:

```python
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

session = requests.Session()
retry = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504]
)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)
```

### 5. Validate Repository URLs

Validate URLs before sending requests:

```python
import re

def is_valid_github_url(url):
    pattern = r'^https?://github\.com/[\w-]+/[\w.-]+/?$'
    return bool(re.match(pattern, url))

if is_valid_github_url(repo_url):
    result = process_repository(repo_url)
```

### 6. Set Timeouts

Always set request timeouts:

```python
response = requests.post(
    url,
    json=data,
    timeout=300  # 5 minutes for large repositories
)
```

### 7. Stream Large Downloads

Use streaming for large file downloads:

```python
response = requests.get(download_url, stream=True)
with open(output_file, 'wb') as f:
    for chunk in response.iter_content(chunk_size=8192):
        f.write(chunk)
```

## Troubleshooting

### Problem: 401 Unauthorized

**Cause:** Missing or incorrect API key

**Solution:**
- Verify API key is correct
- Include `X-API-Key` header in requests
- Contact administrator if key is invalid

### Problem: 429 Too Many Requests

**Cause:** Rate limit exceeded

**Solution:**
- Wait for rate limit window to reset
- Implement exponential backoff
- Reduce request frequency
- Consider upgrading rate limits

### Problem: 400 Invalid URL

**Cause:** Invalid GitHub repository URL

**Solution:**
- Ensure URL is a valid GitHub repository
- Use HTTPS URLs
- Check repository is public
- Remove trailing slashes or query parameters

### Problem: Processing Takes Too Long

**Cause:** Large repository

**Solution:**
- Increase request timeout
- Large repositories may take 1-2 minutes
- Check backend logs for issues
- Consider repository size limits

### Problem: Download Link Expired

**Cause:** File was cleaned up

**Solution:**
- Process repository again
- Files are temporary and may be deleted
- Download immediately after processing

## Interactive Documentation

For interactive API testing, visit:

- **Swagger UI**: `https://YOUR_DOMAIN/docs`
- **ReDoc**: `https://YOUR_DOMAIN/redoc`

These interfaces allow you to:
- Test API endpoints directly
- View detailed schema documentation
- See example requests and responses
- Try different parameters

## Support

For additional support:

1. Check application logs on your deployment
2. Verify health endpoint: `GET /health`
3. Review error response details
4. Contact your deployment administrator
5. Report issues on GitHub repository

## Additional Resources

- [README.md](./README.md) - General documentation
- [DEPLOYMENT.md](./DEPLOYMENT.md) - VPS deployment guide
- [GCloud_Deploy.md](./GCloud_Deploy.md) - Google Cloud deployment guide
- [DOCKER_SETUP.md](./DOCKER_SETUP.md) - Docker setup and development guide
