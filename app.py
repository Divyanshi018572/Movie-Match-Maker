import requests
import streamlit as st
import os

# =============================
# CONFIG
# =============================
API_BASE = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
TMDB_IMG = "https://image.tmdb.org/t/p/w500"

st.set_page_config(page_title="Movie Match Maker", page_icon="🎬", layout="wide")

# =============================
# STYLES (Premium Streamlit Polish)
# =============================
st.markdown(
    """
<style>
/* Import Premium Font */
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&display=swap');

/* Global Font Override */
html, body, [class*="css"] {
    font-family: 'Outfit', sans-serif !important;
}

/* Deep Space Dark Theme with Gradient */
[data-testid="stAppViewContainer"] {
    background: radial-gradient(circle at top left, #1c103f 0%, #0d0a14 100%);
    color: #f1f1f1 !important;
}

/* Glassmorphism Sidebar */
[data-testid="stSidebar"] {
    background: rgba(20, 15, 30, 0.6) !important;
    backdrop-filter: blur(16px) !important;
    border-right: 1px solid rgba(255,255,255,0.05);
}

/* Spacing config */
.block-container { padding-top: 1.5rem; padding-bottom: 3rem; max-width: 1400px; }

/* Stunning Glassmorphism Cards */
.card {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
    backdrop-filter: blur(10px);
    border-radius: 16px;
    padding: 1.8rem;
    transition: transform 0.3s ease, border-color 0.3s ease;
}
.card:hover {
    transform: translateY(-4px);
    border-color: rgba(255, 255, 255, 0.2);
}

/* Poster Image Micro-Animations */
img {
    border-radius: 12px;
    transition: transform 0.3s cubic-bezier(0.2, 0.8, 0.2, 1), box-shadow 0.3s ease;
}
div[data-testid="stImage"] img:hover {
    transform: scale(1.04);
    box-shadow: 0 12px 24px rgba(0,0,0,0.6);
}

/* Beautiful Typography */
h1, h2, h3, h4, h5 {
    color: #ffffff !important;
    font-weight: 600 !important;
    letter-spacing: -0.5px;
}
.small-muted { color: #8e8e9f; font-size: 0.95rem; margin-top: 4px; }
.movie-title { 
    font-size: 1rem; 
    font-weight: 600;
    line-height: 1.3rem; 
    height: 2.6rem; 
    overflow: hidden; 
    margin-top: 10px;
    color: #e2e2e2;
    transition: color 0.2s ease;
}
.movie-title:hover {
    color: #a374ff;
}

/* Neon Glow Interactive Buttons */
button[kind="secondary"] {
    background: rgba(255, 255, 255, 0.05) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    color: white !important;
    border-radius: 8px !important;
    transition: all 0.3s ease !important;
}
button[kind="secondary"]:hover {
    background: rgba(138, 43, 226, 0.15) !important;
    border: 1px solid rgba(138, 43, 226, 0.5) !important;
    box-shadow: 0 0 15px rgba(138, 43, 226, 0.3) !important;
    transform: translateY(-2px);
}
button[kind="primary"] {
    background: linear-gradient(90deg, #8A2BE2 0%, #4B0082 100%) !important;
    border: none !important;
    color: white !important;
    box-shadow: 0 4px 10px rgba(138,43,226,0.3) !important;
    transition: all 0.3s ease !important;
}
button[kind="primary"]:hover {
    box-shadow: 0 6px 20px rgba(138,43,226,0.6) !important;
    transform: translateY(-2px);
}

/* Hero Section Styles */
.hero-container {
    position: relative;
    width: 100%;
    min-height: 380px;
    border-radius: 24px;
    margin-bottom: 2rem;
    overflow: hidden;
    background-size: cover;
    background-position: center;
    display: flex;
    align-items: flex-end;
    box-shadow: 0 10px 40px rgba(0,0,0,0.5);
}
.hero-overlay {
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: linear-gradient(0deg, rgba(13, 10, 20, 0.95) 0%, rgba(13, 10, 20, 0.2) 60%, rgba(13, 10, 20, 0) 100%);
    z-index: 1;
}
.hero-content {
    position: relative;
    z-index: 2;
    padding: 2.5rem;
    width: 100%;
}
.hero-badge {
    background: rgba(138, 43, 226, 0.2);
    border: 1px solid rgba(138, 43, 226, 0.5);
    color: #c0a0ff;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 1rem;
    display: inline-block;
}
.hero-title {
    font-size: 2.5rem;
    font-weight: 700;
    color: white;
    margin-bottom: 0.5rem;
}
.hero-tagline {
    font-size: 1.1rem;
    color: #d1d1d1;
    max-width: 600px;
}

</style>
""",
    unsafe_allow_html=True,
)

