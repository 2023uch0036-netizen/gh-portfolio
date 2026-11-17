import re

# canonical language -> aliases that may appear in a job description
LANG_ALIASES = {
    "Python": ["python", "django", "flask", "fastapi", "pandas"],
    "JavaScript": ["javascript", "js", "node", "nodejs", "node.js", "react", "vue", "express"],
    "TypeScript": ["typescript", "ts", "angular", "nestjs", "next.js", "nextjs"],
    "Java": ["java", "spring", "springboot", "kotlin", "jvm"],
    "C++": ["c++", "cpp"],
    "C#": ["c#", "csharp", ".net", "dotnet", "asp.net"],
    "Go": ["golang", "go"],
    "Rust": ["rust"],
    "Ruby": ["ruby", "rails"],
    "PHP": ["php", "laravel", "symfony"],
    "Swift": ["swift", "ios"],
    "Kotlin": ["kotlin", "android"],
    "HTML": ["html", "html5"],
    "CSS": ["css", "css3", "sass", "tailwind"],
    "Shell": ["bash", "shell", "scripting"],
    "SQL": ["sql", "postgres", "postgresql", "mysql", "sqlite"],
    "Dart": ["dart", "flutter"],
    "Scala": ["scala", "spark"],
    "R": ["r"],
}

# very short / ambiguous aliases only count when written exactly
STRICT = {"go", "r", "js", "ts", "c", "java"}


def _tokens(text: str) -> set[str]:
    text = text.lower()
    toks = set(re.findall(r"[a-z][a-z0-9+#.\-]*|\.net", text))
    return {t.strip(".-") for t in toks}


def required_languages(jd: str) -> list[str]:
    toks = _tokens(jd)
    found = []
    for lang, aliases in LANG_ALIASES.items():
        hits = {a for a in aliases if a in toks}
        # ambiguous aliases (e.g. "go", "r") need a tech context to avoid false hits
        hits = {h for h in hits if h not in {"r", "go"} or _has_context(jd, h)}
        if hits:
            found.append(lang)
    return found


def _has_context(jd: str, alias: str) -> bool:
    pattern = rf"(\b{alias}\b\s*(,|/|language|programming|developer))|((,|/)\s*\b{alias}\b)"
    return bool(re.search(pattern, jd, re.IGNORECASE))


def compute_match(jd: str, repos: list[dict]) -> dict:
    jd = (jd or "").strip()
    if not jd:
        raise ValueError("Job description is empty")
    if len(jd) > 20000:
        raise ValueError("Job description too long (max 20,000 chars)")

    required = required_languages(jd)
    user_langs = {r["language"] for r in repos if r["language"] and not r["is_fork"]}
    if not required:
        return {"percentage": 0, "matched": [], "missing": [], "required": [],
                "label": "No known languages detected in job description"}

    # proficiency weighting: languages with more repos count slightly more
    counts = {l: sum(1 for r in repos if r["language"] == l and not r["is_fork"])
              for l in required}
    matched = [l for l in required if l in user_langs]
    base = len(matched) / len(required)
    depth = sum(min(counts[l], 5) / 5 for l in matched) / len(required)
    pct = round(100 * (0.7 * base + 0.3 * depth))

    label = ("Excellent match" if pct >= 80 else "Strong match" if pct >= 60
             else "Partial match" if pct >= 35 else "Weak match")
    return {"percentage": pct, "label": label, "required": required,
            "matched": matched, "missing": [l for l in required if l not in user_langs]}