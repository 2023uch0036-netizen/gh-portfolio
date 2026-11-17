from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from .. import github_client as gh
from ..services import cache, stats, match, assistant

router = APIRouter(prefix="/api/profile", tags=["profile"])


class JDBody(BaseModel):
    job_description: str = Field(min_length=10, max_length=20000)


class ChatBody(BaseModel):
    question: str = Field(min_length=1, max_length=500)


def _load(username: str, refresh=False):
    try:
        return cache.get_user_and_repos(username, refresh)
    except gh.GitHubError as e:
        raise HTTPException(e.status, e.message)


@router.get("/{username}")
def get_profile(username: str, refresh: bool = False):
    user, repos, from_cache = _load(username, refresh)
    jd = cache.load_job_description(username)
    result = {
        "profile": stats.profile_summary(user, repos),
        "repos": stats.repo_cards(repos),
        "from_cache": from_cache,
        "fetched_at": user["fetched_at"],
        "job_description": jd,
        "match": match.compute_match(jd, repos) if jd else None,
    }
    return result


@router.get("/{username}/contributions")
def get_contributions(username: str, refresh: bool = False):
    _load(username)  # ensures user exists / cached
    try:
        days = cache.get_contributions(username, refresh)
    except gh.GitHubError as e:
        raise HTTPException(e.status, e.message)
    return {**stats.contribution_stats(days),
            "token_missing": not days}


@router.post("/{username}/match")
def post_match(username: str, body: JDBody):
    _, repos, _ = _load(username)
    try:
        result = match.compute_match(body.job_description, repos)
    except ValueError as e:
        raise HTTPException(422, str(e))
    cache.save_job_description(username, body.job_description)
    return result


@router.post("/{username}/chat")
def chat(username: str, body: ChatBody):
    user, repos, _ = _load(username)
    return {"answer": assistant.answer_question(user, repos, body.question)}


@router.post("/{username}/pitch")
def pitch(username: str, body: JDBody):
    user, repos, _ = _load(username)
    m = match.compute_match(body.job_description, repos)
    return {"pitch": assistant.generate_pitch(user, repos, body.job_description, m),
            "match": m}