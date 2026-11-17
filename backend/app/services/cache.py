from datetime import datetime, timedelta, timezone
from .. import github_client as gh
from ..config import CACHE_TTL_MINUTES
from ..db import get_conn


def _now():
    return datetime.now(timezone.utc)


def _is_fresh(ts: str | None) -> bool:
    if not ts:
        return False
    return _now() - datetime.fromisoformat(ts) < timedelta(minutes=CACHE_TTL_MINUTES)


def get_user_and_repos(username: str, refresh: bool = False):
    """Return (user_row, repo_rows, from_cache). Hits GitHub only when stale."""
    username = username.lower()
    with get_conn() as c:
        u = c.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        if u and _is_fresh(u["fetched_at"]) and not refresh:
            repos = c.execute("SELECT * FROM repos WHERE username=?", (username,)).fetchall()
            return dict(u), [dict(r) for r in repos], True

    user, repos = gh.fetch_user(username), gh.fetch_repos(username)
    ts = _now().isoformat()
    with get_conn() as c:
        c.execute(
            "INSERT OR REPLACE INTO users VALUES (?,?,?,?,?,?,?,?,?)",
            (username, user.get("name") or user["login"], user["avatar_url"],
             user.get("bio"), user["followers"], user["following"],
             user["public_repos"], user["html_url"], ts),
        )
        c.execute("DELETE FROM repos WHERE username=?", (username,))
        c.executemany(
            "INSERT INTO repos VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            [(r["id"], username, r["name"], r.get("description"), r.get("language"),
              r["stargazers_count"], r["forks_count"], r["html_url"],
              int(r["fork"]), r["updated_at"], ts) for r in repos],
        )
        u = c.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        rows = c.execute("SELECT * FROM repos WHERE username=?", (username,)).fetchall()
    return dict(u), [dict(r) for r in rows], False


def get_contributions(username: str, refresh: bool = False) -> list[dict]:
    username = username.lower()
    with get_conn() as c:
        u = c.execute("SELECT fetched_at FROM users WHERE username=?", (username,)).fetchone()
        rows = c.execute(
            "SELECT day, count FROM contributions WHERE username=? ORDER BY day", (username,)
        ).fetchall()
        if rows and u and _is_fresh(u["fetched_at"]) and not refresh:
            return [dict(r) for r in rows]
    days = gh.fetch_contributions(username)
    if days:
        with get_conn() as c:
            c.execute("DELETE FROM contributions WHERE username=?", (username,))
            c.executemany(
                "INSERT INTO contributions VALUES (?,?,?)",
                [(username, d["day"], d["count"]) for d in days],
            )
    return days


def save_job_description(username: str, jd: str):
    with get_conn() as c:
        c.execute("INSERT OR REPLACE INTO settings VALUES (?,?)", (username.lower(), jd))


def load_job_description(username: str) -> str:
    with get_conn() as c:
        r = c.execute("SELECT job_description FROM settings WHERE username=?",
                      (username.lower(),)).fetchone()
    return r["job_description"] if r else ""