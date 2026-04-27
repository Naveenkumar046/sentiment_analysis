"""NLP sentiment analysis engine."""
from transformers import pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from config import get_settings
import logging
from typing import Tuple, List
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag
import re

logger = logging.getLogger(__name__)

try:
    nltk.download('punkt', quiet=True)
    nltk.download('averaged_perceptron_tagger', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('punkt_tab', quiet=True)
    nltk.download('averaged_perceptron_tagger_eng', quiet=True)
except Exception as e:
    logger.warning(f"NLTK download warning: {e}")

class NLPEngine:
    """Sentiment analysis engine using DistilBERT."""
    
    def __init__(self):
        """Initialize NLP engine with transformer model."""
        settings = get_settings()
        try:
            self.sentiment_pipe = pipeline(
                "sentiment-analysis",
                model=settings.NLP_MODEL,
                device=settings.TRANSFORMER_DEVICE
            )
            logger.info(f"NLP Engine initialized with model: {settings.NLP_MODEL}")
        except Exception as e:
            logger.error(f"Failed to initialize NLP engine: {str(e)}")
            raise

    def get_sentiment(self, text: str) -> Tuple[str, float]:
        """
        Analyze sentiment of given text.
        
        Args:
            text: Input text to analyze (max 512 tokens)
            
        Returns:
            Tuple of (sentiment_label, confidence_score)
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for sentiment analysis")
            return "NEUTRAL", 0.0
        
        try:
            # DistilBERT has a 512 token limit
            truncated_text = text[:512]
            result = self.sentiment_pipe(truncated_text)[0]
            
            # Normalize label format
            label = result['label'].upper()
            score = float(result['score'])
            
            return label, score
        except Exception as e:
            logger.error(f"Error during sentiment analysis: {str(e)}")
            raise

    def extract_keywords_old(self, texts: List[str], top_n: int = 10) -> List[str]:
        """
        Extract top keywords from a collection of texts.
        
        Args:
            texts: List of text documents
            top_n: Number of top keywords to extract
            
        Returns:
            List of top keywords
        """
        if not texts or len(texts) == 0:
            logger.warning("Empty text collection provided for keyword extraction")
            return []
        
        try:
            vectorizer = TfidfVectorizer(
                stop_words='english',
                max_features=top_n,
                min_df=1
            )
            tfidf_matrix = vectorizer.fit_transform(texts)
            keywords = vectorizer.get_feature_names_out().tolist()
            logger.debug(f"Extracted {len(keywords)} keywords from {len(texts)} texts")
            return keywords
        except Exception as e:
            logger.error(f"Error extracting keywords: {str(e)}")
            return []
    
    def extract_keywords(self, texts: list, top_n: int = 12):
        if not texts or len(texts) < 1:
            return []

        # 1. Setup Stopwords (English + Domain specific)
        stop_words = set(stopwords.words('english'))
        domain_noise = {
            'iphone', 'apple', 'phone', 'device', 'mobile', 'amazon', 
            'product', 'order', 'year', 'price', 'delivery', 'bought', 
            'buy', 'good', 'bad', 'great', 'awesome', 'just', 'time'
        }
        stop_words.update(domain_noise)

        # 2. Pre-process and Filter by Part-of-Speech (Noun/Adjective)
        processed_docs = []
        for text in texts:
            # Tokenize
            words = word_tokenize(text.lower())
            # Tag Parts of Speech (e.g., 'Battery' -> 'NN', 'Great' -> 'JJ')
            tagged_words = pos_tag(words)
            
            # Keep only Nouns (NN) and Adjectives (JJ)
            filtered_words = [
                word for word, tag in tagged_words 
                if (tag.startswith('NN') or tag.startswith('JJ')) 
                and word not in stop_words 
                and len(word) > 3
                and word.isalpha() # Removes numbers and scraping artifacts
            ]
            processed_docs.append(" ".join(filtered_words))

        # 3. Use TF-IDF to find statistically significant keywords/phrases
        vectorizer = TfidfVectorizer(
            ngram_range=(1, 2), # Capture "battery life"
            max_features=1000
        )
        
        try:
            tfidf_matrix = vectorizer.fit_transform(processed_docs)
            scores = tfidf_matrix.sum(axis=0).A1
            words = vectorizer.get_feature_names_out()
            
            # Sort by TF-IDF importance
            word_scores = sorted(zip(words, scores), key=lambda x: x[1], reverse=True)
            
            return [word for word, score in word_scores[:top_n]]
        except Exception as e:
            logger.error(f"Keyword extraction error: {e}")
            return []
        
    # def extract_keywords(self, texts: list, top_n: int = 10):
    #     if not texts:
    #         return []
        
    #     # Simple but effective: Use TF-IDF to find "important" words
    #     # and exclude common English "stop words" (the, a, is, etc.)
    #     vectorizer = TfidfVectorizer(stop_words='english', max_features=100)
    #     tfidf_matrix = vectorizer.fit_transform(texts)
        
    #     # Sum the TF-IDF scores for each word across all reviews
    #     scores = tfidf_matrix.sum(axis=0).A1
    #     words = vectorizer.get_feature_names_out()
        
    #     # Sort words by their scores
    #     word_scores = sorted(zip(words, scores), key=lambda x: x[1], reverse=True)
        
    #     # Return only the top N words
    #     return [word for word, score in word_scores[:top_n]]

# Lazy-loaded singleton instance
_nlp_engine = None


def get_nlp_engine() -> NLPEngine:
    """Get or create NLP engine instance."""
    global _nlp_engine
    if _nlp_engine is None:
        _nlp_engine = NLPEngine()
    return _nlp_engine
