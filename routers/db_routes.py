import sqlite3
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.db import DB_PATH

router = APIRouter()

class WatchlistItem(BaseModel):
    tmdb_id: int
    title: str
    poster_url: Optional[str] = None

@router.post("/watchlist")
def add_to_watchlist(item: WatchlistItem):
    with sqlite3.connect(DB_PATH) as conn:
        try:
            conn.execute(
                "INSERT INTO watchlist (tmdb_id, title, poster_url) VALUES (?, ?, ?)",
                (item.tmdb_id, item.title, item.poster_url)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            pass
    return {"status": "ok"}

@router.delete("/watchlist/{tmdb_id}")
def remove_from_watchlist(tmdb_id: int):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM watchlist WHERE tmdb_id = ?", (tmdb_id,))
        conn.commit()
    return {"status": "ok"}

@router.get("/watchlist/{tmdb_id}")
def check_watchlist(tmdb_id: int):
    with sqlite3.connect(DB_PATH) as conn:
        res = conn.execute("SELECT 1 FROM watchlist WHERE tmdb_id = ?", (tmdb_id,)).fetchone()
        return {"saved": bool(res)}

@router.get("/watchlist")
def get_watchlist():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM watchlist ORDER BY added_at DESC").fetchall()
        return [dict(r) for r in rows]

class RatingItem(BaseModel):
    tmdb_id: int
    title: str
    rating: int

@router.post("/ratings")
def submit_rating(item: RatingItem):
    if not 1 <= item.rating <= 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO ratings (tmdb_id, title, rating) VALUES (?, ?, ?) "
            "ON CONFLICT(tmdb_id) DO UPDATE SET rating=excluded.rating, rated_at=CURRENT_TIMESTAMP",
            (item.tmdb_id, item.title, item.rating)
        )
        conn.commit()
    return {"status": "ok"}

@router.get("/ratings/{tmdb_id}")
def get_rating(tmdb_id: int):
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT rating FROM ratings WHERE tmdb_id = ?", (tmdb_id,)
        ).fetchone()
        return {"rating": row[0] if row else None}
