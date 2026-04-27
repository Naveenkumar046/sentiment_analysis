"""API endpoints for sentiment analysis service."""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from database.session import get_db
from database.models import Review as ReviewModel
from schemas.review import (
    ReviewCreate, SentimentResponse, ReviewResponse, ReviewListResponse,IngestRequest, HealthResponse
)
from sentiment_analysis.nlp_engine import get_nlp_engine
from services.scraper import AmazonScraper, ScraperException
from search_engine.router import classify_intent
from search_engine.faiss import search_rag
from typing import List, Optional
import logging
from starlette.exceptions import HTTPException as StarletteHTTPException
from collections import Counter

logger = logging.getLogger(__name__)

router = APIRouter(tags=["reviews"])



@router.post(
    "/ingest",
    status_code=status.HTTP_200_OK,
    summary="Scrape and ingest reviews from URL"
)
def scrape_and_store(payload: IngestRequest, db: Session = Depends(get_db)):
    url = payload.url
    try:
        scraper = AmazonScraper()
        raw_data = scraper.scrape(url)
        
        if not raw_data:
            # THIS IS THE 422: Ensure it doesn't get converted to 500
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Scraper found the page but 0 reviews were extracted. This usually means Amazon's bot protection is active."
            )
        
        print(f"Raw data extracted: {raw_data[:2]}...")  # Print first 2 items for sanity check
        
        # nlp_engine = get_nlp_engine()
        saved_count = 0
        
        for item in raw_data:
            try:
                # 2. Ensure text exists before passing to NLP
                text_content = item.get('text', '')
                if not text_content:
                    continue

                # sentiment, score = nlp_engine.get_sentiment(text_content)
                
                db_review = ReviewModel(
                    title=item.get('title'),
                    text=text_content,
                    rating=item.get('rating'),
                    storage=item.get('storage'),
                    color=item.get('color'),
                    verified=item.get('verified', False),
                    # sentiment=sentiment,
                    # sentiment_score=score
                )
                db.add(db_review)
                saved_count += 1
            except Exception as e:
                # Use logger.exception to see the FULL traceback
                logger.exception("Validation error while creating ReviewModel")
                continue
        
        db.commit()
        logger.info(f"Successfully ingested {saved_count} reviews from {url}")
        
        return {
            "status": "success",
            "count": saved_count,
            "message": f"Ingested {saved_count} reviews"
        }
    
    except StarletteHTTPException as e:
        # Re-raise FastAPI's own exceptions so they aren't caught by the general Exception block
        raise e
    except ScraperException as e:
        logger.error(f"Scraper error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Ingestion failed due to an unexpected error")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/analyze-stored",
    status_code=status.HTTP_200_OK,
    summary="Process stored reviews for sentiment and extract top keywords"
)
def analyze_and_extract_stats(db: Session = Depends(get_db)):
    """
    1. Performs sentiment analysis on all reviews missing sentiment data.
    2. Extracts top positive and negative keywords from the entire dataset.
    """
    try:
        nlp_engine = get_nlp_engine()
        
        # --- PART 1: Update Sentiment for Unprocessed Reviews ---
        # Find reviews where sentiment hasn't been set yet
        unprocessed_reviews = db.query(ReviewModel).filter(ReviewModel.sentiment == None).all()
        
        processed_count = 0
        for review in unprocessed_reviews:
            try:
                sentiment, score = nlp_engine.get_sentiment(review.text)
                review.sentiment = sentiment
                review.sentiment_score = score
                processed_count += 1
            except Exception as e:
                logger.error(f"Failed to analyze review {review.id}: {str(e)}")
                continue
        
        db.commit() # Save sentiment updates
        
        # --- PART 2: Extract Top Keywords ---
        pos_results = db.query(ReviewModel.text).filter(
            ReviewModel.sentiment == "POSITIVE"
        ).all()
        
        neg_results = db.query(ReviewModel.text).filter(
            ReviewModel.sentiment == "NEGATIVE"
        ).all()
        
        pos_texts = [r[0] for r in pos_results if r[0]]
        neg_texts = [r[0] for r in neg_results if r[0]]
        
        # Run advanced keyword extraction
        top_positive_features = nlp_engine.extract_keywords(pos_texts, top_n=12)
        top_negative_features = nlp_engine.extract_keywords(neg_texts, top_n=12)
        
        return {
            "status": "success",
            "counts": {
                "positive": len(pos_texts),
                "negative": len(neg_texts)
            },
            "insights": {
                "positive_trends": top_positive_features,
                "negative_pain_points": top_negative_features
            }
        }

    except Exception as e:
        db.rollback()
        logger.exception("Analysis and keyword extraction failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Analysis failed: {str(e)}"
        )


@router.post(
    "/analyze-sentiment",
    response_model=SentimentResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze sentiment of a single review"
)
def analyze_single_review(review: ReviewCreate):
    
    try:
        nlp_engine = get_nlp_engine()
        label, score = nlp_engine.get_sentiment(review.text)
        
        return SentimentResponse(
            text=review.text,
            sentiment=label,
            confidence=score
        )
    except Exception as e:
        logger.error(f"Error analyzing sentiment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze sentiment"
        )


