import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import core.db
from routers.tmdb_routes import router as tmdb_router
from routers.db_routes import router as db_router
from routers.rec_routes import router as rec_router
from routers.ai_routes import router as ai_router

app = FastAPI(title="Movie Match Maker API", version="3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(tmdb_router)
app.include_router(db_router)
app.include_router(rec_router)
app.include_router(ai_router)
