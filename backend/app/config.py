import os
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CACHE_TTL_MINUTES = int(os.getenv("CACHE_TTL_MINUTES", "60"))
DB_PATH = os.getenv("DB_PATH", "portfolio.db")