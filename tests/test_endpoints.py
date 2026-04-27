"""Unit tests for API endpoints."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestHealthCheck:
    """Tests for health check endpoint."""
    
    def test_health_check_returns_200(self):
        """Test that health check returns 200 status."""
        response = client.get("/")
        assert response.status_code == 200
    
    def test_health_check_response_format(self):
        """Test that health check returns correct format."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert data["status"] == "healthy"


class TestSentimentAnalysis:
    """Tests for sentiment analysis endpoint."""
    
    def test_analyze_sentiment_positive(self):
        """Test sentiment analysis for positive review."""
        payload = {
            "text": "This product is excellent and works perfectly!"
        }
        response = client.post("/api/v1/analyze-sentiment", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "sentiment" in data
        assert "confidence" in data
        assert 0.0 <= data["confidence"] <= 1.0
    
    def test_analyze_sentiment_negative(self):
        """Test sentiment analysis for negative review."""
        payload = {
            "text": "This product is terrible and broke immediately!"
        }
        response = client.post("/api/v1/analyze-sentiment", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "sentiment" in data
        assert "confidence" in data
    
    def test_analyze_sentiment_empty_text(self):
        """Test sentiment analysis with empty text."""
        payload = {
            "text": ""
        }
        response = client.post("/api/v1/analyze-sentiment", json=payload)
        assert response.status_code == 422  # Validation error


class TestReviewsEndpoint:
    """Tests for reviews retrieval endpoint."""
    
    def test_get_reviews_returns_200(self):
        """Test that get reviews returns 200 status."""
        response = client.get("/api/v1/reviews")
        assert response.status_code == 200
    
    def test_get_reviews_response_format(self):
        """Test that reviews response has correct format."""
        response = client.get("/api/v1/reviews")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "items" in data
        assert isinstance(data["total"], int)
        assert isinstance(data["items"], list)
    
    def test_get_reviews_with_limit(self):
        """Test get reviews with limit parameter."""
        response = client.get("/api/v1/reviews?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 10
    
    def test_get_reviews_with_invalid_limit(self):
        """Test get reviews with invalid limit."""
        response = client.get("/api/v1/reviews?limit=2000")
        assert response.status_code == 422  # Validation error


class TestKeywordsEndpoint:
    """Tests for keywords extraction endpoint."""
    
    def test_get_keywords_returns_200(self):
        """Test that keywords endpoint returns 200."""
        response = client.get("/api/v1/keywords")
        assert response.status_code == 200
    
    def test_get_keywords_response_format(self):
        """Test keywords response format."""
        response = client.get("/api/v1/keywords")
        assert response.status_code == 200
        data = response.json()
        assert "positive_keywords" in data
        assert "negative_keywords" in data
        assert isinstance(data["positive_keywords"], list)
        assert isinstance(data["negative_keywords"], list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