#/api/v1/reviews?sentiment=POSITIVE&color=black&limit=5
#/api/v1/reviews?color=blue
@router.get(
    "/reviews",
    response_model=ReviewListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get reviews with optional filters"
)
def get_reviews(
    color: Optional[str] = Query(None, description="Filter by color (case-insensitive)"),
    storage: Optional[str] = Query(None, description="Filter by storage (e.g., 128GB)"),
    rating: Optional[int] = Query(None, ge=1, le=5, description="Filter by exact rating"),
    sentiment: Optional[str] = Query(None, description="Filter by sentiment (POSITIVE/NEGATIVE)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    try:
        query = db.query(ReviewModel)
        
        # 1. Filter by Color (Case-insensitive partial match)
        if color:
            # Using .ilike allows matching "Blue" if user sends "blue"
            query = query.filter(ReviewModel.color.ilike(f"%{color.strip()}%"))
            
        # 2. Filter by Storage (Case-insensitive partial match)
        if storage:
            # Matches "128GB" even if user sends "128"
            query = query.filter(ReviewModel.storage.ilike(f"%{storage.strip()}%"))
            
        # 3. Filter by Exact Rating
        if rating is not None:
            query = query.filter(ReviewModel.rating == rating)
            
        # 4. Filter by Sentiment
        if sentiment:
            # Standardize to uppercase for matching
            query = query.filter(ReviewModel.sentiment == sentiment.strip().upper())
        
        # Count results before pagination
        total = query.count()
        
        # Order by latest reviews first (assuming you have an id or created_at)
        reviews = query.order_by(ReviewModel.id.desc()).offset(skip).limit(limit).all()
        
        return ReviewListResponse(
            total=total,
            items=[ReviewResponse.from_orm(r) for r in reviews]
        )
    except Exception as e:
        logger.error(f"Error retrieving reviews: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve reviews"
        )


@router.get(
    "/keywords",
    status_code=status.HTTP_200_OK,
    summary="Extract keywords from positive and negative reviews"
)
def get_keywords(
    db: Session = Depends(get_db),
    top_n: int = Query(10, ge=1, le=50, description="Number of top keywords")
):
    """
    Extract most common keywords from positive and negative reviews.
    
    Args:
        db: Database session
        top_n: Number of top keywords to extract
        
    Returns:
        Dictionary with positive and negative keywords
    """
    try:
        nlp_engine = get_nlp_engine()
        pos_results = db.query(ReviewModel.text).filter(
            ReviewModel.sentiment == "POSITIVE"
        ).all()
        
        neg_results = db.query(ReviewModel.text).filter(
            ReviewModel.sentiment == "NEGATIVE"
        ).all()
        
        pos_texts = [r[0] for r in pos_results if r[0]]
        neg_texts = [r[0] for r in neg_results if r[0]]
        
        # Run advanced keyword extraction
        top_positive_features = nlp_engine.extract_keywords(pos_texts, top_n=12)
        top_negative_features = nlp_engine.extract_keywords(neg_texts, top_n=12)
        
        return {
            "status": "success",
            "counts": {
                "positive": len(pos_texts),
                "negative": len(neg_texts)
            },
            "insights": {
                "positive_trends": top_positive_features,
                "negative_pain_points": top_negative_features
            }
        }
        
        # pos_reviews = db.query(ReviewModel.text).filter(
        #     ReviewModel.rating >= 4
        # ).all()
        # neg_reviews = db.query(ReviewModel.text).filter(
        #     ReviewModel.rating <= 2
        # ).all()
        
        # pos_texts = [r[0] for r in pos_reviews if r[0]]
        # neg_texts = [r[0] for r in neg_reviews if r[0]]
        
        # pos_keywords = nlp_engine.extract_keywords(pos_texts, top_n)
        # neg_keywords = nlp_engine.extract_keywords(neg_texts, top_n)
        
        # return {
        #     "positive_keywords": pos_keywords,
        #     "negative_keywords": neg_keywords,
        #     "positive_count": len(pos_texts),
        #     "negative_count": len(neg_texts)
        # }
    except Exception as e:
        logger.error(f"Error extracting keywords: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to extract keywords"
        )


#get all from db
@router.get(
    "/all-reviews", 
    status_code=status.HTTP_200_OK,
    summary="Get all reviews (for debugging)"
)
def get_all_reviews(db: Session = Depends(get_db)):
    try:
        reviews = db.query(ReviewModel).all()
        return [ReviewResponse.from_orm(r) for r in reviews]
    except Exception as e:
        logger.error(f"Error retrieving all reviews: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve all reviews"
        )   


#delete all from db
@router.delete(
    "/delete-all", 
    status_code=status.HTTP_200_OK,
    summary="Delete all reviews (for debugging)"
)   
def delete_all_reviews(db: Session = Depends(get_db)):
    try:
        deleted = db.query(ReviewModel).delete()
        db.commit()
        return {"status": "success", "deleted_count": deleted}
    except Exception as e:
        logger.error(f"Error deleting all reviews: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete all reviews"
        )    

#GENAI CHATBOT ENDPOINT

# 1 - RAG
@router.post(
    "/query",
    status_code=status.HTTP_200_OK,
    summary="Query the review dataset with natural language"
)
def query_responses(
    query: str = Query(..., description="Natural language query about the reviews"),
    db: Session = Depends(get_db)
):
    try:
        # Placeholder for RAG implementation
        # 1. Retrieve relevant reviews based on query (e.g., using full-text search or embedding similarity)
        # 2. Use a GenAI model to generate a response based on retrieved reviews
        analysis = classify_intent(query)
        logger.info(f"Classified query intent as: {analysis}")

        if analysis == "rag":
            rag_response = search_rag(query)
            return {
                "status": "success",
                "query": query,
                "response": rag_response
            }

    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process query"
        )
    