# =============================
# STATE + ROUTING (single-file pages)
# =============================
if "view" not in st.session_state:
    st.session_state.view = "home"  # home | details | watchlist | genre | chat
if "selected_tmdb_id" not in st.session_state:
    st.session_state.selected_tmdb_id = None
if "selected_genre" not in st.session_state:
    st.session_state.selected_genre = "Action"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # [{"role": "user"|"assistant", "content": "..."}]

qp_view = st.query_params.get("view")
qp_id = st.query_params.get("id")
if qp_view in ("home", "details", "watchlist", "genre", "chat"):
    st.session_state.view = qp_view
if qp_id:
    try:
        st.session_state.selected_tmdb_id = int(qp_id)
        st.session_state.view = "details"
    except:
        pass


def goto_home():
    st.session_state.view = "home"
    st.query_params["view"] = "home"
    if "id" in st.query_params:
        del st.query_params["id"]
    st.rerun()


def goto_details(tmdb_id: int):
    st.session_state.view = "details"
    st.session_state.selected_tmdb_id = int(tmdb_id)
    st.query_params["view"] = "details"
    st.query_params["id"] = str(int(tmdb_id))
    st.rerun()


# =============================
# API HELPERS
# =============================
@st.cache_data(ttl=600)  # 10-min cache for heavy TMDB calls - prevents rate limiting
def api_get_json(path: str, params: dict | None = None):
    try:
        r = requests.get(f"{API_BASE}{path}", params=params, timeout=45)
        if r.status_code >= 400:
            return None, f"HTTP {r.status_code}: {r.text[:300]}"
        return r.json(), None
    except Exception as e:
        return None, f"Request failed: {e}"


# No-cache version for live data (watchlist check, search suggestions)
def api_get_live(path: str, params: dict | None = None):
    try:
        r = requests.get(f"{API_BASE}{path}", params=params, timeout=10)
        if r.status_code >= 400:
            return None, f"HTTP {r.status_code}: {r.text[:300]}"
        return r.json(), None
    except Exception as e:
        return None, f"Request failed: {e}"



def poster_grid(cards, cols=6, key_prefix="grid"):
    if not cards:
        st.info("No movies to show.")
        return

    rows = (len(cards) + cols - 1) // cols
    idx = 0
    for r in range(rows):
        colset = st.columns(cols)
        for c in range(cols):
            if idx >= len(cards):
                break
            m = cards[idx]
            idx += 1

            tmdb_id = m.get("tmdb_id")
            title = m.get("title", "Untitled")
            poster = m.get("poster_url")

            with colset[c]:
                if poster:
                    st.image(poster, use_column_width=True)
                else:
                    st.write("🖼️ No poster")

                if st.button("Open", key=f"{key_prefix}_{r}_{c}_{idx}_{tmdb_id}"):
                    if tmdb_id:
                        goto_details(tmdb_id)

                st.markdown(
                    f"<div class='movie-title'>{title}</div>", unsafe_allow_html=True
                )


def to_cards_from_tfidf_items(tfidf_items):
    cards = []
    for x in tfidf_items or []:
        tmdb = x.get("tmdb") or {}
        if tmdb.get("tmdb_id"):
            hybrid = x.get("hybrid_score") or x.get("score") or 0
            cards.append(
                {
                    "tmdb_id": tmdb["tmdb_id"],
                    "title": tmdb.get("title") or x.get("title") or "Untitled",
                    "poster_url": tmdb.get("poster_url"),
                    "hybrid_score": hybrid,
                }
            )
    return cards


