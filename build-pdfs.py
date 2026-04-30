#!/usr/bin/env python3
"""
build-pdfs.py — generate editorial-design per-gig PDFs from gig-config.json.

Pipeline:
  1. Read gig-config.json
  2. For each gig: render standalone HTML (cover page + content sheet)
  3. Run Chrome --headless --print-to-pdf to produce PDF
  4. Save into ./pdfs/

Cover page  : dark plum gradient, huge gig#, wave/phase pill, big serif title,
              accent rule, intro paragraph, author + url footer.
Content page: bone background, Fraunces serif headers, Inter body, plum
              underlined section labels, white pricing cards (STANDARD inverted),
              magenta-accent FAQ blocks.

Requirements:
  - Python 3.8+
  - Google Chrome installed (Windows path auto-detected; pass --chrome PATH otherwise)

Usage:
  python build-pdfs.py
  python build-pdfs.py --config gig-config.json --out pdfs --chrome "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
"""
from __future__ import annotations
import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# ─── Chrome auto-detect ────────────────────────────────────────────────────
def find_chrome() -> str | None:
    candidates = []
    if platform.system() == "Windows":
        candidates += [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        ]
    elif platform.system() == "Darwin":
        candidates += [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        ]
    else:  # Linux
        for name in ("google-chrome", "chromium", "chromium-browser", "microsoft-edge"):
            p = shutil.which(name)
            if p:
                return p
    for c in candidates:
        if c and Path(c).exists():
            return c
    return None

