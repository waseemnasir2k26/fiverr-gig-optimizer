"""Load gigs from JSON, YAML (needs PyYAML) or a simple Markdown layout."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


class GigFormatError(ValueError):
    pass


def normalize(raw: dict) -> dict:
    """Map the accepted key spellings onto one internal shape."""
    g: dict[str, Any] = {}
    g["title"] = str(raw.get("title") or "").strip()
    g["category"] = raw.get("category") or raw.get("cat") or ""
    tags = raw.get("tags") or []
    if isinstance(tags, str):
        tags = [t.strip() for t in re.split(r"[,\n]", tags) if t.strip()]
    g["tags"] = [str(t).strip() for t in tags]
    g["description"] = str(raw.get("description") or raw.get("desc") or "")
    pk = raw.get("packages") or raw.get("pricing") or {}
    packages: dict[str, dict] = {}
    for tier, p in pk.items():
        if not isinstance(p, dict):
            continue
        price = p.get("price")
        try:
            price = float(str(price).replace("$", "").replace(",", "")) if price is not None else None
        except ValueError:
            price = None
        days = p.get("days")
        if days is None:
            m = re.search(r"\d+", str(p.get("delivery") or p.get("del") or ""))
            days = int(m.group()) if m else None
        packages[str(tier).lower()] = {
            "name": p.get("name") or p.get("title") or "",
            "price": price,
            "days": int(days) if days is not None else None,
            "revisions": p.get("revisions", p.get("rev")),
            "items": [str(i) for i in (p.get("items") or [])],
        }
    g["packages"] = packages
    faq = raw.get("faq") or []
    g["faq"] = [
        {"q": str(f.get("q") or f.get("question") or ""), "a": str(f.get("a") or f.get("answer") or "")}
        for f in faq
        if isinstance(f, dict)
    ]
    g["requirements"] = [str(r) for r in (raw.get("requirements") or [])]
    imgs = raw.get("images")
    g["images"] = imgs if isinstance(imgs, list) and imgs else None
    return g


def gigs_from_data(data: Any) -> list[dict]:
    if isinstance(data, dict) and isinstance(data.get("gigs"), list):
        return [normalize(g) for g in data["gigs"]]
    if isinstance(data, list):
        return [normalize(g) for g in data]
    if isinstance(data, dict):
        return [normalize(data)]
    raise GigFormatError("expected a gig object, a list of gigs, or a config with a 'gigs' list")


_SECTION = re.compile(r"(?i)^(description|packages|faq|requirements|images)\b")


def parse_markdown(text: str) -> dict:
    """Parse the Markdown layout documented in docs/input-formats.md."""
    raw: dict[str, Any] = {"packages": {}, "faq": [], "requirements": [], "images": []}
    section = None
    desc_lines: list[str] = []
    pending_q = None
    for line in text.splitlines():
        s = line.strip()
        m = re.match(r"^#{1,3}\s+(.*)$", s)
        if m and _SECTION.match(m.group(1)):
            section = m.group(1).split()[0].lower()
            continue
        kv = re.match(r"(?i)^(title|category|tags)\s*:\s*(.*)$", s)
        if kv and section is None:
            raw[kv.group(1).lower()] = kv.group(2).strip()
            continue
        if section == "description":
            desc_lines.append(line.rstrip())
        elif section == "packages" and s.startswith(("-", "*")):
            body = s.lstrip("-* ").strip()
            tier, _, rest = body.partition(":")
            pkg: dict[str, Any] = {"items": []}
            for part in (p.strip() for p in rest.split("|")):
                if re.match(r"^\$?\d[\d,.]*$", part):
                    pkg["price"] = part
                elif re.search(r"\bdays?\b", part, re.I):
                    pkg["days"] = int(re.search(r"\d+", part).group())
                elif re.search(r"\brevisions?\b", part, re.I):
                    pkg["revisions"] = re.search(r"\d+|unlimited", part, re.I).group()
                elif part:
                    pkg["items"].extend(i.strip() for i in part.split(";") if i.strip())
            raw["packages"][tier.strip().lower()] = pkg
        elif section == "faq":
            if s.lower().startswith("q:"):
                pending_q = s[2:].strip()
            elif s.lower().startswith("a:") and pending_q is not None:
                raw["faq"].append({"q": pending_q, "a": s[2:].strip()})
                pending_q = None
        elif section == "requirements" and s.startswith(("-", "*")):
            raw["requirements"].append(s.lstrip("-* ").strip())
        elif section == "images" and s.startswith(("-", "*")):
            im = re.match(r"^[-*]\s*(\w+)?\s*:?\s*(\d+)\s*x\s*(\d+)", s, re.I)
            if im:
                raw["images"].append(
                    {"type": (im.group(1) or "image").lower(), "width": int(im.group(2)), "height": int(im.group(3))}
                )
            else:
                kind = re.match(r"^[-*]\s*(video|pdf)\b", s, re.I)
                if kind:
                    raw["images"].append({"type": kind.group(1).lower()})
    raw["description"] = "\n".join(desc_lines).strip()
    if not raw.get("title"):
        raise GigFormatError("markdown gig needs a 'Title: ...' line")
    return raw


def load_path(path: str | Path) -> list[dict]:
    p = Path(path)
    if not p.exists():
        raise GigFormatError(f"file not found: {p}")
    text = p.read_text(encoding="utf-8")
    suffix = p.suffix.lower()
    if suffix == ".json":
        try:
            return gigs_from_data(json.loads(text))
        except json.JSONDecodeError as e:
            raise GigFormatError(f"invalid JSON in {p}: {e}") from e
    if suffix in (".yaml", ".yml"):
        try:
            import yaml  # type: ignore
        except ImportError as e:
            raise GigFormatError("YAML input needs PyYAML: pip install 'fiverr-gig-optimizer[yaml]'") from e
        return gigs_from_data(yaml.safe_load(text))
    if suffix in (".md", ".markdown", ".txt"):
        return [normalize(parse_markdown(text))]
    raise GigFormatError(f"unsupported file type '{suffix}' (use .json, .yaml, .yml or .md)")