# =============================
# IMPORTANT: Robust TMDB search parsing
# Supports BOTH API shapes:
# 1) raw TMDB: {"results":[{id,title,poster_path,...}]}
# 2) list cards: [{tmdb_id,title,poster_url,...}]
# =============================
def parse_tmdb_search_to_cards(data, keyword: str, limit: int = 24):
    """
    Returns:
      suggestions: list[(label, tmdb_id)]
      cards: list[{tmdb_id,title,poster_url}]
    """
    keyword_l = keyword.strip().lower()

    # A) If API returns dict with 'results'
    if isinstance(data, dict) and "results" in data:
        raw = data.get("results") or []
        raw_items = []
        for m in raw:
            title = (m.get("title") or "").strip()
            tmdb_id = m.get("id")
            poster_path = m.get("poster_path")
            if not title or not tmdb_id:
                continue
            raw_items.append(
                {
                    "tmdb_id": int(tmdb_id),
                    "title": title,
                    "poster_url": f"{TMDB_IMG}{poster_path}" if poster_path else None,
                    "release_date": m.get("release_date", ""),
                }
            )

    # B) If API returns already as list
    elif isinstance(data, list):
        raw_items = []
        for m in data:
            # might be {tmdb_id,title,poster_url}
            tmdb_id = m.get("tmdb_id") or m.get("id")
            title = (m.get("title") or "").strip()
            poster_url = m.get("poster_url")
            if not title or not tmdb_id:
                continue
            raw_items.append(
                {
                    "tmdb_id": int(tmdb_id),
                    "title": title,
                    "poster_url": poster_url,
                    "release_date": m.get("release_date", ""),
                }
            )
    else:
        return [], []

    # Word-match filtering (contains)
    matched = [x for x in raw_items if keyword_l in x["title"].lower()]

    # If nothing matched, fallback to raw list (so never blank)
    final_list = matched if matched else raw_items

    # Suggestions = top 10 labels
    suggestions = []
    for x in final_list[:10]:
        year = (x.get("release_date") or "")[:4]
        label = f"{x['title']} ({year})" if year else x["title"]
        suggestions.append((label, x["tmdb_id"]))

    # Cards = top N
    cards = [
        {"tmdb_id": x["tmdb_id"], "title": x["title"], "poster_url": x["poster_url"]}
        for x in final_list[:limit]
    ]
    return suggestions, cards


# =============================
# SIDEBAR (clean)
# =============================
with st.sidebar:
    st.markdown("## 🎬 Menu")
    if st.button("🏠 Home"):
        goto_home()
    if st.button("🗂️ My Watchlist"):
        st.session_state.view = "watchlist"
        st.rerun()
    if st.button("🎭 Browse by Genre"):
        st.session_state.view = "genre"
        st.rerun()
    if st.button("🤖 AI Movie Chat"):
        st.session_state.view = "chat"
        st.rerun()

    st.markdown("---")
    st.markdown("### 🏠 Home Feed (only home)")
    home_category = st.selectbox(
        "Category",
        ["trending", "popular", "top_rated", "now_playing", "upcoming"],
        index=0,
    )
    grid_cols = st.slider("Grid columns", 4, 8, 6)

# =============================
# HEADER
# =============================
st.title("🎬 Movie Match Maker")
# HERO SECTION REMOVAL: Moving header content into hero banner below.
st.divider()

