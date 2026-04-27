"""Pydantic schemas for request/response validation."""
from pydantic import BaseModel, Field, field_validator
from typing import Optional


class ReviewCreate(BaseModel):
    """Schema for creating a review."""
    
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    text: str = Field(..., min_length=5, max_length=5000)
    rating: Optional[int] = Field(None, ge=1, le=5)
    storage: Optional[str] = None
    color: Optional[str] = None
    verified: Optional[bool] = False

    @field_validator("text")
    def validate_text(cls, v):
        """Ensure text is not empty or only whitespace."""
        if not v or v.isspace():
            raise ValueError("Review text cannot be empty")
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Great product",
                "text": "This product is excellent and works as advertised.",
                "rating": 5,
                "storage": "128GB",
                "color": "Black",
                "verified": True
            }
        }


class SentimentResponse(BaseModel):
    """Schema for sentiment analysis response."""
    
    text: str
    sentiment: str = Field(..., description="POSITIVE or NEGATIVE")
    confidence: float = Field(..., ge=0.0, le=1.0)

    class Config:
        json_schema_extra = {
            "example": {
                "text": "This product is excellent",
                "sentiment": "POSITIVE",
                "confidence": 0.99
            }
        }


class ReviewResponse(BaseModel):
    """Schema for review response."""
    
    id: int
    title: Optional[str] = None
    text: str
    rating: Optional[int] = None
    storage: Optional[str] = None
    color: Optional[str] = None
    verified: bool
    sentiment: str
    sentiment_score: float

    class Config:
        from_attributes = True


class ReviewListResponse(BaseModel):
    """Schema for paginated review list response."""
    
    total: int
    items: list[ReviewResponse]


class HealthResponse(BaseModel):
    """Schema for health check response."""
    
    status: str
    version: str

class IngestRequest(BaseModel):
    url: str