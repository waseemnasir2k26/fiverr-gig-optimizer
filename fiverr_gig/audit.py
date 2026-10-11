"""Gig audit: score a gig 0-100 against Fiverr limits and listing best practice.

Limits come from fiverr_gig.rules (each tagged official / observed / heuristic).
A high score means the listing is well-formed. It does not predict rank or sales.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict

from . import rules
from .lint import lint

MAX_POINTS = {"title": 20, "tags": 15, "description": 15, "packages": 20, "faq": 10, "requirements": 10, "images": 10}


@dataclass
class Category:
    name: str
    points: float
    max: int
    fixes: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    scored: bool = True


def _words(text: str) -> set[str]:
    return {w[:-1] if w.endswith("s") and len(w) > 3 else w for w in re.findall(r"[a-z0-9+#]+", text.lower()) if len(w) > 2}


def audit_title(g: dict) -> Category:
    c = Category("title", 0, MAX_POINTS["title"])
    t = g["title"]
    pts = 0.0
    if not t:
        c.fixes.append("Add a title. Fiverr titles are written as 'I will ...'.")
        return c
    if t.lower().startswith(rules.TITLE_PREFIX):
        pts += 4
    else:
        c.fixes.append("Start the title with 'I will' (Fiverr's standard gig title form).")
    n = len(t)
    if n <= rules.TITLE_MAX:
        pts += 6
        c.notes.append(f"{n}/{rules.TITLE_MAX} characters")
    else:
        c.fixes.append(f"Title is {n} characters; the limit is {rules.TITLE_MAX}. Cut {n - rules.TITLE_MAX}.")
    if n <= rules.TITLE_CARD_SAFE:
        pts += 4
    elif n <= rules.TITLE_MAX:
        pts += 2
        c.fixes.append(
            f"Only the first ~{rules.TITLE_CARD_SAFE} characters are safe on the gig card; put the main keyword before character {rules.TITLE_CARD_SAFE}."
        )
    # keyword placement: first tag's words should appear early in the title
    body = re.sub(r"(?i)^i will\s+", "", t)
    first_50 = body[: rules.TITLE_CARD_SAFE].lower()
    tag_words = [w for tag in g["tags"][:1] for w in _words(tag)]
    if tag_words and all(w in first_50 for w in tag_words):
        pts += 4
    elif tag_words:
        c.fixes.append(f"Front-load your top tag ('{g['tags'][0]}') in the first {rules.TITLE_CARD_SAFE} characters of the title.")
    else:
        pts += 2  # cannot judge placement without tags
    if t.isupper() or re.search(r"[!]{2,}|[\U0001F300-\U0001FAFF]", t):
        c.fixes.append("Avoid ALL CAPS, repeated '!' and emoji in the title.")
    else:
        pts += 2
    c.points = pts
    return c


def audit_tags(g: dict) -> Category:
    c = Category("tags", 0, MAX_POINTS["tags"])
    tags = g["tags"]
    if not tags:
        c.fixes.append(f"Add {rules.TAGS_MAX} tags: each a buyer search phrase, 1-3 words.")
        return c
    pts = 0.0
    if len(tags) == rules.TAGS_MAX:
        pts += 5
    elif len(tags) < rules.TAGS_MAX:
        pts += 2
        c.fixes.append(f"Use all {rules.TAGS_MAX} tags; you have {len(tags)}.")
    else:
        c.fixes.append(f"Fiverr allows {rules.TAGS_MAX} tags; you listed {len(tags)}. Drop {len(tags) - rules.TAGS_MAX}.")
    long_tags = [t for t in tags if len(t) > rules.TAG_MAX_LEN]
    if long_tags:
        c.fixes.append(f"Tags over {rules.TAG_MAX_LEN} characters are rejected in practice: {', '.join(long_tags)}.")
    else:
        pts += 3
    if len({t.lower() for t in tags}) == len(tags):
        pts += 2
    else:
        c.fixes.append("Remove duplicate tags.")
    multi = sum(1 for t in tags if len(t.split()) >= 2)
    if multi >= max(1, len(tags) // 2):
        pts += 2
    else:
        c.fixes.append("Use mostly 2-3 word phrases; single words are broad and crowded.")
    title_words = _words(g["title"] + " " + g["description"])
    overlap = sum(1 for t in tags if _words(t) & title_words)
    if overlap >= min(3, len(tags)):
        pts += 3
    else:
        c.fixes.append("Most tags should echo words that appear in the title or description (relevance).")
    c.points = pts
    return c


def audit_description(g: dict) -> Category:
    c = Category("description", 0, MAX_POINTS["description"])
    d = g["description"]
    if not d.strip():
        c.fixes.append("Add a description (up to 1,200 characters).")
        return c
    pts = 0.0
    n = len(d)
    if n <= rules.DESC_MAX:
        pts += 4
        c.notes.append(f"{n}/{rules.DESC_MAX} characters")
    else:
        c.fixes.append(f"Description is {n} characters; the limit is {rules.DESC_MAX}. Cut {n - rules.DESC_MAX}.")
    if n >= rules.DESC_MIN_GOOD:
        pts += 3
    else:
        c.fixes.append(f"Description is thin ({n} chars). Cover what you deliver, how it works, and who it is for (aim for {rules.DESC_MIN_GOOD}+).")
    bullets = len(re.findall(r"(?m)^\s*(?:[-*•]|\d+[.)])\s+", d))
    if bullets >= rules.DESC_BULLET_MIN:
        pts += 3
    else:
        c.fixes.append("Add a bulleted list of what the buyer gets (3+ bullets scan better than a paragraph).")
    if re.search(r"(?i)\b(message me|send me|order|get started|start|ask me|contact)\b", d[-300:]):
        pts += 2
    else:
        c.fixes.append("End with a call to action that keeps the buyer on Fiverr (e.g. 'Message me here before ordering').")
    hits = [f for f in lint(d) if f.severity == "high"]
    if not hits:
        pts += 3
    else:
        c.fixes.append("Remove off-platform contact or payment words: " + ", ".join(sorted({f.match for f in hits})) + ".")
    c.points = pts
    return c


def audit_packages(g: dict) -> Category:
    c = Category("packages", 0, MAX_POINTS["packages"])
    pk = g["packages"]
    have = [t for t in rules.PACKAGE_TIERS if t in pk]
    if not have:
        c.fixes.append("Add Basic / Standard / Premium packages.")
        return c
    pts = 0.0
    if len(have) == 3:
        pts += 6
    else:
        pts += 2
        c.fixes.append("Offer all three tiers (Basic, Standard, Premium); missing: " + ", ".join(t for t in rules.PACKAGE_TIERS if t not in pk) + ".")
    prices = [pk[t]["price"] for t in have]
    if all(p is not None and p > 0 for p in prices):
        if all(a < b for a, b in zip(prices, prices[1:])):
            pts += 5
            if len(have) == 3 and prices[0] > 0:
                ratio = prices[2] / prices[0]
                if 3 <= ratio <= 12:
                    pts += 2
                else:
                    c.fixes.append(f"Premium is {ratio:.1f}x Basic. A 3x-12x ladder is typical; adjust so Standard looks like the obvious pick.")
            else:
                pts += 1
        else:
            c.fixes.append("Prices must rise Basic < Standard < Premium.")
    else:
        c.fixes.append("Every package needs a price above zero.")
    days = [pk[t]["days"] for t in have]
    if all(d is not None for d in days) and all(a <= b for a, b in zip(days, days[1:])):
        pts += 2
    else:
        c.fixes.append("Give each package a delivery time that does not shrink as scope grows.")
    counts = [len(pk[t]["items"]) for t in have]
    if all(n >= 2 for n in counts) and all(a <= b for a, b in zip(counts, counts[1:])):
        pts += 3
    else:
        c.fixes.append("List 2+ deliverables per package, growing from Basic to Premium.")
    if len({tuple(pk[t]["items"]) for t in have}) == len(have):
        pts += 2
    else:
        c.fixes.append("Packages have identical deliverables; differentiate them.")
    c.points = min(pts, c.max)
    return c


def audit_faq(g: dict) -> Category:
    c = Category("faq", 0, MAX_POINTS["faq"])
    faq = [f for f in g["faq"] if f["q"].strip() and f["a"].strip()]
    n = len(faq)
    if n == 0:
        c.fixes.append(f"Add at least {rules.FAQ_MIN_GOOD} FAQs (scope, turnaround, what you need from the buyer).")
        return c
    pts = min(n, rules.FAQ_MIN_GOOD) / rules.FAQ_MIN_GOOD * 7
    if n < rules.FAQ_MIN_GOOD:
        c.fixes.append(f"Add {rules.FAQ_MIN_GOOD - n} more FAQ(s).")
    if all(len(f["a"]) >= 40 for f in faq):
        pts += 3
    else:
        c.fixes.append("Answer each FAQ in a full sentence or two (40+ characters).")
    c.points = pts
    return c


def audit_requirements(g: dict) -> Category:
    c = Category("requirements", 0, MAX_POINTS["requirements"])
    req = [r for r in g["requirements"] if r.strip()]
    if not req:
        c.fixes.append("Add buyer requirements so orders start with what you need (access, files, brand details).")
        return c
    pts = 6
    if any("?" in r or r.lower().startswith(("what", "which", "please", "provide", "share", "send", "list")) for r in req):
        pts += 4
    else:
        c.fixes.append("Phrase requirements as clear questions or instructions ('Please provide ...').")
    c.points = pts
    return c


def audit_images(g: dict) -> Category:
    c = Category("images", 0, MAX_POINTS["images"])
    imgs = g["images"]
    if not imgs:
        c.scored = False
        c.notes.append(
            f"not scored: add an 'images' list to check sizes (recommended {rules.IMG_RECOMMENDED[0]}x{rules.IMG_RECOMMENDED[1]})"
        )
        return c
    pics = [i for i in imgs if i.get("type", "image") == "image"]
    vids = [i for i in imgs if i.get("type") == "video"]
    pdfs = [i for i in imgs if i.get("type") == "pdf"]
    pts = 0.0
    if 1 <= len(pics) <= rules.GALLERY_MAX_IMAGES:
        pts += 3
    else:
        c.fixes.append(f"Gallery takes 1-{rules.GALLERY_MAX_IMAGES} images; you listed {len(pics)}.")
    if len(vids) <= rules.GALLERY_MAX_VIDEOS and len(pdfs) <= rules.GALLERY_MAX_PDFS:
        pts += 1
    else:
        c.fixes.append(f"Max {rules.GALLERY_MAX_VIDEOS} video and {rules.GALLERY_MAX_PDFS} PDFs.")
    bad = False
    for i in pics:
        w, h = i.get("width"), i.get("height")
        if not (w and h):
            continue
        if w < rules.IMG_MIN[0] or h < rules.IMG_MIN[1] or w > rules.IMG_MAX[0] or h > rules.IMG_MAX[1]:
            c.fixes.append(f"Image {w}x{h} is outside Fiverr's {rules.IMG_MIN[0]}x{rules.IMG_MIN[1]} to {rules.IMG_MAX[0]}x{rules.IMG_MAX[1]} range.")
            bad = True
        elif (w, h) != rules.IMG_RECOMMENDED:
            c.fixes.append(f"Image {w}x{h}: Fiverr recommends {rules.IMG_RECOMMENDED[0]}x{rules.IMG_RECOMMENDED[1]}.")
    if pics and not bad:
        pts += 3
    if vids:
        pts += 1.5
    else:
        c.fixes.append("Add a short gig video if you can; it is the one gallery slot most sellers leave empty.")
    if pdfs:
        pts += 1.5
    c.points = min(pts, c.max)
    return c


def _grade(score: float) -> str:
    return "A" if score >= 90 else "B" if score >= 80 else "C" if score >= 70 else "D" if score >= 55 else "F"


def audit(gig: dict) -> dict:
    cats = [
        audit_title(gig),
        audit_tags(gig),
        audit_description(gig),
        audit_packages(gig),
        audit_faq(gig),
        audit_requirements(gig),
        audit_images(gig),
    ]
    scored = [c for c in cats if c.scored]
    got = sum(c.points for c in scored)
    possible = sum(c.max for c in scored)
    score = round(got / possible * 100) if possible else 0
    fixes = [f for c in cats for f in c.fixes]
    return {
        "title": gig["title"],
        "score": score,
        "grade": _grade(score),
        "categories": [asdict(c) for c in cats],
        "fixes": fixes,
    }
