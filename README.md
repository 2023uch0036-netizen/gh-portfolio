Architecture diagram. Browser -> FastAPI router -> services (cache / stats / match / assistant) -> SQLite and GitHub API.
API table of the five endpoints.
Caching strategy. A TTL of CACHE_TTL_MINUTES, ?refresh=true to bypass it, and a note that GitHub's rate limit is 60/hr unauthenticated vs 5000/hr with a token.
Match algorithm. A 70% coverage and 30% depth formula, with a note that all logic is server-side.
Extra features. Ask My Portfolio and the AI Pitch Generator, with a note on the fallback when no API key is set.