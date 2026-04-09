from typing import List, Any, Dict
from fastapi import APIRouter, HTTPException, Query

from core.models import TMDBMovieCard, TMDBMovieDetails
from core.utils import tmdb_get, tmdb_cards_from_results, tmdb_movie_details, tmdb_search_first, tmdb_search_movies, make_img_url

router = APIRouter()

TMDB_GENRES = {
    "Action": 28, "Adventure": 12, "Animation": 16, "Comedy": 35,
    "Crime": 80, "Documentary": 99, "Drama": 18, "Family": 10751,
    "Fantasy": 14, "History": 36, "Horror": 27, "Music": 10402,
    "Mystery": 9648, "Romance": 10749, "Science Fiction": 878,
    "Thriller": 53, "War": 10752, "Western": 37,
}

@router.get("/home", response_model=List[TMDBMovieCard])
async def home(
    category: str = Query("popular"),
    limit: int = Query(24, ge=1, le=50),
):
    try:
        if category == "trending":
            data = await tmdb_get("/trending/movie/day", {"language": "en-US"})
            return await tmdb_cards_from_results(data.get("results", []), limit=limit)

        if category not in {"popular", "top_rated", "upcoming", "now_playing"}:
            raise HTTPException(status_code=400, detail="Invalid category")

        data = await tmdb_get(f"/movie/{category}", {"language": "en-US", "page": 1})
        return await tmdb_cards_from_results(data.get("results", []), limit=limit)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Home route failed: {e}")

@router.get("/tmdb/search")
async def tmdb_search(
    query: str = Query(..., min_length=1),
    page: int = Query(1, ge=1, le=10),
):
    return await tmdb_search_movies(query=query, page=page)

@router.get("/movie/id/{tmdb_id}", response_model=TMDBMovieDetails)
async def movie_details_route(tmdb_id: int):
    return await tmdb_movie_details(tmdb_id)

@router.get("/recommend/genre", response_model=List[TMDBMovieCard])
async def recommend_genre(
    tmdb_id: int = Query(...),
    limit: int = Query(18, ge=1, le=50),
):
    details = await tmdb_movie_details(tmdb_id)
    if not details.genres:
        return []

    genre_id = details.genres[0]["id"]
    discover = await tmdb_get(
        "/discover/movie",
        {
            "with_genres": genre_id,
            "language": "en-US",
            "sort_by": "popularity.desc",
            "page": 1,
        },
    )
    cards = await tmdb_cards_from_results(discover.get("results", []), limit=limit)
    return [c for c in cards if c.tmdb_id != tmdb_id]

@router.get("/discover/genre")
async def discover_by_genre(
    genre: str = Query(...),
    page: int = Query(1),
    year_from: int = Query(1900),
    year_to: int = Query(2025),
    min_rating: float = Query(0.0),
):
    genre_id = TMDB_GENRES.get(genre)
    if not genre_id:
        raise HTTPException(status_code=400, detail=f"Unknown genre: {genre}")
    data = await tmdb_get(
        "/discover/movie",
        {
            "with_genres": genre_id,
            "sort_by": "popularity.desc",
            "language": "en-US",
            "page": page,
            "primary_release_date.gte": f"{year_from}-01-01",
            "primary_release_date.lte": f"{year_to}-12-31",
            "vote_average.gte": min_rating,
            "vote_count.gte": 50,
        },
    )
    results = data.get("results", [])
    cards = [
        {
            "tmdb_id": int(m["id"]),
            "title": m.get("title", ""),
            "poster_url": make_img_url(m.get("poster_path")),
            "release_date": m.get("release_date", ""),
            "vote_average": m.get("vote_average", 0),
        }
        for m in results
        if m.get("id") and m.get("title")
    ]
    return {"genre": genre, "page": page, "results": cards}

@router.get("/genres")
def list_genres():
    return list(TMDB_GENRES.keys())
