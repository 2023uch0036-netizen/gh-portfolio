import sqlite3
from contextlib import contextmanager
from .config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    name TEXT, avatar_url TEXT, bio TEXT,
    followers INTEGER DEFAULT 0, following INTEGER DEFAULT 0,
    public_repos INTEGER DEFAULT 0, html_url TEXT,
    fetched_at TEXT
);
CREATE TABLE IF NOT EXISTS repos (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL,
    name TEXT, description TEXT, language TEXT,
    stars INTEGER DEFAULT 0, forks INTEGER DEFAULT 0,
    html_url TEXT, is_fork INTEGER DEFAULT 0,
    updated_at TEXT, fetched_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_repos_user ON repos(username);
CREATE TABLE IF NOT EXISTS contributions (
    username TEXT NOT NULL, day TEXT NOT NULL, count INTEGER NOT NULL,
    PRIMARY KEY (username, day)
);
CREATE TABLE IF NOT EXISTS settings (
    username TEXT PRIMARY KEY,
    job_description TEXT DEFAULT ''
);
"""


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as c:
        c.executescript(SCHEMA)