# ─── Helpers ───────────────────────────────────────────────────────────────
def slugify(s: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s[:80]

def html_escape(s: str) -> str:
    return (s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")
             .replace('"', "&quot;"))

def desc_to_html(desc: str) -> str:
    """Convert plain-text desc (with \\n bullets) to safe HTML w/ paragraphs + bullet UL."""
    paras = [p.strip() for p in desc.split("\n\n") if p.strip()]
    out = []
    for p in paras:
        lines = p.split("\n")
        # bullet block? (lines starting with • or →)
        if all(re.match(r"^[•→\-\*]\s+", line) for line in lines if line.strip()):
            items = [re.sub(r"^[•→\-\*]\s+", "", line) for line in lines if line.strip()]
            out.append("<ul>" + "".join(f"<li>{html_escape(i)}</li>" for i in items) + "</ul>")
        else:
            out.append("<p>" + html_escape(p).replace("\n", "<br>") + "</p>")
    return "\n".join(out)

# ─── PRINT_CSS (editorial design) ──────────────────────────────────────────
PRINT_CSS = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,700;9..144,900&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
@page { size: A4; margin: 14mm 14mm 16mm 14mm; }
@page :first { margin: 0; }
*{box-sizing:border-box}
html,body{background:#FAF6F0!important}
body{color:#1a1a1a!important;font-family:'Inter',-apple-system,sans-serif;font-size:10.5pt;line-height:1.55;margin:0;padding:0}

/* ── COVER ── */
.cover{page-break-after:always;height:297mm;width:210mm;background:linear-gradient(135deg,#1a0a24 0%,#2d0a3d 55%,#4a0e5e 100%);color:#fff;padding:28mm 22mm;position:relative;display:flex;flex-direction:column;justify-content:space-between}
.cover::before{content:"";position:absolute;top:0;right:0;width:55%;height:100%;background:radial-gradient(circle at 80% 30%,rgba(224,64,251,.25) 0%,transparent 60%);pointer-events:none}
.cv-top{display:flex;align-items:center;justify-content:space-between;position:relative;z-index:2}
.cv-brand{font-family:'Fraunces',serif;font-weight:900;font-size:14pt;letter-spacing:.5px;color:#e040fb}
.cv-meta{font-size:8pt;letter-spacing:1.5px;text-transform:uppercase;color:rgba(255,255,255,.55)}
.cv-mid{position:relative;z-index:2}
.cv-num{font-family:'Fraunces',serif;font-weight:900;font-size:90pt;line-height:.85;color:rgba(224,64,251,.18);letter-spacing:-3px;margin-bottom:6mm}
.cv-tag{display:inline-block;padding:5px 12px;border:1px solid rgba(224,64,251,.6);color:#e040fb;font-size:8.5pt;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;border-radius:50px;margin-bottom:8mm}
.cv-title{font-family:'Fraunces',serif;font-weight:700;font-size:32pt;line-height:1.1;color:#fff;margin:0 0 10mm 0;max-width:145mm}
.cv-rule{width:60mm;height:3px;background:#e040fb;margin-bottom:6mm}
.cv-desc{font-size:11pt;line-height:1.55;color:rgba(255,255,255,.78);max-width:140mm;font-weight:400}
.cv-bot{position:relative;z-index:2;display:flex;justify-content:space-between;align-items:flex-end;padding-top:10mm;border-top:1px solid rgba(255,255,255,.12)}
.cv-author{font-family:'Fraunces',serif;font-size:13pt;font-weight:700;color:#fff}
.cv-author small{display:block;font-family:'Inter',sans-serif;font-weight:400;font-size:9pt;color:rgba(255,255,255,.55);margin-top:3px;letter-spacing:1px;text-transform:uppercase}
.cv-url{font-size:9pt;color:rgba(255,255,255,.55);font-weight:500;letter-spacing:.8px}

/* ── CONTENT ── */
.sheet{padding:0}
.sheet::before{content:"__BRAND__ - Fiverr Gig Sheet";display:block;font-size:8pt;letter-spacing:2px;text-transform:uppercase;color:#8a6f4d;padding-bottom:5mm;margin-bottom:8mm;border-bottom:1px solid rgba(0,0,0,.1)}
.sheet::after{content:"__URL__ - __NAME__";display:block;margin-top:10mm;padding-top:4mm;border-top:1px solid rgba(0,0,0,.08);font-size:8pt;letter-spacing:1.5px;color:#8a6f4d;text-align:center;text-transform:uppercase}
.row{page-break-inside:avoid;margin-bottom:7mm}
.lbl{font-family:'Fraunces',serif;font-weight:700;color:#5a1875;font-size:9pt;letter-spacing:2px;text-transform:uppercase;margin-bottom:3mm;padding-bottom:2mm;border-bottom:1px solid rgba(90,24,117,.18);display:block}
.val{font-size:10.5pt;line-height:1.6;color:#1a1a1a}
.val p{margin:0 0 2mm 0}
.val ul{margin:2mm 0;padding-left:4mm}
.val li{margin-bottom:1.2mm}
.val.mono{font-family:'Courier New',monospace;font-size:10pt;background:#f0e9dc;padding:6px 10px;border-radius:4px;color:#5a1875}
.tags{display:flex;flex-wrap:wrap;gap:2mm}
.tag{background:#f0e9dc;color:#5a1875;font-size:9pt;font-weight:600;padding:3px 9px;border-radius:50px;letter-spacing:.3px}
/* Pricing */
.pricing-cards{display:grid;grid-template-columns:repeat(3,1fr);gap:5mm;margin-top:2mm}
.ptier{background:#fff;border:1px solid rgba(0,0,0,.1);color:#1a1a1a;padding:6mm 5mm;border-radius:4px;position:relative}
.ptier.std{background:#1a0a24;border-color:#1a0a24;color:#fff;transform:scale(1.02)}
.ptier.std::before{content:"RECOMMENDED";position:absolute;top:-9px;left:50%;transform:translateX(-50%);background:#e040fb;color:#fff;font-size:7pt;font-weight:700;letter-spacing:1.5px;padding:3px 10px;border-radius:50px}
.ptier .pt-tag{font-family:'Fraunces',serif;font-weight:700;color:#8a6f4d;font-size:8pt;letter-spacing:2px;margin-bottom:3mm;display:block}
.ptier.std .pt-tag{color:#e040fb}
.ptier .pt-title{font-family:'Fraunces',serif;font-weight:700;color:#1a1a1a;font-size:11pt;line-height:1.25;margin-bottom:2mm;display:block}
.ptier.std .pt-title{color:#fff}
.ptier .pt-price{font-family:'Fraunces',serif;font-weight:900;color:#5a1875;font-size:18pt;line-height:1;margin-bottom:3mm;display:block}
.ptier.std .pt-price{color:#e040fb}
.ptier .pt-meta{font-size:8.5pt;color:#8a6f4d;margin-bottom:3mm;letter-spacing:.3px}
.ptier.std .pt-meta{color:rgba(255,255,255,.55)}
.ptier ul{margin:0;padding-left:4mm;color:#555;font-size:9pt;line-height:1.5}
.ptier.std ul{color:rgba(255,255,255,.78)}
.ptier li{margin-bottom:1mm}
/* FAQ */
.faqs{display:flex;flex-direction:column;gap:3mm}
.faq{background:#fff;border-left:3px solid #e040fb;padding:4mm 5mm;border-radius:0 4px 4px 0;page-break-inside:avoid}
.faq-q{font-family:'Fraunces',serif;font-weight:700;color:#1a0a24;font-size:10.5pt;margin-bottom:2mm;line-height:1.35}
.faq-a{color:#3a3a3a;font-size:10pt;line-height:1.6}
.kv{display:grid;grid-template-columns:max-content 1fr;gap:3mm 6mm;font-size:10pt}
.kv dt{color:#5a1875;font-weight:700;font-family:'Fraunces',serif}
.kv dd{margin:0;color:#1a1a1a}
</style>
"""

# ─── Templating ────────────────────────────────────────────────────────────
def build_cover(gig: dict, seller: dict) -> str:
    title = gig.get("title", "")
    pretty = re.sub(r"^I will\s+", "", title, flags=re.I)
    pretty = (pretty[:1].upper() + pretty[1:]) if pretty else title
    intro_src = gig.get("img", {}).get("pdfWhat") or gig.get("desc", "").split("\n\n")[0]
    intro = intro_src.strip()
    if len(intro) > 280:
        intro = intro[:277].rsplit(" ", 1)[0] + "..."
    phase = gig.get("phase", 1)
    phase_lbl = {1: "PHASE 1 - LAUNCH NOW", 2: "PHASE 2 - AFTER 5 REVIEWS", 3: "PHASE 3 - AFTER LEVEL 2"}.get(phase, f"PHASE {phase}")
    brand = html_escape(seller.get("brand") or seller.get("name") or "")
    name = html_escape(seller.get("name", ""))
    url = html_escape(seller.get("website", ""))
    return f"""
<div class="cover">
  <div class="cv-top">
    <div class="cv-brand">{brand}</div>
    <div class="cv-meta">Fiverr Gig Sheet</div>
  </div>
  <div class="cv-mid">
    <div class="cv-num">#{gig['id']:02d}</div>
    <div class="cv-tag">{phase_lbl}</div>
    <h1 class="cv-title">{html_escape(pretty)}</h1>
    <div class="cv-rule"></div>
    <p class="cv-desc">{html_escape(intro)}</p>
  </div>
  <div class="cv-bot">
    <div class="cv-author">{name} <small>{brand}</small></div>
    <div class="cv-url">{url}</div>
  </div>
</div>
"""

def build_pricing(p: dict) -> str:
    def card(tier_key: str, classes: str, tier_label: str) -> str:
        t = p.get(tier_key, {})
        items = "".join(f"<li>{html_escape(i)}</li>" for i in t.get("items", []))
        meta = f"{html_escape(t.get('del',''))} - {html_escape(str(t.get('rev','')))} revisions"
        return f"""<div class="ptier {classes}">
  <span class="pt-tag">{tier_label}</span>
  <span class="pt-title">{html_escape(t.get('title') or t.get('name',''))}</span>
  <span class="pt-price">${t.get('price','')}</span>
  <div class="pt-meta">{meta}</div>
  <ul>{items}</ul>
</div>"""
    return f'<div class="pricing-cards">{card("basic","","BASIC")}{card("standard","std","STANDARD")}{card("premium","","PREMIUM")}</div>'

def build_faqs(faqs: list[dict]) -> str:
    if not faqs:
        return ""
    blocks = "".join(
        f'<div class="faq"><div class="faq-q">{html_escape(f.get("q",""))}</div>'
        f'<div class="faq-a">{html_escape(f.get("a",""))}</div></div>'
        for f in faqs
    )
    return f'<div class="row"><div class="lbl">Frequently Asked Questions</div><div class="faqs">{blocks}</div></div>'

def build_sheet(gig: dict, seller: dict) -> str:
    tags = "".join(f'<span class="tag">{html_escape(t)}</span>' for t in gig.get("tags", []))
    desc_html = desc_to_html(gig.get("desc", ""))
    pricing = build_pricing(gig.get("pricing", {}))
    faqs = build_faqs(gig.get("faqs", []))
    css = PRINT_CSS.replace("__BRAND__", html_escape(seller.get("brand") or "SkynetLabs"))\
                   .replace("__URL__", html_escape(seller.get("website", "")))\
                   .replace("__NAME__", html_escape(seller.get("name", "")))
    cover = build_cover(gig, seller)
    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>Fiverr Gig #{gig['id']} - {html_escape(gig.get('title',''))}</title>
{css}
</head><body>
{cover}
<div class="sheet">
  <div class="row"><div class="lbl">Gig Title</div><div class="val"><p>{html_escape(gig.get('title',''))}</p></div></div>
  <div class="row"><div class="lbl">Category</div><div class="val"><p>{html_escape(gig.get('cat',''))}</p></div></div>
  <div class="row"><div class="lbl">Tags ({len(gig.get('tags',[]))} / 5)</div><div class="val"><div class="tags">{tags}</div></div></div>
  <div class="row"><div class="lbl">Description ({len(gig.get('desc',''))} / 1200)</div><div class="val">{desc_html}</div></div>
  <div class="row"><div class="lbl">Pricing Tiers</div>{pricing}</div>
  {faqs}
  <div class="row"><div class="lbl">Cross-Sell Funnel</div><div class="val"><p>{html_escape(gig.get('xsell',''))}</p></div></div>
  <div class="row"><div class="lbl">Competition</div><div class="val"><p>{html_escape(gig.get('competition',''))}</p></div></div>
</div>
</body></html>"""

# ─── Chrome runner ─────────────────────────────────────────────────────────
def render_pdf(chrome: str, html_path: Path, pdf_path: Path, profile_dir: Path) -> bool:
    pdf_abs = pdf_path.resolve()
    html_abs = html_path.resolve()
    cmd = [
        chrome, "--headless", "--disable-gpu",
        f"--user-data-dir={profile_dir.resolve()}",
        f"--print-to-pdf={pdf_abs}",
        "--no-pdf-header-footer",
        "--virtual-time-budget=3000",
        f"file:///{html_abs.as_posix()}",
    ]
    proc = subprocess.run(cmd, capture_output=True, timeout=90)
    if not (pdf_abs.exists() and pdf_abs.stat().st_size > 1000):
        err = (proc.stderr or b"").decode("utf-8", errors="replace")[:500]
        if err:
            print(f"    chrome stderr: {err}")
        return False
    return True

# ─── Main ──────────────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser(description="Build editorial-design PDFs from gig-config.json")
    ap.add_argument("--config", default="gig-config.json", help="Gig config JSON path")
    ap.add_argument("--out", default="pdfs", help="Output directory for PDFs")
    ap.add_argument("--chrome", default=None, help="Path to Chrome/Edge binary")
    ap.add_argument("--keep-html", action="store_true", help="Keep generated HTML files")
    args = ap.parse_args()

    cfg_path = Path(args.config)
    if not cfg_path.exists():
        print(f"ERROR: {cfg_path} not found.", file=sys.stderr)
        print("Run /fiverr-optimize in Claude Code to generate it.", file=sys.stderr)
        return 1

    chrome = args.chrome or find_chrome()
    if not chrome:
        print("ERROR: Chrome / Edge binary not found. Pass --chrome PATH.", file=sys.stderr)
        return 1
    print(f"Chrome: {chrome}")

    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    seller = cfg.get("seller", {})
    gigs = cfg.get("gigs", [])
    if not gigs:
        print("ERROR: No gigs in config.", file=sys.stderr)
        return 1

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    html_dir = out_dir / "_html"
    html_dir.mkdir(exist_ok=True)

    profile_dir = Path(tempfile.gettempdir()) / "fiverr-pdf-chrome-profile"
    profile_dir.mkdir(parents=True, exist_ok=True)

    ok_count = 0
    for gig in gigs:
        gid = gig["id"]
        slug = slugify(gig.get("title", f"gig-{gid}"))
        base = f"gig-{gid:02d}-{slug}"
        html_path = html_dir / f"{base}.html"
        pdf_path = out_dir / f"{base}.pdf"
        html_path.write_text(build_sheet(gig, seller), encoding="utf-8")
        ok = render_pdf(chrome, html_path, pdf_path, profile_dir)
        sz = pdf_path.stat().st_size if pdf_path.exists() else 0
        print(f"  gig {gid:02d}: {'OK' if ok else 'FAIL'}  {pdf_path.name}  ({sz//1024} KB)")
        if ok:
            ok_count += 1

    if not args.keep_html:
        shutil.rmtree(html_dir, ignore_errors=True)

    print(f"\n{ok_count}/{len(gigs)} PDFs built -> {out_dir.resolve()}")
    return 0 if ok_count == len(gigs) else 1

if __name__ == "__main__":
    sys.exit(main())
