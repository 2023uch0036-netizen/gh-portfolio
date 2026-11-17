from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from .db import init_db
from .routers import profile

app = FastAPI(title="GitHub Developer Portfolio")
init_db()
app.include_router(profile.router)

FRONTEND = Path(__file__).resolve().parents[2] / "frontend"
app.mount("/", StaticFiles(directory=FRONTEND, html=True), name="frontend")s