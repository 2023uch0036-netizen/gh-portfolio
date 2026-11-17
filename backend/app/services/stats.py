from collections import Counter
from datetime import date, timedelta


def profile_summary(user: dict, repos: list[dict]) -> dict:
    own = [r for r in repos if not r["is_fork"]]
    return {
        "username": user["username"], "name": user["name"],
        "avatar_url": user["avatar_url"], "bio": user["bio"],
        "html_url": user["html_url"],
        "followers": user["followers"], "following": user["following"],
        "public_repos": user["public_repos"],
        "total_stars": sum(r["stars"] for r in repos),
        "total_forks": sum(r["forks"] for r in repos),
        "top_languages": top_languages(own),
    }


def top_languages(repos: list[dict], limit: int = 6) -> list[dict]:
    counts = Counter(r["language"] for r in repos if r["language"])
    total = sum(counts.values()) or 1
    return [
        {"language": lang, "repos": n, "percent": round(100 * n / total, 1)}
        for lang, n in counts.most_common(limit)
    ]


def repo_cards(repos: list[dict]) -> list[dict]:
    ranked = sorted(repos, key=lambda r: (r["stars"], r["updated_at"]), reverse=True)
    return [
        {k: r[k] for k in ("name", "description", "language", "stars", "forks", "html_url")}
        for r in ranked
    ]


def _levels(counts: list[int]) -> list[int]:
    """Map counts to intensity 0-4 using quartiles of non-zero days."""
    nz = sorted(c for c in counts if c > 0)
    if not nz:
        return [0] * len(counts)
    q = [nz[int(len(nz) * p) - 1 if len(nz) * p >= 1 else 0] for p in (0.25, 0.5, 0.75)]
    def lvl(c):
        if c == 0: return 0
        if c <= q[0]: return 1
        if c <= q[1]: return 2
        if c <= q[2]: return 3
        return 4
    return [lvl(c) for c in counts]


def contribution_stats(days: list[dict]) -> dict:
    lv = _levels([d["count"] for d in days])
    cells = [{**d, "level": l} for d, l in zip(days, lv)]

    by_day = {date.fromisoformat(d["day"]): d["count"] for d in days}
    longest = run = 0
    for d in sorted(by_day):
        run = run + 1 if by_day[d] > 0 and (d - timedelta(days=1)) in by_day \
            and by_day[d - timedelta(days=1)] > 0 else (1 if by_day[d] > 0 else 0)
        longest = max(longest, run)

    # current streak: walk back from the latest day (today may still be 0)
    current, cursor = 0, max(by_day) if by_day else None
    if cursor and by_day[cursor] == 0:
        cursor -= timedelta(days=1)
    while cursor in by_day and by_day[cursor] > 0:
        current += 1
        cursor -= timedelta(days=1)

    return {
        "cells": cells,
        "total": sum(by_day.values()),
        "current_streak": current,
        "longest_streak": longest,
    }