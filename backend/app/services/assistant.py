from ..config import ANTHROPIC_API_KEY
from . import stats

MODEL = "claude-sonnet-4-5"


def _context(user: dict, repos: list[dict]) -> str:
    s = stats.profile_summary(user, repos)
    lines = [f"Developer: {s['name']} (@{s['username']}). Bio: {s['bio']}",
             f"Followers {s['followers']}, total stars {s['total_stars']}.",
             "Top languages: " + ", ".join(f"{l['language']} ({l['percent']}%)" for l in s["top_languages"]),
             "Repositories:"]
    for r in stats.repo_cards(repos)[:30]:
        lines.append(f"- {r['name']} [{r['language']}] ⭐{r['stars']} 🍴{r['forks']}: {r['description']}")
    return "\n".join(lines)


def _llm(system: str, prompt: str, max_tokens=500) -> str | None:
    if not ANTHROPIC_API_KEY:
        return None
    import anthropic
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    msg = client.messages.create(
        model=MODEL, max_tokens=max_tokens, system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text


def answer_question(user, repos, question: str) -> str:
    if not question.strip() or len(question) > 500:
        raise ValueError("Question must be 1-500 characters")
    system = ("You answer recruiter questions about a developer using ONLY the data below. "
              "If the data doesn't say, say so. Be concise.\n\n" + _context(user, repos))
    out = _llm(system, question)
    if out:
        return out
    # fallback without an API key: keyword search over repos
    q = question.lower()
    hits = [r for r in repos if r["language"] and r["language"].lower() in q
            or q in (r["description"] or "").lower()]
    if hits:
        return "Relevant repos: " + ", ".join(r["name"] for r in hits[:5])
    return "Set ANTHROPIC_API_KEY for full answers. Top languages: " + \
        ", ".join(l["language"] for l in stats.top_languages(repos))


def generate_pitch(user, repos, jd: str, match: dict) -> str:
    system = "Write a 4-sentence, honest, first-person pitch for a developer applying to a role. No fluff."
    prompt = (f"{_context(user, repos)}\n\nJob description:\n{jd[:3000]}\n\n"
              f"Matched skills: {match['matched']}. Gaps: {match['missing']}. "
              "Mention strengths; acknowledge gaps briefly and positively.")
    out = _llm(system, prompt, 400)
    return out or (f"I work primarily in {', '.join(match['matched']) or 'several languages'} "
                   f"and have {len(repos)} public repositories. Enable ANTHROPIC_API_KEY for a full pitch.")