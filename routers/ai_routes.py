import json as _json
import sqlite3
from typing import Optional, List
from fastapi import APIRouter, HTTPException
from openai import OpenAI as GroqClient

from core.db import DB_PATH
from core.config import GROQ_API_KEY
from core.models import ChatRequest, SummaryRequest, ConvSearchRequest
from core.utils import tmdb_get
from routers.tmdb_routes import TMDB_GENRES

router = APIRouter()

CINEBOT_SYSTEM_PROMPT = """You are CineBot 🍿😎, the ultimate AI movie buff, built directly into the user's Movie Match Maker app!

Your personality: You are energetic, incredibly friendly, hilarious, and maybe just a little too obsessed with movies. You love making film-related puns and jokes. You speak to the user like they are your best friend coming over for movie night. 

When recommending movies, ALWAYS format your response like this:
🍿 **[Movie Title] ([Year])** — [Genre]
> 🤩 Why you'll love it: [1-2 sentence passionate, funny reason tailored to the user's request]
⭐ TMDB Rating: X.X/10

Give 3-5 recommendations per response (unless asked otherwise).

Additional rules:
- Drown your text in fun emojis! 🎥🍿🤪🤯✨🎉
- Make a movie-related joke or pun in almost every response.
- If the user asks about a specific movie, hype it up (or roast it if it’s famously bad), and give them all the juicy details.
- Always end your message with a playful, movie-themed question to keep the chat rolling! (e.g. "Got the popcorn ready, or should we keep looking?")
- Stay in character 100%. If they ask about non-movie stuff, make a joke about how your programming matrix only understands cinema. 🎬"""

CINEBOT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_tmdb_movies",
            "description": "Search the TMDB database for movies either by a specific title (query) OR by genre and release year. Call this tool whenever the user asks for specific movie recommendations or parameters.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The exact movie title to search for (e.g. 'Inception'). Use this if searching a specific movie by name."
                    },
                    "genre_name": {
                        "type": "string",
                        "description": "The name of the genre to filter by (e.g. 'Action', 'Comedy', 'Horror', 'Science Fiction')."
                    },
                    "year_from": {
                        "type": "integer",
                        "description": "Start release year filter (e.g. 2010)."
                    },
                    "year_to": {
                        "type": "integer",
                        "description": "End release year filter (e.g. 2020)."
                    },
                    "min_rating": {
                        "type": "number",
                        "description": "Minimum TMDB rating from 0.0 to 10.0 (e.g. 7.5)."
                    }
                }
            }
        }
    }
]

