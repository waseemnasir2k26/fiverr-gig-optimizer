"""Tag and title helper from a seed niche. Offline heuristics; optional LLM (off by default).

The offline mode does not know real Fiverr search volume. It builds well-formed
candidates (<= 20 chars, multi-word, buyer-intent modifiers) for you to check
against Fiverr's own search suggestions. Treat the output as a starting list.
"""
from __future__ import annotations

import json
import os
import re
import urllib.request

from . import rules

_STOP = {"a", "an", "the", "and", "or", "for", "with", "to", "of", "in", "on", "i", "will"}
_INTENT_GENERAL = ["expert", "service", "custom", "professional", "freelancer", "for business", "consultant", "pro", "affordable", "fast"]
_INTENT_TECH = ["developer", "expert", "setup", "integration", "automation", "consultant", "fix", "custom", "audit", "service"]
_TECH_HINTS = {"n8n", "api", "wordpress", "shopify", "python", "automation", "zapier", "bot", "chatbot", "code", "coding", "web", "website", "app", "ai", "seo", "crm", "scraper", "script", "integration", "make", "react", "plugin", "software", "data"}


def _intent(toks: list[str]) -> list[str]:
    return _INTENT_TECH if _TECH_HINTS & set(toks) else _INTENT_GENERAL
_VERBS = ["build", "set up", "create", "fix", "design", "automate"]


def _tokens(seed: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9+#.]+", seed.lower()) if t not in _STOP]


def suggest_tags(seed: str, limit: int = 15) -> list[dict]:
    """Return ranked tag candidates, each valid (<= TAG_MAX_LEN chars)."""
    toks = _tokens(seed)
    if not toks:
        raise ValueError("seed niche is empty")
    base = " ".join(toks)
    cands: dict[str, float] = {}

    def add(tag: str, score: float) -> None:
        tag = tag.strip()
        if 0 < len(tag) <= rules.TAG_MAX_LEN and tag not in cands:
            cands[tag] = score

    add(base, 10)
    intent = _intent(toks)
    for i in intent:
        add(f"{base} {i}", 8 if len(toks) <= 2 else 6)
        add(f"{i} {base}", 5)
    if len(toks) > 1:
        for t in toks:
            if len(t) > 2:
                add(t, 3)
                for i in intent[:5]:
                    add(f"{t} {i}", 4)
        for a in range(len(toks) - 1):
            add(" ".join(toks[a : a + 2]), 7)
    ranked = sorted(cands.items(), key=lambda kv: (-kv[1], kv[0]))[:limit]
    return [{"tag": t, "length": len(t), "score": s} for t, s in ranked]


def pick_five(cands: list[dict]) -> list[str]:
    """Choose up to 5 diverse tags: skip a tag whose words overlap >= 75% with one already chosen."""
    chosen: list[str] = []
    for c in cands:
        t = c["tag"]
        a = set(t.split())
        if any(len(a & set(x.split())) / len(a | set(x.split())) >= 0.75 for x in chosen):
            continue
        chosen.append(t)
        if len(chosen) == rules.TAGS_MAX:
            break
    return chosen


def suggest_titles(seed: str, limit: int = 5) -> list[dict]:
    toks = _tokens(seed)
    if not toks:
        raise ValueError("seed niche is empty")
    base = " ".join(toks)
    out = []
    for v in _VERBS:
        if v in toks:  # avoid "I will design logo design"
            continue
        t = f"I will {v} {base}"
        if len(t) <= rules.TITLE_MAX:
            out.append(t)
    out = out[:limit]
    return [{"title": t, "length": len(t), "within_card_safe": len(t) <= rules.TITLE_CARD_SAFE} for t in out]


def build(seed: str) -> dict:
    cands = suggest_tags(seed)
    return {"seed": seed, "tags": cands, "five_tags": pick_five(cands), "titles": suggest_titles(seed), "source": "offline"}


def llm_enabled(env: dict | None = None) -> bool:
    e = os.environ if env is None else env
    return bool(e.get("FIVERR_GIG_LLM_BASE_URL") and e.get("FIVERR_GIG_LLM_API_KEY") and e.get("FIVERR_GIG_LLM_MODEL"))


def llm_suggest(seed: str, env: dict | None = None, opener=urllib.request.urlopen) -> list[str]:
    """Optional: ask an OpenAI-compatible chat endpoint for extra tag ideas.

    Only the seed niche text is sent. Runs only when the caller passes --llm AND the
    three FIVERR_GIG_LLM_* variables are set. Output is filtered to valid tags.
    """
    e = os.environ if env is None else env
    if not llm_enabled(e):
        raise RuntimeError("LLM not configured: set FIVERR_GIG_LLM_BASE_URL, FIVERR_GIG_LLM_API_KEY, FIVERR_GIG_LLM_MODEL")
    url = e["FIVERR_GIG_LLM_BASE_URL"].rstrip("/") + "/chat/completions"
    body = {
        "model": e["FIVERR_GIG_LLM_MODEL"],
        "messages": [
            {
                "role": "user",
                "content": f"List 12 Fiverr gig search tags (each at most {rules.TAG_MAX_LEN} characters, 1-3 words) "
                f"for this service niche: {seed}. Reply with a JSON array of strings only.",
            }
        ],
        "temperature": 0.4,
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {e['FIVERR_GIG_LLM_API_KEY']}"},
    )
    with opener(req, timeout=30) as resp:
        payload = json.loads(resp.read().decode())
    text = payload["choices"][0]["message"]["content"]
    m = re.search(r"\[.*\]", text, re.S)
    arr = json.loads(m.group()) if m else []
    seen, out = set(), []
    for t in arr:
        t = str(t).strip().lower()
        if t and len(t) <= rules.TAG_MAX_LEN and t not in seen:
            seen.add(t)
            out.append(t)
    return out