# ==========================================================
# VIEW: HOME
# ==========================================================
if st.session_state.view == "home":
    # --- HERO AREA ---
    # Try a faster, non-caching call for the hero so we don't hold up the page
    try:
        hero_data, h_err = api_get_live("/home", params={"category": "trending", "limit": 1})
    except Exception:
        hero_data, h_err = None, "Timeout"

    if h_err is None and hero_data:
        hero = hero_data[0]
        # Use high-res backdrop if available, fallback to poster
        bg_url = hero.get("backdrop_url") or hero.get("poster_url") or "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba"
        st.markdown(f"""
            <div class="hero-container" style="background-image: url('{bg_url}');">
                <div class="hero-overlay"></div>
                <div class="hero-content">
                    <span class="hero-badge">✨ Featured Match of the Day</span>
                    <div class="hero-title">{hero.get('title', 'Your Next Favorite Movie')}</div>
                    <div class="hero-tagline">Trending now with a {hero.get('vote_average', '8.0')}/10 rating. Discover why this movie is matching with millions!</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    typed = st.text_input(
        "Search by movie title (keyword)", placeholder="Type: avenger, batman, love..."
    )

    # ===  CONVERSATIONAL AI SEARCH ===
    with st.expander("🗣️ Describe what you want to watch (AI Search)"):
        conv_query = st.text_area(
            "Natural language search",
            placeholder="e.g. 'A funny movie for kids from the 2010s' or 'Scary thriller from the 90s rated above 7'",
            key="conv_query", height=80, label_visibility="collapsed"
        )
        if st.button("🔍 Search with AI", key="conv_search_btn") and conv_query.strip():
            with st.spinner("🤖 AI is understanding your request..."):
                ai_resp = requests.post(f"{API_BASE}/ai/search", json={"query": conv_query.strip()}, timeout=20)
            if ai_resp.status_code == 200:
                ai_data = ai_resp.json()
                st.caption(f"🤖 AI understood: *{ai_data.get('description', '')}*")
                col_a, col_b, col_c = st.columns(3)
                col_a.metric("🎬 Genre", ai_data.get('genre') or 'Any')
                col_b.metric("📅 Years", f"{ai_data.get('year_from', 1990)}–{ai_data.get('year_to', 2025)}")
                col_c.metric("⭐ Min Rating", ai_data.get('min_rating', 5.0))
                # Fetch results using extracted filters
                if ai_data.get('genre'):
                    res_data, res_err = api_get_json("/discover/genre", params={
                        "genre": ai_data['genre'],
                        "year_from": ai_data.get('year_from', 1990),
                        "year_to": ai_data.get('year_to', 2025),
                        "min_rating": ai_data.get('min_rating', 5.0),
                    })
                    if not res_err and res_data and res_data.get('results'):
                        st.markdown(f"### 🎯 AI Results — {ai_data.get('genre')} Movies")
                        poster_grid(res_data['results'], cols=grid_cols, key_prefix="ai_search")
                    else:
                        st.info("No results found. Try rephrasing your request.")
                else:
                    st.info("AI couldn't detect a genre. Try being more specific, e.g. 'action movies from 2020'.")
            else:
                st.error("AI Search failed. Please try again.")

    st.divider()

    # SEARCH MODE (Autocomplete + word-match results)
    if typed.strip():
        if len(typed.strip()) < 2:
            st.caption("Type at least 2 characters for suggestions.")
        else:
            data, err = api_get_json("/tmdb/search", params={"query": typed.strip()})

            if err or data is None:
                st.error(f"Search failed: {err}")
            else:
                suggestions, cards = parse_tmdb_search_to_cards(
                    data, typed.strip(), limit=24
                )

                # Dropdown
                if suggestions:
                    labels = ["-- Select a movie --"] + [s[0] for s in suggestions]
                    selected = st.selectbox("Suggestions", labels, index=0)

                    if selected != "-- Select a movie --":
                        # map label -> id
                        label_to_id = {s[0]: s[1] for s in suggestions}
                        goto_details(label_to_id[selected])
                else:
                    st.info("No suggestions found. Try another keyword.")

                st.markdown("### Results")
                poster_grid(cards, cols=grid_cols, key_prefix="search_results")

        st.stop()

    # HOME FEED MODE
    st.markdown(f"### 🏠 Home — {home_category.replace('_',' ').title()}")

    home_cards, err = api_get_json(
        "/home", params={"category": home_category, "limit": 24}
    )
    if err or not home_cards:
        st.error(f"Home feed failed: {err or 'Unknown error'}")
        st.stop()

    poster_grid(home_cards, cols=grid_cols, key_prefix="home_feed")

# ==========================================================
# VIEW: DETAILS
# ==========================================================
elif st.session_state.view == "details":
    tmdb_id = st.session_state.selected_tmdb_id
    if not tmdb_id:
        st.warning("No movie selected.")
        if st.button("← Back to Home"):
            goto_home()
        st.stop()

    # Top bar
    a, b = st.columns([3, 1])
    with a:
        st.markdown("### 📄 Movie Details")
    with b:
        if st.button("← Back to Home"):
            goto_home()

    # Watchlist Toggle
    wl_check, _ = api_get_live(f"/watchlist/{tmdb_id}")
    is_saved = (wl_check or {}).get("saved", False)
    col_wl, col_rate = st.columns([1, 2])
    with col_wl:
        if is_saved:
            if st.button("❤️ Saved to Watchlist — Click to Remove"):
                requests.delete(f"{API_BASE}/watchlist/{tmdb_id}")
                st.rerun()
        else:
            if st.button("➕ Add to Watchlist"):
                movie_data, _ = api_get_json(f"/movie/id/{tmdb_id}")
                if movie_data:
                    requests.post(f"{API_BASE}/watchlist", json={
                        "tmdb_id": tmdb_id,
                        "title": movie_data.get("title", ""),
                        "poster_url": movie_data.get("poster_url", "")
                    })
                st.rerun()

    with col_rate:
        rating_data, _ = api_get_live(f"/ratings/{tmdb_id}")
        current_rating = (rating_data or {}).get("rating") or 0
        star_map = {"⭐ 1 — Poor": 1, "⭐⭐ 2 — Fair": 2, "⭐⭐⭐ 3 — Good": 3, "⭐⭐⭐⭐ 4 — Great": 4, "⭐⭐⭐⭐⭐ 5 — Excellent": 5}
        labels = ["(no rating yet)"] + list(star_map.keys())
        current_label = next((k for k, v in star_map.items() if v == current_rating), "(no rating yet)")
        chosen = st.selectbox("🌟 Your Rating", labels, index=labels.index(current_label), key=f"rate_{tmdb_id}")
        if chosen != "(no rating yet)" and star_map[chosen] != current_rating:
            movie_title = (api_get_json(f"/movie/id/{tmdb_id}")[0] or {}).get("title", "")
            requests.post(f"{API_BASE}/ratings", json={"tmdb_id": tmdb_id, "title": movie_title, "rating": star_map[chosen]})
            st.rerun()

    # Details (your FastAPI safe route)
    data, err = api_get_json(f"/movie/id/{tmdb_id}")
    if err or not data:
        st.error(f"Could not load details: {err or 'Unknown error'}")
        st.stop()

    # Layout: Poster LEFT, Details RIGHT
    left, right = st.columns([1, 2.4], gap="large")

    with left:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        if data.get("poster_url"):
            st.image(data["poster_url"], use_column_width=True)
        else:
            st.write("🖼️ No poster")
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown(f"## {data.get('title','')}")
        release = data.get("release_date") or "-"
        genres = ", ".join([g["name"] for g in data.get("genres", [])]) or "-"
        st.markdown(
            f"<div class='small-muted'>Release: {release}</div>", unsafe_allow_html=True
        )
        st.markdown(
            f"<div class='small-muted'>Genres: {genres}</div>", unsafe_allow_html=True
        )
        st.markdown("---")
        
        col_data = data.get("collection")
        if col_data:
            st.info(f"✨ **Part of the {col_data.get('name')}**")
            
        st.markdown("### Overview")
        st.write(data.get("overview") or "No overview available.")
        st.markdown("</div>", unsafe_allow_html=True)

    if data.get("backdrop_url"):
        st.markdown("#### Backdrop")
        st.image(data["backdrop_url"], use_column_width=True)

    if data.get("trailer_youtube_id"):
        st.markdown("#### 🎥 Trailer")
        st.video(f"https://www.youtube.com/watch?v={data['trailer_youtube_id']}")

    providers = data.get("watch_providers", [])
    watch_link = data.get("watch_link", "")

    if providers:
        if watch_link:
            st.markdown(f"#### 📺 [Where to Watch (US)]({watch_link})")
        else:
            st.markdown("#### 📺 Where to Watch (US)")
        
        cols = st.columns(len(providers) + 12) # padding columns so they stay small
        for i, p in enumerate(providers):
            with cols[i]:
                if watch_link:
                    st.markdown(f"""
                    <a href="{watch_link}" target="_blank">
                        <img src="{p.get('logo_url')}" width="40" style="border-radius:10px;" title="Watch on {p.get('name')}">
                    </a><br><small style="color:gray;">{p.get('name')}</small>
                    """, unsafe_allow_html=True)
                else:
                    st.image(p.get("logo_url"), width=40, caption=p.get("name"))

    reviews = data.get("reviews", [])
    if reviews:
        st.write("") # small spacer
        with st.expander("📝 Read User Reviews"):
            for r in reviews:
                st.markdown(f"**{r['author']}**")
                content = r['content']
                if len(content) > 600:
                    content = content[:600] + "..." # Truncate massive reviews
                st.markdown(f"> *{content}*")
                if r.get("url"):
                    st.markdown(f"[Read full review]({r['url']})")
                st.markdown("---")

    # === AI MOVIE SUMMARY ===
    with st.expander("✨ Get AI Movie Summary (Powered by Groq)"):
        ai_sum_key = f"ai_summary_{tmdb_id}"
        if ai_sum_key not in st.session_state:
            st.session_state[ai_sum_key] = None
        if st.button("🤖 Generate AI Summary", key=f"sum_btn_{tmdb_id}"):
            with st.spinner("Writing your personalized movie summary..."):
                sum_resp = requests.post(f"{API_BASE}/ai/summary", json={
                    "title": data.get('title', ''),
                    "overview": data.get('overview', ''),
                    "genres": [g['name'] for g in data.get('genres', [])],
                    "release_date": data.get('release_date', ''),
                    "vote_average": data.get('vote_average', 0),
                }, timeout=20)
            if sum_resp.status_code == 200:
                st.session_state[ai_sum_key] = sum_resp.json().get('summary', '')
            else:
                st.error("Could not generate summary. Try again.")
        if st.session_state.get(ai_sum_key):
            st.info(f"🎬 {st.session_state[ai_sum_key]}")

    st.divider()
    st.markdown("### ✅ Recommendations")

    # Recommendations (TF-IDF + Genre) via your bundle endpoint
    title = (data.get("title") or "").strip()
    if title:
        bundle, err2 = api_get_json(
            "/movie/search",
            params={"query": title, "tfidf_top_n": 12, "genre_limit": 12},
        )

        if not err2 and bundle:
            st.markdown("#### 🔎 Similar Movies (TF-IDF)")
            poster_grid(
                to_cards_from_tfidf_items(bundle.get("tfidf_recommendations")),
                cols=grid_cols,
                key_prefix="details_tfidf",
            )

            st.markdown("#### 🎭 More Like This (Genre)")
            poster_grid(
                bundle.get("genre_recommendations", []),
                cols=grid_cols,
                key_prefix="details_genre",
            )
        else:
            st.info("Showing Genre recommendations (fallback).")
            genre_only, err3 = api_get_json(
                "/recommend/genre", params={"tmdb_id": tmdb_id, "limit": 18}
            )
            if not err3 and genre_only:
                poster_grid(
                    genre_only, cols=grid_cols, key_prefix="details_genre_fallback"
                )
            else:
                st.warning("No recommendations available right now.")
    else:
        st.warning("No title available to compute recommendations.")

# ==========================================================
# VIEW: WATCHLIST
# ==========================================================
elif st.session_state.view == "watchlist":
    st.title("🗂️ My Watchlist")
    if st.button("← Back to Home"):
        goto_home()

    # === AI WATCHLIST ANALYZER ===
    col_wl_hdr, col_wl_btn = st.columns([3, 1])
    with col_wl_btn:
        analyze_clicked = st.button("🧠 Analyze My Taste", use_container_width=True)
    if analyze_clicked:
        with st.spinner("🤖 AI is analyzing your movie taste..."):
            ana_resp = requests.get(f"{API_BASE}/ai/watchlist-analysis", timeout=30)
        if ana_resp.status_code == 200:
            ana_data = ana_resp.json()
            st.session_state['wl_analysis'] = ana_data.get('analysis', '')
            st.session_state['wl_count'] = ana_data.get('movie_count', 0)
        else:
            st.error("Analysis failed. Make sure you have movies in your watchlist.")
    if st.session_state.get('wl_analysis'):
        st.markdown(st.session_state['wl_analysis'])
        st.divider()

    wl_data, wl_err = api_get_live("/watchlist")
    if wl_err:
        st.error(f"Could not load watchlist: {wl_err}")
    elif not wl_data:
        st.info("Your watchlist is empty! Go browse movies and click ➕ Add to Watchlist.")
    else:
        st.caption(f"{len(wl_data)} saved movies")
        cards = [
            {
                "tmdb_id": m["tmdb_id"],
                "title": m["title"],
                "poster_url": m.get("poster_url")
            }
            for m in wl_data
        ]
        poster_grid(cards, cols=grid_cols, key_prefix="watchlist")

# ==========================================================
# VIEW: GENRE BROWSER (Advanced Search & Filtering)
# ==========================================================
elif st.session_state.view == "genre":
    GENRES = [
        "Action", "Adventure", "Animation", "Comedy", "Crime",
        "Documentary", "Drama", "Family", "Fantasy", "History",
        "Horror", "Music", "Mystery", "Romance", "Science Fiction",
        "Thriller", "War", "Western"
    ]

    st.title("🎭 Advanced Search & Filtering")
    if st.button("← Back to Home"):
        goto_home()
    st.divider()

    # === FILTER ROW ===
    col1, col2, col3 = st.columns([1.5, 2, 1.5])

    with col1:
        selected_genre = st.selectbox(
            "🎬 Genre",
            GENRES,
            index=GENRES.index(st.session_state.selected_genre) if st.session_state.selected_genre in GENRES else 0,
            key="genre_selectbox"
        )
        st.session_state.selected_genre = selected_genre

    with col2:
        year_range = st.slider(
            "📅 Release Year Range",
            min_value=1970, max_value=2025,
            value=(2000, 2025), step=1
        )

    with col3:
        min_rating = st.slider(
            "⭐ Min TMDB Rating",
            min_value=0.0, max_value=9.0,
            value=5.0, step=0.5
        )

    genre_page = st.number_input("Page", min_value=1, max_value=20, value=1, step=1)
    st.markdown(f"### 🎬 {selected_genre} Movies ({year_range[0]}–{year_range[1]}, Rating ≥ {min_rating})")

    genre_data, err = api_get_json(
        "/discover/genre",
        params={
            "genre": selected_genre,
            "page": int(genre_page),
            "year_from": year_range[0],
            "year_to": year_range[1],
            "min_rating": min_rating,
        }
    )

    if err:
        st.error(f"Could not load results: {err}")
    elif not genre_data or not genre_data.get("results"):
        st.info(f"No movies found matching your filters. Try adjusting the year range or rating.")
    else:
        results = genre_data["results"]
        st.caption(f"Showing {len(results)} movies")
        poster_grid(results, cols=grid_cols, key_prefix=f"genre_{selected_genre}_{genre_page}_{year_range}_{min_rating}")


# ==========================================================
# VIEW: AI MOVIE CHAT
# ==========================================================
elif st.session_state.view == "chat":
    st.title("🤖 CineBot — AI Movie Assistant")
    st.markdown("<div class='small-muted'>Powered by Grok · Ask me anything about movies!</div>", unsafe_allow_html=True)
    if st.button("← Back to Home"):
        goto_home()
    st.divider()

    # Render existing chat history
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.markdown(msg["content"])
        else:
            with st.chat_message("assistant", avatar="🎬"):
                st.markdown(msg["content"])

    # Chat input
    user_input = st.chat_input("Ask me about movies... (e.g. 'Suggest a scary movie for tonight')") 
    if user_input:
        # Show user message immediately
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.chat_history.append({"role": "user", "content": user_input})

        # Call backend
        with st.chat_message("assistant", avatar="🎬"):
            with st.spinner("CineBot is thinking..."):
                try:
                    resp = requests.post(
                        f"{API_BASE}/chat",
                        json={
                            "message": user_input,
                            "history": st.session_state.chat_history[:-1]  # exclude current msg
                        },
                        timeout=30
                    )
                    if resp.status_code == 200:
                        reply = resp.json().get("reply", "Sorry, I couldn't process that.")
                    else:
                        reply = f"⚠️ Error: {resp.text[:200]}"
                except Exception as e:
                    reply = f"⚠️ Connection error: {e}"
                st.markdown(reply)

        st.session_state.chat_history.append({"role": "assistant", "content": reply})

    # Clear button
    if st.session_state.chat_history:
        if st.button("🗑️ Clear Chat History"):
            st.session_state.chat_history = []
            st.rerun()


