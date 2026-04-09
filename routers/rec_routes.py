import os
import pickle
import numpy as np
import pandas as pd
from typing import List, Tuple, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query

from core.models import SearchBundleResponse, TFIDFRecItem, TMDBMovieCard
from core.utils import _norm_title, tmdb_search_first, make_img_url, tmdb_movie_details, tmdb_get, tmdb_cards_from_results

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DF_PATH = os.path.join(BASE_DIR, "df.pkl")
INDICES_PATH = os.path.join(BASE_DIR, "indices.pkl")
TFIDF_MATRIX_PATH = os.path.join(BASE_DIR, "tfidf_matrix.pkl")
TFIDF_PATH = os.path.join(BASE_DIR, "tfidf.pkl")

df: Optional[pd.DataFrame] = None
indices_obj: Any = None
tfidf_matrix: Any = None
tfidf_obj: Any = None

TITLE_TO_IDX: Optional[Dict[str, int]] = None

def build_title_to_idx_map(indices: Any) -> Dict[str, int]:
    title_to_idx: Dict[str, int] = {}
    if isinstance(indices, dict):
        for k, v in indices.items():
            title_to_idx[_norm_title(k)] = int(v)
        return title_to_idx
    try:
        for k, v in indices.items():
            title_to_idx[_norm_title(k)] = int(v)
        return title_to_idx
    except Exception:
        raise RuntimeError("indices.pkl must be dict or pandas Series-like")

def load_pickles():
    global df, indices_obj, tfidf_matrix, tfidf_obj, TITLE_TO_IDX
    import time
    
    start_all = time.perf_counter()
    
    def _timed_load(path, name):
        s = time.perf_counter()
        with open(path, "rb") as f:
            obj = pickle.load(f)
        e = time.perf_counter()
        print(f"DEBUG: Loaded {name} from {os.path.basename(path)} in {e-s:.2f}s")
        return obj

    try:
        df = _timed_load(DF_PATH, "DataFrame")
        indices_obj = _timed_load(INDICES_PATH, "Indices")
        tfidf_matrix = _timed_load(TFIDF_MATRIX_PATH, "TF-IDF Matrix")
        tfidf_obj = _timed_load(TFIDF_PATH, "TF-IDF Vectorizer")
        
        TITLE_TO_IDX = build_title_to_idx_map(indices_obj)
        
        end_all = time.perf_counter()
        print(f"DEBUG: Total Pickle Load Time: {end_all-start_all:.2f}s")
        
        if df is None or "title" not in df.columns:
            raise RuntimeError("df.pkl must contain a DataFrame with a 'title' column")
    except Exception as e:
        print(f"ERROR: Failed to load pickles: {e}")
        raise

def get_local_idx_by_title(title: str) -> int:
    global TITLE_TO_IDX
    if TITLE_TO_IDX is None:
        raise HTTPException(status_code=500, detail="TF-IDF index map not initialized")
    key = _norm_title(title)
    if key in TITLE_TO_IDX:
        return int(TITLE_TO_IDX[key])
    raise HTTPException(
        status_code=404, detail=f"Title not found in local dataset: '{title}'"
    )

def tfidf_recommend_titles(
    query_title: str, top_n: int = 10
) -> List[Tuple[str, float]]:
    global df, tfidf_matrix
    if df is None or tfidf_matrix is None:
        raise HTTPException(status_code=500, detail="TF-IDF resources not loaded")

    idx = get_local_idx_by_title(query_title)

    qv = tfidf_matrix[idx]
    scores = (tfidf_matrix @ qv.T).toarray().ravel()
    order = np.argsort(-scores)

    out: List[Tuple[str, float]] = []
    for i in order:
        if int(i) == int(idx):
            continue
        try:
            title_i = str(df.iloc[int(i)]["title"])
        except Exception:
            continue
        out.append((title_i, float(scores[int(i)])))
        if len(out) >= top_n:
            break
    return out

async def attach_tmdb_card_by_title(title: str) -> Optional[TMDBMovieCard]:
    try:
        m = await tmdb_search_first(title)
        if not m:
            return None
        return TMDBMovieCard(
            tmdb_id=int(m["id"]),
            title=m.get("title") or title,
            poster_url=make_img_url(m.get("poster_path")),
            release_date=m.get("release_date"),
            vote_average=m.get("vote_average"),
        )
    except Exception:
        return None

@router.get("/recommend/tfidf")
async def recommend_tfidf(
    title: str = Query(..., min_length=1),
    top_n: int = Query(10, ge=1, le=50),
):
    recs = tfidf_recommend_titles(title, top_n=top_n)
    return [{"title": t, "score": s} for t, s in recs]

@router.get("/movie/search", response_model=SearchBundleResponse)
async def search_bundle(
    query: str = Query(..., min_length=1),
    tfidf_top_n: int = Query(12, ge=1, le=30),
    genre_limit: int = Query(12, ge=1, le=30),
):
    best = await tmdb_search_first(query)
    if not best:
        raise HTTPException(
            status_code=404, detail=f"No TMDB movie found for query: {query}"
        )

    tmdb_id = int(best["id"])
    details = await tmdb_movie_details(tmdb_id)

    tfidf_items: List[TFIDFRecItem] = []
    recs: List[Tuple[str, float]] = []
    try:
        recs = tfidf_recommend_titles(details.title, top_n=tfidf_top_n)
    except Exception:
        try:
            recs = tfidf_recommend_titles(query, top_n=tfidf_top_n)
        except Exception:
            recs = []

    hybrid_items: List[TFIDFRecItem] = []
    for title, tfidf_score in recs:
        card = await attach_tmdb_card_by_title(title)
        vote_avg = 0.0
        if card and card.tmdb_id:
            try:
                movie_data = await tmdb_get(f"/movie/{card.tmdb_id}", {"language": "en-US"})
                vote_avg = float(movie_data.get("vote_average") or 0.0)
            except Exception:
                vote_avg = 0.0
        hybrid = round(0.60 * tfidf_score + 0.40 * (vote_avg / 10.0), 4)
        hybrid_items.append(TFIDFRecItem(title=title, score=tfidf_score, hybrid_score=hybrid, tmdb=card))

    tfidf_items = sorted(hybrid_items, key=lambda x: x.hybrid_score, reverse=True)

    genre_recs: List[TMDBMovieCard] = []
    if details.genres:
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
        cards = await tmdb_cards_from_results(
            discover.get("results", []), limit=genre_limit
        )
        genre_recs = [c for c in cards if c.tmdb_id != details.tmdb_id]

    return SearchBundleResponse(
        query=query,
        movie_details=details,
        tfidf_recommendations=tfidf_items,
        genre_recommendations=genre_recs,
    )
