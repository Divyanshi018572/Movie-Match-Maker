import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "movies.db")

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS watchlist (
                tmdb_id INTEGER PRIMARY KEY,
                title TEXT,
                poster_url TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS ratings (
                tmdb_id INTEGER PRIMARY KEY,
                title TEXT,
                rating INTEGER CHECK(rating BETWEEN 1 AND 5),
                rated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

init_db()
