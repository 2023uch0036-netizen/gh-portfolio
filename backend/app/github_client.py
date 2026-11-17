import httpx
from .config import GITHUB_TOKEN

API = "https://api.github.com"


class GitHubError(Exception):
    def __init__(self, status: int, message: str):
        self.status, self.message = status, message


def _headers():
    h = {"Accept": "application/vnd.github+json"}
    if GITHUB_TOKEN:
        h["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return h


def _check(r: httpx.Response):
    if r.status_code == 404:
        raise GitHubError(404, "GitHub user not found")
    if r.status_code in (403, 429):
        raise GitHubError(429, "GitHub rate limit hit; add GITHUB_TOKEN or retry later")
    r.raise_for_status()


def fetch_user(username: str) -> dict:
    r = httpx.get(f"{API}/users/{username}", headers=_headers(), timeout=15)
    _check(r)
    return r.json()


def fetch_repos(username: str) -> list[dict]:
    repos, page = [], 1
    while True:
        r = httpx.get(
            f"{API}/users/{username}/repos",
            params={"per_page": 100, "page": page, "sort": "updated"},
            headers=_headers(), timeout=15,
        )
        _check(r)
        batch = r.json()
        repos += batch
        if len(batch) < 100:
            return repos
        page += 1


QUERY = """
query($login:String!){
  user(login:$login){
    contributionsCollection{
      contributionCalendar{
        weeks{ contributionDays{ date contributionCount } }
      }
    }
  }
}"""


def fetch_contributions(username: str) -> list[dict]:
    """Returns [{day, count}]. Requires GITHUB_TOKEN (GraphQL needs auth)."""
    if not GITHUB_TOKEN:
        return []
    r = httpx.post(
        f"{API}/graphql",
        json={"query": QUERY, "variables": {"login": username}},
        headers=_headers(), timeout=20,
    )
    _check(r)
    data = r.json()["data"]["user"]
    if not data:
        return []
    weeks = data["contributionsCollection"]["contributionCalendar"]["weeks"]
    return [
        {"day": d["date"], "count": d["contributionCount"]}
        for w in weeks for d in w["contributionDays"]
    ]