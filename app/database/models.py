from sqlalchemy import Column, Integer, String, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    text = Column(String)
    rating = Column(Integer)
    storage = Column(String)
    color = Column(String)
    verified = Column(Boolean)
    sentiment = Column(String)
    sentiment_score = Column(Float)
