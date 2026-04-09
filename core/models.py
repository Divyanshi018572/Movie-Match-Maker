from typing import Optional, List, Dict
from pydantic import BaseModel

class TMDBMovieCard(BaseModel):
    tmdb_id: int
    title: str
    poster_url: Optional[str] = None
    release_date: Optional[str] = None
    vote_average: Optional[float] = None

class TMDBMovieDetails(BaseModel):
    tmdb_id: int
    title: str
    overview: Optional[str] = None
    release_date: Optional[str] = None
    poster_url: Optional[str] = None
    backdrop_url: Optional[str] = None
    trailer_youtube_id: Optional[str] = None
    watch_providers: List[dict] = []
    watch_link: str = ""
    collection: Optional[dict] = None
    reviews: List[dict] = []
    genres: List[dict] = []

class TFIDFRecItem(BaseModel):
    title: str
    score: float
    hybrid_score: float = 0.0
    tmdb: Optional[TMDBMovieCard] = None

class SearchBundleResponse(BaseModel):
    query: str
    movie_details: TMDBMovieDetails
    tfidf_recommendations: List[TFIDFRecItem]
    genre_recommendations: List[TMDBMovieCard]

class ChatRequest(BaseModel):
    message: str
    history: List[dict] = []

class SummaryRequest(BaseModel):
    title: str
    overview: Optional[str] = ""
    genres: List[str] = []
    release_date: Optional[str] = ""
    vote_average: Optional[float] = 0.0

class ConvSearchRequest(BaseModel):
    query: str
