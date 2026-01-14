"""
Integration tests for the API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


class TestRootEndpoint:
    """Tests for root endpoint."""
    
    def test_root_returns_ok(self):
        """Test root endpoint returns OK status."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "running" in data["message"].lower()


class TestHealthEndpoint:
    """Tests for health check endpoint."""
    
    def test_health_returns_healthy(self):
        """Test health endpoint returns healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_health_returns_enhanced_info(self):
        """Test health endpoint returns enhanced health information."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        
        # Check for enhanced health check fields
        assert "git_available" in data
        assert "disk_space_ok" in data
        assert "output_dir_writable" in data
        assert "version" in data
        assert "details" in data
        
        # These should all be booleans
        assert isinstance(data["git_available"], bool)
        assert isinstance(data["disk_space_ok"], bool)
        assert isinstance(data["output_dir_writable"], bool)


class TestProcessRepoEndpoint:
    """Tests for process-repo endpoint."""
    
    def test_invalid_url_returns_400(self):
        """Test invalid URL returns 400 error."""
        response = client.post("/process-repo", json={
            "repo_url": "not-a-valid-url",
            "format": "markdown"
        })
        assert response.status_code == 400
    
    def test_non_github_url_returns_400(self):
        """Test non-GitHub URL returns 400 error."""
        response = client.post("/process-repo", json={
            "repo_url": "https://gitlab.com/user/repo",
            "format": "markdown"
        })
        assert response.status_code == 400
    
    def test_invalid_format_returns_422(self):
        """Test invalid format returns 422 error."""
        response = client.post("/process-repo", json={
            "repo_url": "https://github.com/user/repo",
            "format": "invalid_format"
        })
        assert response.status_code == 422
    
    def test_missing_repo_url_returns_422(self):
        """Test missing repo_url returns 422 error."""
        response = client.post("/process-repo", json={
            "format": "markdown"
        })
        assert response.status_code == 422
    
    def test_error_response_is_standardized(self):
        """Test error responses have standardized format."""
        response = client.post("/process-repo", json={
            "repo_url": "not-a-valid-url",
            "format": "markdown"
        })
        assert response.status_code == 400
        data = response.json()
        
        # Check for standardized error structure
        assert "status" in data
        assert data["status"] == "error"
        assert "error" in data
        
        error = data["error"]
        assert "error_code" in error
        assert "error_type" in error
        assert "message" in error
    
    def test_request_id_in_response_header(self):
        """Test that X-Request-ID is present in response headers."""
        response = client.post("/process-repo", json={
            "repo_url": "not-a-valid-url",
            "format": "markdown"
        })
        
        # Check for request ID header
        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) > 0
    
    def test_accepts_include_content_parameter(self):
        """Test that include_content parameter is accepted in request validation."""
        # Test that include_content is a valid parameter by sending it
        # We expect a 400 due to validation error on the URL format, not 422 for unknown field
        response = client.post("/process-repo", json={
            "repo_url": "invalid-url",
            "format": "markdown",
            "include_content": True
        })
        # We should get 400 (bad URL) not 422 (validation error for unknown field)
        assert response.status_code == 400


class TestDownloadEndpoint:
    """Tests for download endpoint."""
    
    def test_nonexistent_file_returns_404(self):
        """Test nonexistent file returns 404 error."""
        response = client.get("/download/nonexistent_file.md")
        assert response.status_code == 404
    
    def test_directory_traversal_blocked(self):
        """Test directory traversal is blocked."""
        # FastAPI normalizes the path, so ../../../etc/passwd becomes just the last segment
        # The validation still blocks it because the check looks for special characters
        response = client.get("/download/..%2F..%2F..%2Fetc%2Fpasswd")
        # The validation catches encoded slashes
        assert response.status_code in [400, 404]
    
    def test_404_error_is_standardized(self):
        """Test 404 error has standardized format."""
        response = client.get("/download/nonexistent_file.md")
        assert response.status_code == 404
        data = response.json()
        
        # Check for standardized error structure
        assert "status" in data
        assert data["status"] == "error"
        assert "error" in data
        
        error = data["error"]
        assert "error_code" in error
        assert "error_type" in error
        assert "message" in error


class TestDeleteEndpoint:
    """Tests for delete endpoint."""
    
    def test_nonexistent_file_returns_404(self):
        """Test deleting nonexistent file returns 404 error."""
        response = client.delete("/download/nonexistent_file.md")
        assert response.status_code == 404
    
    def test_directory_traversal_blocked(self):
        """Test directory traversal is blocked on delete."""
        # FastAPI normalizes the path, so ../../../etc/passwd becomes just the last segment
        # The validation still blocks it because the check looks for special characters
        response = client.delete("/download/..%2F..%2F..%2Fetc%2Fpasswd")
        # The validation catches encoded slashes or file not found
        assert response.status_code in [400, 404]


class TestRequestTracking:
    """Tests for request tracking functionality."""
    
    def test_custom_request_id_is_echoed(self):
        """Test that provided X-Request-ID is echoed back."""
        custom_id = "test-request-12345"
        response = client.get("/health", headers={"X-Request-ID": custom_id})
        
        assert response.status_code == 200
        assert response.headers.get("X-Request-ID") == custom_id
    
    def test_request_id_generated_if_not_provided(self):
        """Test that request ID is generated if not provided."""
        response = client.get("/health")
        
        assert response.status_code == 200
        request_id = response.headers.get("X-Request-ID")
        assert request_id is not None
        assert len(request_id) > 0