@router.post("/chat")
async def movie_chat(req: ChatRequest):
    if not GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not configured in .env")
    try:
        client = GroqClient(
            api_key=GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
        )
        messages = [{"role": "system", "content": CINEBOT_SYSTEM_PROMPT}]
        messages.extend(req.history[-10:])
        messages.append({"role": "user", "content": req.message})

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            tools=CINEBOT_TOOLS,
            tool_choice="auto",
            max_tokens=600,
            temperature=0.7,
        )
        
        response_message = response.choices[0].message
        
        if response_message.tool_calls:
            messages.append(response_message.model_dump())
            
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args = _json.loads(tool_call.function.arguments)
                
                if function_name == "search_tmdb_movies":
                    tool_result_str = "No movies found."
                    query = function_args.get("query")
                    
                    if query:
                        data = await tmdb_get("/search/movie", {"query": query, "page": 1})
                        results = data.get("results", [])[:5]
                    else:
                        params = {"page": 1, "sort_by": "popularity.desc", "vote_count.gte": 100}
                        g_name = function_args.get("genre_name")
                        if g_name and g_name in TMDB_GENRES:
                            params["with_genres"] = TMDB_GENRES[g_name]
                        if function_args.get("year_from"):
                            params["primary_release_date.gte"] = f"{function_args['year_from']}-01-01"
                        if function_args.get("year_to"):
                            params["primary_release_date.lte"] = f"{function_args['year_to']}-12-31"
                        if function_args.get("min_rating"):
                            params["vote_average.gte"] = function_args['min_rating']
                            
                        data = await tmdb_get("/discover/movie", params)
                        results = data.get("results", [])[:5]
                    
                    if results:
                        simplified_results = [
                            {"title": r.get("title"), "year": str(r.get("release_date"))[:4] if r.get("release_date") else "N/A", "rating": r.get("vote_average"), "overview": r.get("overview")}
                            for r in results
                        ]
                        tool_result_str = _json.dumps(simplified_results)

                    messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": tool_result_str,
                    })
            
            second_response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                max_tokens=600,
                temperature=0.7,
            )
            reply = second_response.choices[0].message.content
        else:
            reply = response_message.content

        return {"reply": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CineBot error: {repr(e)}")


def groq_ask(prompt: str, max_tokens: int = 500, temperature: float = 0.7) -> str:
    if not GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not configured")
    client = GroqClient(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return response.choices[0].message.content.strip()


@router.post("/ai/summary")
def ai_movie_summary(req: SummaryRequest):
    try:
        genre_str = ", ".join(req.genres) if req.genres else "Unknown"
        prompt = f"""You are CineBot 🍿😎, a hilarious and super enthusiastic film buff. Write a short, punchy, 3-sentence summary trying to hype up this movie to a friend!
Focus on: Who will love it, the crazy emotional rollercoaster they are in for, and maybe slip a tiny movie pun or joke in there. Lots of emojis! 🤩🔥

Movie: {req.title} ({req.release_date[:4] if req.release_date else 'N/A'})
Genre: {genre_str}
TMDB Rating: {req.vote_average}/10
Plot: {req.overview or 'Not available'}

Write ONLY the 3-sentence summary. No headers, no bullet points. Go!"""
        summary = groq_ask(prompt, max_tokens=200, temperature=0.8)
        return {"summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Summary error: {repr(e)}")


@router.post("/ai/search")
def ai_conversational_search(req: ConvSearchRequest):
    try:
        prompt = f"""You are a movie search assistant. Extract search intent from the user's natural language query.
Return ONLY a valid JSON object (no explanation, no markdown) with these exact keys:
- "keyword": main movie keyword/title to search (string, can be empty)
- "genre": one of [Action, Adventure, Animation, Comedy, Crime, Documentary, Drama, Family, Fantasy, History, Horror, Music, Mystery, Romance, Science Fiction, Thriller, War, Western] or empty string
- "year_from": integer start year (default 1990)
- "year_to": integer end year (default 2025)
- "min_rating": float 0.0-9.0 (default 5.0)
- "description": 1 short sentence describing what you understood (for showing to user)

User query: "{req.query}"

Respond with ONLY the JSON object:"""
        raw = groq_ask(prompt, max_tokens=200, temperature=0.2)
        start = raw.find("{")
        end = raw.rfind("}") + 1
        parsed = _json.loads(raw[start:end])
        return parsed
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Search error: {repr(e)}")


@router.get("/ai/watchlist-analysis")
def ai_watchlist_analysis():
    if not GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not configured")
    try:
        with sqlite3.connect(DB_PATH) as conn:
            rows = conn.execute("SELECT title FROM watchlist ORDER BY added_at DESC").fetchall()
        if not rows:
            return {"profile": "Your watchlist is empty! Start saving movies to get a taste analysis.", "recommendations": []}

        titles = [r[0] for r in rows]
        titles_str = "\n".join(f"- {t}" for t in titles[:30])  # max 30 for token limit

        prompt = f"""You are CineBot 🎬🤖, a witty, fun, and highly energetic movie psychoanalyst! Analyze this person's watchlist and roast/praise their movie taste with lots of humor and emojis!

Their saved movies:
{titles_str}

Write your response in this EXACT format:
**🧬 Your Cinematic DNA:**
[2-3 hilarious, highly energetic sentences diagnosing their movie taste. Give their taste a funny made-up name (e.g. "Chronic Action Junkie" or "Hopeless Romantic with a dark side"). Use emojis!]

**🎁 My Hand-Picked Treats For You:**
1. 🎬 **[Movie Title] (Year)** — [One funny/exciting sentence why this is exactly their jam]
2. 🎬 **[Movie Title] (Year)** — [One funny/exciting sentence why they'll love it]
3. 🎬 **[Movie Title] (Year)** — [One funny/exciting sentence why they need to watch it tonight]

**💡 CineBot's Hot Take:**
[One funny observation, roast, or quirky insight about their watchlist]"""

        analysis = groq_ask(prompt, max_tokens=500, temperature=0.7)
        return {"analysis": analysis, "movie_count": len(titles)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Watchlist Analysis error: {repr(e)}")
