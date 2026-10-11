"""Command line entry point: `fiverr-gig` (also `python -m fiverr_gig`)."""
from __future__ import annotations

import argparse
import json
import sys

from . import __version__, keywords, pricing, rules
from .audit import audit
from .lint import lint, summary
from .loader import GigFormatError, load_path


def _bar(score: int, width: int = 20) -> str:
    filled = round(score / 100 * width)
    return "#" * filled + "-" * (width - filled)


def cmd_audit(a: argparse.Namespace) -> int:
    try:
        gigs = load_path(a.file)
    except GigFormatError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    results = [audit(g) for g in gigs]
    if a.json:
        print(json.dumps(results if len(results) > 1 else results[0], indent=2))
    else:
        for r in results:
            print(f"GIG: {r['title']}")
            print(f"SCORE: {r['score']}/100  grade {r['grade']}  [{_bar(r['score'])}]")
            for c in r["categories"]:
                tag = f"{c['points']:.0f}/{c['max']}" if c["scored"] else "n/a"
                print(f"  {c['name']:<13}{tag:>6}")
            if r["fixes"]:
                print("FIXES:")
                for i, f in enumerate(r["fixes"], 1):
                    print(f"  {i}. {f}")
            else:
                print("FIXES: none")
            print()
    worst = min(r["score"] for r in results)
    return 1 if a.min_score is not None and worst < a.min_score else 0


def cmd_lint(a: argparse.Namespace) -> int:
    if a.text is not None:
        text = a.text
    elif a.file == "-" or a.file is None:
        text = sys.stdin.read()
    else:
        with open(a.file, encoding="utf-8") as fh:
            text = fh.read()
    findings = lint(text)
    if a.json:
        print(json.dumps({"summary": summary(findings), "findings": [f.to_dict() for f in findings]}, indent=2))
    else:
        print(summary(findings))
        for f in findings:
            sug = f" -> try: {f.suggestion}" if f.suggestion else ""
            print(f"  [{f.severity}] '{f.match}' ({f.label}){sug}")
    return 1 if findings else 0


def cmd_price(a: argparse.Namespace) -> int:
    try:
        if a.ladder is not None:
            ladder = pricing.suggest_ladder(a.ladder)
            if a.json:
                print(json.dumps(ladder, indent=2))
            else:
                print(f"Ladder from Basic ${a.ladder:g} (1x / 2.5x / 5x heuristic, not a Fiverr rule):")
                for tier, v in ladder.items():
                    print(f"  {tier:<9} sticker ${v['gross']:>6}   you keep ${v['net']:>8.2f}")
            return 0
        r = pricing.report(gross=a.gross, net_target=a.net, hours=a.hours)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    if a.json:
        print(json.dumps(r, indent=2))
    else:
        print(f"Sticker price (gross): ${r['gross']:.2f}")
        print(f"Fiverr seller fee {r['fee_rate']:.0%}:   -${r['fee']:.2f}")
        print(f"You keep (net):        ${r['net']:.2f}")
        if "net_hourly" in r:
            print(f"Net per hour ({r['hours']:g}h):    ${r['net_hourly']:.2f}")
        print(f"Buyer checkout (estimate): ${r['buyer_checkout_estimate']:.2f}  (5.5% + small-order fee; check Fiverr's current fees page)")
    return 0


def cmd_keywords(a: argparse.Namespace) -> int:
    if isinstance(a.seed, list):
        a.seed = " ".join(a.seed)
    try:
        res = keywords.build(a.seed)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    if a.llm:
        try:
            extra = keywords.llm_suggest(a.seed)
            res["llm_tags"] = extra
            res["source"] = "offline+llm"
        except Exception as e:  # network/config errors must not hide the offline result
            print(f"warning: LLM step skipped: {e}", file=sys.stderr)
    if a.json:
        print(json.dumps(res, indent=2))
    else:
        print(f"Seed: {res['seed']}  (offline heuristics; verify against Fiverr search suggestions)")
        print("Suggested 5 tags: " + ", ".join(res["five_tags"]))
        print("All candidates:")
        for t in res["tags"]:
            print(f"  {t['tag']:<22} {t['length']:>2} chars")
        print("Title drafts:")
        for t in res["titles"]:
            print(f"  {t['title']}  ({t['length']})")
        if "llm_tags" in res:
            print("LLM extras: " + ", ".join(res["llm_tags"]))
    return 0


def cmd_rules(a: argparse.Namespace) -> int:
    data = {
        "title_max": rules.TITLE_MAX,
        "title_card_safe": rules.TITLE_CARD_SAFE,
        "tags_max": rules.TAGS_MAX,
        "tag_max_len": rules.TAG_MAX_LEN,
        "description_max": rules.DESC_MAX,
        "image_recommended": list(rules.IMG_RECOMMENDED),
        "image_min": list(rules.IMG_MIN),
        "image_max": list(rules.IMG_MAX),
        "gallery": {"images": rules.GALLERY_MAX_IMAGES, "videos": rules.GALLERY_MAX_VIDEOS, "pdfs": rules.GALLERY_MAX_PDFS},
        "seller_fee": rules.SELLER_FEE,
    }
    print(json.dumps(data, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="fiverr-gig", description="Offline Fiverr seller toolkit.")
    p.add_argument("--version", action="version", version=f"fiverr-gig {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("audit", help="score a gig 0-100 and list fixes")
    s.add_argument("file", help="gig as .json, .yaml/.yml or .md (a config with a 'gigs' list audits all)")
    s.add_argument("--json", action="store_true")
    s.add_argument("--min-score", type=int, default=None, help="exit 1 if any gig scores below this")
    s.set_defaults(fn=cmd_audit)

    s = sub.add_parser("lint", help="flag off-platform / payment words in a message")
    s.add_argument("file", nargs="?", help="message file, or '-' for stdin")
    s.add_argument("--text", help="message text directly")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_lint)

    s = sub.add_parser("price", help="net after Fiverr's 20%% fee, ladder, hourly equivalent")
    g = s.add_mutually_exclusive_group(required=True)
    g.add_argument("--gross", type=float, help="sticker price in USD")
    g.add_argument("--net", type=float, help="amount you want to keep; prints the sticker to quote")
    g.add_argument("--ladder", type=float, help="Basic price; suggests Standard and Premium")
    s.add_argument("--hours", type=float, help="hours of work, for a net hourly rate")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_price)

    s = sub.add_parser("keywords", help="tag and title ideas from a seed niche")
    s.add_argument("seed", nargs="+", help="seed niche; quotes optional (keywords logo design)")
    s.add_argument("--llm", action="store_true", help="also ask an OpenAI-compatible endpoint (needs FIVERR_GIG_LLM_* env vars)")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_keywords)

    s = sub.add_parser("rules", help="print the limits the tools check")
    s.set_defaults(fn=cmd_rules)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
