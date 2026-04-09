import ssl, requests, time
from typing import Dict, Any, Optional, List
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from fastapi import HTTPException

from core.config import TMDB_API_KEY, TMDB_BASE, TMDB_IMG_500
from core.models import TMDBMovieCard, TMDBMovieDetails

_TMDB_RETRY = Retry(total=5, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504], allowed_methods=["GET"])
_TMDB_SESSION = requests.Session()
_TMDB_SESSION.mount("https://", HTTPAdapter(max_retries=_TMDB_RETRY))

def _norm_title(t: str) -> str:
    return str(t).strip().lower()

def make_img_url(path: Optional[str]) -> Optional[str]:
    if not path:
        return None
    return f"{TMDB_IMG_500}{path}"

async def tmdb_get(path: str, params: Dict[str, Any]) -> Dict[str, Any]:
    q = dict(params)
    q["api_key"] = TMDB_API_KEY

    last_err = None
    for attempt in range(1, 4):
        print(f"DEBUG: TMDB Fetch Attempt {attempt} | Path: {path}")
        try:
            r = _TMDB_SESSION.get(f"{TMDB_BASE}{path}", params=q, timeout=12)
            break
        except requests.exceptions.Timeout:
            last_err = "Request Timed Out (12s)"
            print(f"DEBUG: TMDB Timeout on attempt {attempt}")
            continue
        except Exception as e:
            last_err = str(e)
            print(f"DEBUG: TMDB Error on attempt {attempt}: {e}")
            time.sleep(0.3 * attempt)
    else:
        raise HTTPException(
            status_code=504,
            detail=f"TMDB Gateway Timeout after 3 attempts. Last error: {last_err}",
        )

    if r.status_code != 200:
        print(f"DEBUG: TMDB non-200. Code: {r.status_code} | Body: {r.text[:100]}")
        raise HTTPException(
            status_code=502, detail=f"TMDB API Remote Error {r.status_code}"
        )

    return r.json()

async def tmdb_cards_from_results(
    results: List[dict], limit: int = 20
) -> List[TMDBMovieCard]:
    out: List[TMDBMovieCard] = []
    for m in (results or [])[:limit]:
        out.append(
            TMDBMovieCard(
                tmdb_id=int(m["id"]),
                title=m.get("title") or m.get("name") or "",
                poster_url=make_img_url(m.get("poster_path")),
                release_date=m.get("release_date"),
                vote_average=m.get("vote_average"),
            )
        )
    return out

async def tmdb_search_first(query: str) -> Optional[dict]:
    data = await tmdb_get(
        "/search/movie",
        {
            "query": query,
            "include_adult": "false",
            "language": "en-US",
            "page": 1,
        },
    )
    results = data.get("results", [])
    return results[0] if results else None

async def tmdb_search_movies(query: str, page: int = 1) -> Dict[str, Any]:
    return await tmdb_get(
        "/search/movie",
        {
            "query": query,
            "include_adult": "false",
            "language": "en-US",
            "page": page,
        },
    )

async def tmdb_movie_details(movie_id: int) -> TMDBMovieDetails:
    data = await tmdb_get(f"/movie/{movie_id}", {"language": "en-US", "append_to_response": "videos,watch/providers,reviews"})
    
    trailer_key = None
    videos = data.get("videos", {}).get("results", [])
    for v in videos:
        if v.get("site") == "YouTube" and v.get("type") == "Trailer":
            trailer_key = v.get("key")
            break

    providers_data = []
    us_providers = data.get("watch/providers", {}).get("results", {}).get("US", {})
    watch_link = us_providers.get("link", "")
    
    for p_type in ["flatrate", "rent", "buy"]:
        if p_type in us_providers:
            for p in us_providers[p_type]:
                providers_data.append({
                    "name": p.get("provider_name"),
                    "logo_url": make_img_url(p.get("logo_path"))
                })
            break

    col_data = None
    raw_col = data.get("belongs_to_collection")
    if raw_col:
        col_data = {
            "id": raw_col.get("id"),
            "name": raw_col.get("name"),
            "poster_url": make_img_url(raw_col.get("poster_path")),
        }

    rev_data = []
    raw_revs = data.get("reviews", {}).get("results", [])[:3]
    for r in raw_revs:
        rev_data.append({
            "author": r.get("author", "Unknown"),
            "content": r.get("content", ""),
            "url": r.get("url", "")
        })

    return TMDBMovieDetails(
        tmdb_id=int(data["id"]),
        title=data.get("title") or "",
        overview=data.get("overview"),
        release_date=data.get("release_date"),
        poster_url=make_img_url(data.get("poster_path")),
        backdrop_url=make_img_url(data.get("backdrop_path")),
        trailer_youtube_id=trailer_key,
        watch_providers=providers_data,
        watch_link=watch_link,
        collection=col_data,
        reviews=rev_data,
        genres=data.get("genres", []) or [],
    )
