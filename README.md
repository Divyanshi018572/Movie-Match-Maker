---
title: Movie Match Maker
emoji: 🎬
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
---
# 🎬 Movie Match Maker

**Movie Match Maker** is a premium, AI-powered film discovery platform that blends traditional data-driven recommendations with cutting-edge LLM reasoning. Whether you're looking for a specific hidden gem or just want to chat about cinema, Movie Match Maker is your ultimate film companion.

---

## ✨ Key Features

### 🤖 CineBot AI Assistant
A hilarious, movie-obsessed AI personality powered by **Llama 3 (via Groq)**. CineBot doesn't just chat; it uses agentic tool-calling to search the live TMDB database for real-time recommendations.

### 🧠 Hybrid Recommendation Engine
- **TF-IDF Core**: A custom-trained machine learning model that analyzes movie descriptions to find deeper content-based matches.
- **TMDB Integration**: Live data for trending, popular, and upcoming movies, including trailers and streaming providers (US).

### 🗣️ Conversational AI Search
Forget rigid filters. Type "Suggest a colorful sci-fi movie from the 80s with a high rating," and the AI understands your intent, filters the parameters, and surfaces the best matches.

### 🧬 Cinematic DNA (Watchlist Analysis)
Save movies to your watchlist and let the AI psychoanalyze your taste! Get a personalized "Cinematic DNA" profile and hand-picked treats based on your history.

---

## 🛠️ Technology Stack

- **Backend**: [FastAPI](https://fastapi.tiangolo.com/) (Modular Architecture)
- **Frontend**: [Streamlit](https://streamlit.io/) (Premium Glassmorphism Design)
- **AI/LLM**: [Groq Cloud](https://groq.com/) (Llama 3.3 70B Versatile)
- **Database**: SQLite3
- **Data Science**: Pandas, Scikit-learn, Numpy
- **API**: [TMDB (The Movie Database)](https://www.themoviedb.org/)

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.9+
- A TMDB API Key
- A Groq API Key

### 2. Installation
Clone the repository and install the dependencies:
```bash
pip install -r requirements.txt
```

### 3. Environment Variables
Create a `.env` file in the root directory:
```env
TMDB_API_KEY=your_tmdb_api_key
TMDB_ACCESS_TOKEN=your_tmdb_access_token
GROQ_API_KEY=your_groq_api_key
```

### 4. Running the Application
You need to run both the FastAPI backend and the Streamlit frontend.

**Start the Backend:**
```bash
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

**Start the Frontend:**
```bash
streamlit run app.py
```

---

## 🎨 Professional Design
The UI features an enterprise-grade "Deep Space" theme with:
- **Glassmorphism**: Frosted glass sidebars and cards.
- **Frosted Hero Banner**: A dynamic trending header that changes based on top movies.
- **Micro-Animations**: Smooth hover transitions and neon glow interactive elements.

---

## 📂 Project Structure
```text
├── core/               # Shared logic, database, and config
├── routers/            # Feature-specific API endpoints
├── main.py             # FastAPI entry point
├── app.py              # Streamlit frontend
├── movies.db           # Persistent SQLite storage
└── requirements.txt    # Project dependencies
```

*Enjoy your cinematic journey with **Movie Match Maker**!* 🍿🎬
