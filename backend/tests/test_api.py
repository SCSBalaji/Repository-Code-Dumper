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
