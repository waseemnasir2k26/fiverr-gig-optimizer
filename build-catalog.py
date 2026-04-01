#!/usr/bin/env python3
"""
Fiverr Gig Optimizer — Build Script
Reads gig-config.json and generates a complete HTML catalog with:
- Canvas thumbnails (1280x769px)
- Copy-paste titles, descriptions, tags
- Download PNG / PDF export per gig
- Cross-sell funnel diagram
- Action plan checklist

Usage:
    python build-catalog.py                    # Uses gig-config.json
    python build-catalog.py my-config.json     # Uses custom config
    python build-catalog.py --no-photo         # Skip photo embedding
"""
import json, base64, os, sys

# ─── Load config ───
config_path = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'gig-config.json'
no_photo = '--no-photo' in sys.argv

if not os.path.exists(config_path):
    print(f"ERROR: {config_path} not found.")
    print("Run /fiverr-optimize in Claude Code to generate it, or copy config-example.json")
    sys.exit(1)

with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)

seller = config['seller']
strategy = config.get('strategy', {})
gigs = config['gigs']

# ─── Load photo as base64 ───
photo_b64 = ""
if not no_photo and seller.get('photo'):
    photo_path = seller['photo']
    # Try multiple paths
    for p in [photo_path, os.path.join(os.path.dirname(config_path), photo_path)]:
        if os.path.exists(p):
            with open(p, 'rb') as f:
                raw = base64.b64encode(f.read()).decode()
                ext = os.path.splitext(p)[1].lower().replace('.', '')
                mime = {'png': 'image/png', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'webp': 'image/webp'}.get(ext, 'image/png')
                photo_b64 = f"data:{mime};base64,{raw}"
            print(f"Photo loaded: {p} ({len(raw)//1024}KB)")
            break
    else:
        # Check if it's already base64
        if photo_path.endswith('.txt') or photo_path.endswith('.b64'):
            for p in [photo_path, os.path.join(os.path.dirname(config_path), photo_path)]:
                if os.path.exists(p):
                    with open(p, 'r') as f:
                        b64_content = f.read().strip()
                    if b64_content.startswith('data:'):
                        photo_b64 = b64_content
                    else:
                        photo_b64 = f"data:image/png;base64,{b64_content}"
                    print(f"Photo loaded from base64 file: {p}")
                    break
        if not photo_b64:
            print(f"WARNING: Photo not found at {photo_path} — generating without photo")

# ─── Build gig data as JSON string ───
gigs_json = json.dumps(gigs, ensure_ascii=False)

# ─── Count phases ───
p1 = [g for g in gigs if g['phase'] == 1]
p2 = [g for g in gigs if g['phase'] == 2]
p3 = [g for g in gigs if g['phase'] == 3]

# ─── Build cross-sell funnel ASCII ───
def build_funnel(gigs):
    lines = []
    if len(gigs) <= 3:
        for g in gigs:
            lines.append(f"  Gig #{g['id']}: {g['img']['headline']} (${g['pricing']['basic']['price']}-${g['pricing']['premium']['price']})")
        return '\n'.join(lines)

    # Find bundle/premium gig (highest price)
    by_price = sorted(gigs, key=lambda g: g['pricing']['premium']['price'], reverse=True)
    top = by_price[0]
    mid = [g for g in gigs if g['phase'] == 2 and g['id'] != top['id']]
    base = [g for g in gigs if g['phase'] == 1]

    lines.append(f"                    +----------------------------------+")
    lines.append(f"                    |  {top['img']['headline']:^32s}|")
    lines.append(f"                    |  (Phase {top['phase']} — Gig #{top['id']})              |")
    lines.append(f"                    +----------------------------------+")
    lines.append(f"                            |            |")

    if mid:
        m1 = mid[0] if len(mid) > 0 else None
        m2 = mid[1] if len(mid) > 1 else None
        if m1 and m2:
            lines.append(f"          +-----------------+  +----------------+")
            lines.append(f"          | {m1['img']['headline'][:15]:^15s} |  | {m2['img']['headline'][:14]:^14s} |")
            lines.append(f"          | (Phase {m1['phase']} - #{m1['id']})   |  | (Phase {m2['phase']} - #{m2['id']})  |")
            lines.append(f"          +-----------------+  +----------------+")
        elif m1:
            lines.append(f"               +-----------------+")
            lines.append(f"               | {m1['img']['headline'][:15]:^15s} |")
            lines.append(f"               | (Phase {m1['phase']} - #{m1['id']})   |")
            lines.append(f"               +-----------------+")

    lines.append(f"               |      |               |")
    for g in base:
        lines.append(f"    +-- Gig #{g['id']}: {g['img']['headline']} (${g['pricing']['basic']['price']}-${g['pricing']['premium']['price']})")

    return '\n'.join(lines)

funnel_ascii = build_funnel(gigs)

# ─── Build action plan ───
action_items = [
    f"<li><strong>TODAY:</strong> Delete/pause underperforming gigs that dilute your authority</li>",
    f"<li><strong>THIS WEEK:</strong> Create Phase 1 gigs ({len(p1)} gigs) — lowest competition, fastest to get reviews</li>",
    f"<li><strong>WEEK 2-3:</strong> Get 5 reviews on each (offer launch pricing to first 5 buyers)</li>",
    f"<li><strong>WEEK 2-3:</strong> Respond to EVERY message within 1 hour (critical algorithm signal)</li>",
    f"<li><strong>WEEK 3-4:</strong> Add gig video to each (+30% impressions, 2x orders)</li>",
]
if p2:
    action_items.append(f"<li><strong>WEEK 6+:</strong> Launch Phase 2 gigs ({len(p2)} gigs) after 5+ reviews</li>")
if p3:
    action_items.append(f"<li><strong>AFTER LEVEL 2:</strong> Launch Phase 3 gigs ({len(p3)} gigs) based on what's working</li>")

action_html = '\n    '.join(action_items)

brand_name = seller.get('brand', seller['name'])
website = seller.get('website', '')
watermark = f"{brand_name}"
if website:
    watermark += f"  ·  {website}"

# ─── Generate HTML ───
html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Fiverr Strategy Catalog - {brand_name}</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=Montserrat:wght@700;800;900&display=swap');
:root{{--bg:#050507;--card:#0c0c10;--bdr:#1a1a22;--txt:#e2e2e6;--mut:#777;--grn:#1DBF73;--pur:#a855f7;--red:#ef4444;--gld:#FFD700;--blu:#3b82f6;--cya:#06b6d4;--ora:#f97316;--lim:#84cc16}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Inter',system-ui,sans-serif;background:var(--bg);color:var(--txt);line-height:1.6}}
.hero{{padding:48px 20px 40px;text-align:center;background:linear-gradient(160deg,#050507,#080c12,#050507,#0a0710);border-bottom:1px solid var(--bdr);position:relative;overflow:hidden}}
.hero::before{{content:'';position:absolute;inset:0;background:radial-gradient(ellipse at 30% 50%,rgba(29,191,115,.06),transparent 55%),radial-gradient(ellipse at 70% 50%,rgba(168,85,247,.04),transparent 55%)}}
.hi{{position:relative;z-index:1;max-width:900px;margin:0 auto}}
.brow{{display:flex;justify-content:center;gap:7px;margin-bottom:14px;flex-wrap:wrap}}
.bb{{display:inline-block;padding:3px 11px;border-radius:18px;font-size:9px;font-weight:700;letter-spacing:.7px}}
.bb-g{{background:rgba(29,191,115,.1);border:1px solid rgba(29,191,115,.25);color:var(--grn)}}
.bb-p{{background:rgba(168,85,247,.1);border:1px solid rgba(168,85,247,.25);color:var(--pur)}}
.bb-b{{background:rgba(59,130,246,.1);border:1px solid rgba(59,130,246,.25);color:var(--blu)}}
.bb-gl{{background:rgba(255,215,0,.1);border:1px solid rgba(255,215,0,.25);color:var(--gld)}}
h1{{font-size:38px;font-weight:900;letter-spacing:-2px;line-height:1.05;margin-bottom:10px}}
h1 .g{{color:var(--grn)}} h1 .p{{color:var(--pur)}} h1 .gl{{color:var(--gld)}}
.hero>div>p{{font-size:14px;color:var(--mut);max-width:680px;margin:0 auto 20px}}
.srow{{display:flex;justify-content:center;gap:28px;flex-wrap:wrap}}
.st{{text-align:center}}.sv{{font-size:22px;font-weight:800}}.sv.g{{color:var(--grn)}}.sv.p{{color:var(--pur)}}.sv.b{{color:var(--blu)}}.sv.gl{{color:var(--gld)}}
.sl{{font-size:9px;color:var(--mut);text-transform:uppercase;letter-spacing:1px;margin-top:2px}}
.funnel{{max-width:1000px;margin:30px auto 0;padding:20px;background:rgba(255,255,255,.015);border:1px solid var(--bdr);border-radius:12px}}
.funnel h3{{font-size:13px;font-weight:800;color:var(--grn);text-transform:uppercase;letter-spacing:1.5px;margin-bottom:12px;text-align:center}}
.funnel pre{{font-size:11px;color:#888;line-height:1.6;overflow-x:auto;text-align:center;white-space:pre}}
.topbar{{max-width:1200px;margin:20px auto;padding:0 20px;display:flex;gap:10px;flex-wrap:wrap;justify-content:center}}
.topbtn{{padding:10px 20px;border-radius:8px;font-size:12px;font-weight:700;cursor:pointer;border:none;transition:all .2s;letter-spacing:.5px}}
.topbtn-pdf{{background:var(--red);color:#fff}}.topbtn-pdf:hover{{background:#dc2626}}
.topbtn-all{{background:var(--pur);color:#fff}}.topbtn-all:hover{{background:#9333ea}}
.topbtn-copy{{background:var(--grn);color:#000}}.topbtn-copy:hover{{background:#19a864}}
.con{{max-width:1200px;margin:0 auto;padding:10px 20px 60px}}
.sec{{display:flex;align-items:center;gap:14px;margin:36px 0 20px}}
.sec .ln{{flex:1;height:1px;background:var(--bdr)}}
.sec .tx{{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:2px;white-space:nowrap}}
.sec .tx.g{{color:var(--grn)}}.sec .tx.p{{color:var(--pur)}}.sec .tx.b{{color:var(--blu)}}
.gc{{background:var(--card);border:1px solid var(--bdr);border-radius:12px;margin-bottom:28px;overflow:hidden;position:relative;transition:border-color .3s}}
.gc:hover{{border-color:rgba(29,191,115,.3)}}
.gc.p1{{border-color:rgba(29,191,115,.35)}}.gc.p1:hover{{border-color:rgba(29,191,115,.55)}}
.gc.p2{{border-color:rgba(168,85,247,.3)}}.gc.p2:hover{{border-color:rgba(168,85,247,.5)}}
.gc.p3{{border-color:rgba(59,130,246,.2)}}.gc.p3:hover{{border-color:rgba(59,130,246,.4)}}
.cbs{{position:absolute;top:12px;right:12px;display:flex;gap:4px;z-index:10}}
.cb{{padding:2px 8px;border-radius:4px;font-size:8px;font-weight:700;letter-spacing:.4px;backdrop-filter:blur(6px)}}
.cb-p1{{background:rgba(29,191,115,.3);color:var(--grn)}}
.cb-p2{{background:rgba(168,85,247,.25);color:var(--pur)}}
.cb-p3{{background:rgba(59,130,246,.2);color:var(--blu)}}
.gn{{position:absolute;top:12px;left:12px;width:32px;height:32px;background:rgba(0,0,0,.5);border:1px solid rgba(255,255,255,.08);border-radius:8px;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:12px;color:#fff;z-index:10;backdrop-filter:blur(6px)}}
.gc.p1 .gn{{background:rgba(29,191,115,.2);color:#6ee7b7}}
.gc.p2 .gn{{background:rgba(168,85,247,.2);color:#d8b4fe}}
.gc.p3 .gn{{background:rgba(59,130,246,.15);color:#93c5fd}}
.rib{{position:absolute;top:18px;right:-34px;padding:3px 42px;font-size:8px;font-weight:800;letter-spacing:1.5px;transform:rotate(45deg);z-index:11}}
.rib-1{{background:linear-gradient(135deg,#1DBF73,#059669);color:#fff}}
.rib-2{{background:linear-gradient(135deg,#a855f7,#7c3aed);color:#fff}}
.rib-3{{background:linear-gradient(135deg,#3b82f6,#2563eb);color:#fff}}
.rib-b{{background:linear-gradient(135deg,#FFD700,#F59E0B);color:#000}}
.gb{{width:100%;overflow:hidden}}.gb canvas{{width:100%;display:block}}
.gcn{{padding:20px 24px 18px}}
.gcat{{font-size:9px;color:var(--grn);font-weight:700;text-transform:uppercase;letter-spacing:.7px;margin-bottom:6px}}
.gt{{font-size:17px;font-weight:700;color:#fff;line-height:1.3;margin-bottom:3px}}
.cc{{font-size:8px;color:#444;font-weight:400;margin-left:5px}}
.phase-tag{{display:inline-block;padding:3px 10px;border-radius:4px;font-size:9px;font-weight:700;margin:6px 0 4px;letter-spacing:.5px}}
.pt-1{{background:rgba(29,191,115,.1);color:var(--grn);border:1px solid rgba(29,191,115,.2)}}
.pt-2{{background:rgba(168,85,247,.1);color:var(--pur);border:1px solid rgba(168,85,247,.2)}}
.pt-3{{background:rgba(59,130,246,.1);color:var(--blu);border:1px solid rgba(59,130,246,.2)}}
.comp{{font-size:10px;color:#555;margin:4px 0 10px;display:flex;gap:12px;flex-wrap:wrap}}
.comp span{{display:flex;align-items:center;gap:3px}}
.comp .lo{{color:#22c55e}}.comp .md{{color:var(--ora)}}.comp .hi{{color:var(--red)}}
.xsell{{background:rgba(29,191,115,.04);border:1px solid rgba(29,191,115,.1);border-radius:8px;padding:10px 14px;margin:10px 0 14px;font-size:11px;color:#888;line-height:1.6}}
.xsell strong{{color:var(--grn);font-weight:700}}
.tsec{{margin-bottom:14px}}
.stl{{font-size:8px;color:var(--mut);text-transform:uppercase;letter-spacing:1px;font-weight:700;margin-bottom:6px;display:flex;align-items:center;gap:6px}}
.stl .m{{background:rgba(255,255,255,.03);padding:1px 6px;border-radius:3px;font-size:7px;color:#555}}
.tl{{display:flex;flex-wrap:wrap;gap:5px}}
.tag{{background:rgba(29,191,115,.06);border:1px solid rgba(29,191,115,.13);color:rgba(29,191,115,.8);padding:3px 9px;border-radius:4px;font-size:10px;font-weight:500}}
.dsec{{margin-bottom:18px}}
.desc{{font-size:12px;color:#aaa;line-height:1.7;white-space:pre-wrap;max-height:180px;overflow:hidden;transition:max-height .3s}}
.desc.open{{max-height:none}}
.toggle-desc{{font-size:10px;color:var(--grn);cursor:pointer;margin-top:4px;display:inline-block;font-weight:600}}
.psec{{margin-bottom:14px}}
.pgrid{{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}}
.tier{{background:rgba(255,255,255,.015);border:1px solid var(--bdr);border-radius:8px;padding:14px 12px;text-align:center;position:relative;transition:all .25s}}
.tier:hover{{border-color:rgba(29,191,115,.2)}}
.tier.best{{border-color:var(--grn);background:rgba(29,191,115,.03)}}
.tier.best::after{{content:'POPULAR';position:absolute;top:-7px;left:50%;transform:translateX(-50%);background:var(--grn);color:#000;font-size:7px;font-weight:800;padding:1px 7px;border-radius:3px;letter-spacing:.6px}}
.tn{{font-size:9px;font-weight:700;color:#555;text-transform:uppercase;letter-spacing:.6px}}
.tt{{font-size:11px;font-weight:600;color:#ccc;margin:4px 0 6px;min-height:28px;display:flex;align-items:center;justify-content:center}}
.tp{{font-size:26px;font-weight:800;color:var(--grn);margin-bottom:8px}}
.tl2{{list-style:none;text-align:left}}
.tl2 li{{font-size:10px;color:#888;padding:2px 0;display:flex;align-items:flex-start;gap:4px}}
.ck{{color:var(--grn);font-weight:700;flex-shrink:0;font-size:10px}}
.acts{{display:flex;gap:6px;flex-wrap:wrap;padding-top:14px;border-top:1px solid var(--bdr)}}
.btn{{padding:6px 12px;border-radius:6px;font-size:10px;font-weight:600;cursor:pointer;border:none;transition:all .2s;display:flex;align-items:center;gap:4px}}
.btn-c{{background:rgba(29,191,115,.08);color:var(--grn);border:1px solid rgba(29,191,115,.15)}}.btn-c:hover{{background:rgba(29,191,115,.15)}}
.btn-a{{background:rgba(168,85,247,.08);color:var(--pur);border:1px solid rgba(168,85,247,.15)}}.btn-a:hover{{background:rgba(168,85,247,.15)}}
.btn-d{{background:rgba(255,255,255,.03);color:#888;border:1px solid var(--bdr)}}.btn-d:hover{{background:rgba(255,255,255,.06)}}
.btn-pdf{{background:rgba(239,68,68,.08);color:var(--red);border:1px solid rgba(239,68,68,.15)}}.btn-pdf:hover{{background:rgba(239,68,68,.15)}}
.toast{{position:fixed;bottom:20px;right:20px;background:var(--grn);color:#000;padding:9px 16px;border-radius:8px;font-size:11px;font-weight:600;opacity:0;transform:translateY(8px);transition:all .3s;z-index:999;pointer-events:none}}
.toast.show{{opacity:1;transform:translateY(0)}}
.ft{{text-align:center;padding:30px 20px;border-top:1px solid var(--bdr)}}.ft p{{font-size:11px;color:#444}}.ft a{{color:var(--grn);text-decoration:none}}
.action-plan{{max-width:1000px;margin:0 auto 30px;padding:24px;background:rgba(255,255,255,.015);border:1px solid var(--bdr);border-radius:12px}}
.action-plan h3{{font-size:13px;font-weight:800;color:var(--red);text-transform:uppercase;letter-spacing:1.5px;margin-bottom:14px}}
.action-plan ol{{padding-left:20px;font-size:12px;color:#aaa;line-height:2}}
.action-plan ol li strong{{color:var(--grn)}}
.credit{{max-width:1000px;margin:10px auto 20px;padding:14px;background:rgba(29,191,115,.03);border:1px solid rgba(29,191,115,.1);border-radius:8px;text-align:center;font-size:11px;color:#666}}
.credit a{{color:var(--grn);font-weight:600;text-decoration:none}}
@media(max-width:768px){{h1{{font-size:26px}}.pgrid{{grid-template-columns:1fr}}.gcn{{padding:16px 14px}}.funnel pre{{font-size:9px}}}}
@media print{{body{{background:#fff;color:#000}}.hero,.topbar,.acts,.cbs,.gn,.rib,.toast,.funnel,.action-plan,.credit{{display:none!important}}.gc{{break-inside:avoid;border:1px solid #ddd;margin-bottom:20px}}.desc{{max-height:none!important;color:#333}}.tag{{border:1px solid #ccc;color:#333}}.tier{{border:1px solid #ddd}}.tp{{color:var(--grn)}}.gt{{color:#000}}.sec .tx{{color:#333}}}}
</style>
</head>
<body>
<div class="hero"><div class="hi">
  <div class="brow">
    <span class="bb bb-g">PHASE 1: LAUNCH NOW</span>
    {"<span class='bb bb-p'>PHASE 2: AFTER 5 REVIEWS</span>" if p2 else ""}
    {"<span class='bb bb-b'>PHASE 3: AFTER LEVEL 2</span>" if p3 else ""}
    <span class="bb bb-gl">RESEARCH-BACKED STRATEGY</span>
  </div>
  <h1>Fiverr <span class="g">Domination</span> <span class="p">Strategy</span></h1>
  <p>Combo-niche gigs targeting low-competition keywords. Phase-based rollout. Every gig cross-sells into the next.</p>
  <div class="srow">
    <div class="st"><div class="sv g">{len(p1)}</div><div class="sl">Phase 1 Gigs</div></div>
    {"<div class='st'><div class='sv p'>" + str(len(p2)) + "</div><div class='sl'>Phase 2 Upsells</div></div>" if p2 else ""}
    {"<div class='st'><div class='sv b'>" + str(len(p3)) + "</div><div class='sl'>Phase 3 Expand</div></div>" if p3 else ""}
    <div class="st"><div class="sv gl">{strategy.get('monthlyTarget', '$10K')}</div><div class="sl">Mo. Target</div></div>
  </div>
  <div class="funnel">
    <h3>Cross-Sell Funnel Map</h3>
    <pre>{funnel_ascii}</pre>
  </div>
</div></div>
<div class="topbar">
  <button class="topbtn topbtn-pdf" onclick="window.print()">Print Full PDF</button>
  <button class="topbtn topbtn-all" onclick="downloadAllPNG()">Download All Thumbnails</button>
  <button class="topbtn topbtn-copy" onclick="copyAllGigs()">Copy All Gigs Text</button>
</div>
<div class="con" id="gc"></div>

<div class="action-plan">
  <h3>Immediate Action Plan</h3>
  <ol>
    {action_html}
  </ol>
</div>

<div class="credit">
  Generated with <a href="https://github.com/waseemnasir2k26/fiverr-gig-optimizer" target="_blank">Fiverr Gig Optimizer</a> — Open source Claude Code skill for Fiverr domination
</div>

<div class="ft">
  <p>{brand_name} {f'&mdash; <a href="https://{website}">{website}</a>' if website else ''} &mdash; Fiverr Strategy Catalog</p>
</div>
<div class="toast" id="toast"></div>

<script>
const PHOTO_B64="{photo_b64}";
const photoImg=new Image();if(PHOTO_B64)photoImg.src=PHOTO_B64;

const G={gigs_json};

const secs={{
  phase1:{{l:"PHASE 1 — LAUNCH NOW ({len(p1)} Combo-Niche Gigs)",c:"g"}},
  phase2:{{l:"PHASE 2 — AFTER 5+ REVIEWS (Premium Upsells)",c:"p"}},
  phase3:{{l:"PHASE 3 — AFTER LEVEL 2 (Strategic Expansion)",c:"b"}}
}};
const WATERMARK="{watermark}";
const con=document.getElementById('gc');let cur="";

G.forEach(g=>{{
  const secKey='phase'+g.phase;
  if(secKey!==cur){{cur=secKey;const s=secs[cur];if(s){{const d=document.createElement('div');d.className='sec';d.innerHTML=`<span class="ln"></span><span class="tx ${{s.c}}">${{s.l}}</span><span class="ln"></span>`;con.appendChild(d)}}}}
  const c=document.createElement('div');
  const cls=g.phase===1?'p1':g.phase===2?'p2':'p3';
  c.className=`gc ${{cls}}`;
  const ribCls=g.phase===1?'rib-1':g.phase===2?'rib-2':'rib-3';
  const ptCls=g.phase===1?'pt-1':g.phase===2?'pt-2':'pt-3';
  const cbCls=g.phase===1?'cb-p1':g.phase===2?'cb-p2':'cb-p3';
  const cid=`c${{g.id}}`,did=`d${{g.id}}`;
  c.innerHTML=`<div class="rib ${{ribCls}}">PHASE ${{g.phase}}</div><div class="gn">${{String(g.id).padStart(2,'0')}}</div>
<div class="cbs"><span class="cb ${{cbCls}}">PHASE ${{g.phase}}</span></div>
<div class="gb"><canvas id="${{cid}}"></canvas></div>
<div class="gcn">
<div class="gcat">${{g.cat}}</div>
<div class="gt">${{g.title}}<span class="cc">${{g.title.length}}/80</span></div>
<div class="phase-tag ${{ptCls}}">PHASE ${{g.phase}}${{g.phase===1?' — LAUNCH NOW':g.phase===2?' — AFTER 5 REVIEWS':' — AFTER LEVEL 2'}}</div>
<div class="comp"><span>Competition: <span class="${{g.compCls}}">${{g.competition}}</span></span></div>
<div class="xsell">${{g.xsell}}</div>
<div class="tsec"><div class="stl">Tags <span class="m">${{g.tags.length}}/5</span></div><div class="tl">${{g.tags.map(t=>`<span class="tag">${{t}}</span>`).join('')}}</div></div>
<div class="dsec"><div class="stl">Description <span class="m">${{g.desc.length}}/1200</span></div><div class="desc" id="${{did}}">${{g.desc}}</div><span class="toggle-desc" onclick="this.previousElementSibling.classList.toggle('open');this.textContent=this.textContent==='Show more'?'Show less':'Show more'">Show more</span></div>
<div class="psec"><div class="stl">Pricing</div><div class="pgrid">${{TH(g.pricing.basic,0)}}${{TH(g.pricing.standard,1)}}${{TH(g.pricing.premium,0)}}</div></div>
<div class="acts">
<button class="btn btn-c" onclick="cp('${{E(g.title)}}','title')">Copy Title</button>
<button class="btn btn-c" onclick="cpE('${{did}}','desc')">Copy Desc</button>
<button class="btn btn-c" onclick="cp('${{g.tags.join(', ')}}','tags')">Copy Tags</button>
<button class="btn btn-a" onclick="cpA(${{g.id}})">Copy All</button>
<button class="btn btn-d" onclick="dl('${{cid}}','gig-${{g.id}}-thumbnail.png')">PNG</button>
<button class="btn btn-pdf" onclick="dlPDF(${{g.id}})">PDF</button>
</div></div>`;
  con.appendChild(c);
}});

function TH(t,b){{return`<div class="tier${{b?' best':''}}"><div class="tn">${{t.name}}</div><div class="tt">${{t.title}}</div><div class="tp">$${{t.price}}</div><ul class="tl2"><li><span class="ck">\\u2713</span>${{t.del}}</li><li><span class="ck">\\u2713</span>${{t.rev}} revisions</li>${{t.items.map(i=>`<li><span class="ck">\\u2713</span>${{i}}</li>`).join('')}}</ul></div>`}}
function E(s){{return s.replace(/'/g,"\\\\'")}}

// ═══════ CENTERED THUMBNAILS ═══════
function renderAll(){{G.forEach(g=>{{const cv=document.getElementById(`c${{g.id}}`);if(cv)RB(cv,g)}})}}
photoImg.onload=()=>renderAll();
if(!PHOTO_B64||photoImg.complete&&photoImg.naturalWidth>0)setTimeout(renderAll,100);

function RB(cv,g){{
  const x=cv.getContext('2d');cv.width=1280;cv.height=769;
  const w=1280,h=769,im=g.img,ac=im.accent,hw=w/2,hh=h/2;

  const bg=x.createLinearGradient(0,0,w,h);
  bg.addColorStop(0,im.bg1);bg.addColorStop(.5,im.bg2);bg.addColorStop(1,im.bg1);
  x.fillStyle=bg;x.fillRect(0,0,w,h);

  x.fillStyle='rgba(255,255,255,.012)';
  for(let gx=0;gx<w;gx+=36)for(let gy=0;gy<h;gy+=36){{x.beginPath();x.arc(gx,gy,.7,0,Math.PI*2);x.fill()}}

  const glow=x.createRadialGradient(hw,hh-30,0,hw,hh-30,450);
  glow.addColorStop(0,HR(ac,.14));glow.addColorStop(.4,HR(ac,.05));glow.addColorStop(1,'transparent');
  x.fillStyle=glow;x.fillRect(0,0,w,h);

  x.strokeStyle=HR(ac,.15);x.lineWidth=1.5;RR(x,6,6,w-12,h-12,12);x.stroke();
  x.strokeStyle=HR(ac,.5);x.lineWidth=2.5;const cn=35;
  x.beginPath();x.moveTo(6,cn+6);x.lineTo(6,6);x.lineTo(cn+6,6);x.stroke();
  x.beginPath();x.moveTo(w-cn-6,6);x.lineTo(w-6,6);x.lineTo(w-6,cn+6);x.stroke();
  x.beginPath();x.moveTo(6,h-cn-6);x.lineTo(6,h-6);x.lineTo(cn+6,h-6);x.stroke();
  x.beginPath();x.moveTo(w-cn-6,h-6);x.lineTo(w-6,h-6);x.lineTo(w-6,h-cn-6);x.stroke();

  if(im.badge){{
    x.font='800 12px Inter,sans-serif';
    const btw=x.measureText(im.badge).width+28;
    const bx=hw-btw/2,by=30;
    x.fillStyle=HR(ac,.12);x.strokeStyle=HR(ac,.45);x.lineWidth=1.5;
    RR(x,bx,by,btw,28,14);x.fill();x.stroke();
    x.fillStyle=ac;x.textAlign='center';x.textBaseline='middle';
    x.fillText(im.badge,hw,by+14);
  }}

  const pr=105,pcx=hw,pcy=188;
  const pGlow=x.createRadialGradient(pcx,pcy,pr-10,pcx,pcy,pr+50);
  pGlow.addColorStop(0,HR(ac,.22));pGlow.addColorStop(.6,HR(ac,.06));pGlow.addColorStop(1,'transparent');
  x.fillStyle=pGlow;x.beginPath();x.arc(pcx,pcy,pr+50,0,Math.PI*2);x.fill();
  x.strokeStyle=HR(ac,.45);x.lineWidth=2.5;
  x.beginPath();x.arc(pcx,pcy,pr+4,0,Math.PI*2);x.stroke();
  x.strokeStyle=HR(ac,.12);x.lineWidth=1;
  x.beginPath();x.arc(pcx,pcy,pr+18,0,Math.PI*2);x.stroke();
  x.save();x.beginPath();x.arc(pcx,pcy,pr,0,Math.PI*2);x.clip();
  if(PHOTO_B64&&photoImg.complete&&photoImg.naturalWidth>0){{
    const s=Math.max(pr*2/photoImg.width,pr*2/photoImg.height);
    const pw=photoImg.width*s,ph=photoImg.height*s;
    x.drawImage(photoImg,pcx-pw/2,pcy-ph/2,pw,ph);
  }}else{{x.fillStyle=HR(ac,.15);x.beginPath();x.arc(pcx,pcy,pr,0,Math.PI*2);x.fill()}}
  x.restore();

  x.textAlign='center';x.textBaseline='top';
  const headline=im.headline;
  let fs=headline.length>20?50:headline.length>14?60:70;
  x.font=`900 ${{fs}}px Montserrat,sans-serif`;
  let tm=x.measureText(headline);
  while(tm.width>w-100&&fs>34){{fs-=3;x.font=`900 ${{fs}}px Montserrat,sans-serif`;tm=x.measureText(headline)}}
  const hly=330;
  x.save();x.shadowColor=HR(ac,.5);x.shadowBlur=35;x.fillStyle='#fff';x.fillText(headline,hw,hly);x.restore();
  x.fillStyle='#fff';x.fillText(headline,hw,hly);

  const barY=hly+fs+10;
  x.fillStyle=ac;RR(x,hw-35,barY,70,3.5,2);x.fill();

  let subFs=19;x.font=`500 ${{subFs}}px Inter,sans-serif`;
  let stm=x.measureText(im.sub);
  while(stm.width>w-140&&subFs>11){{subFs-=2;x.font=`500 ${{subFs}}px Inter,sans-serif`;stm=x.measureText(im.sub)}}
  x.fillStyle='rgba(255,255,255,.5)';x.textAlign='center';x.textBaseline='top';
  x.fillText(im.sub,hw,barY+14);

  if(im.tools&&im.tools.length){{
    x.font='600 11px Inter,sans-serif';
    const maxT=Math.min(im.tools.length,6);const pills=im.tools.slice(0,maxT);
    let totalW=0;const widths=pills.map(t=>{{const tw=x.measureText(t).width+24;totalW+=tw;return tw}});
    totalW+=(maxT-1)*8;let toolX=hw-totalW/2;const toolY=h-120;
    pills.forEach((t,i)=>{{
      x.fillStyle=HR(ac,.08);x.strokeStyle=HR(ac,.25);x.lineWidth=1;
      RR(x,toolX,toolY,widths[i],26,6);x.fill();x.stroke();
      x.fillStyle='rgba(255,255,255,.65)';x.textAlign='center';x.textBaseline='middle';
      x.fillText(t,toolX+widths[i]/2,toolY+13);toolX+=widths[i]+8;
    }});
  }}

  x.fillStyle=HR(ac,.035);
  x.beginPath();x.arc(w*.12,h*.7,120,0,Math.PI*2);x.fill();
  x.beginPath();x.arc(w*.88,h*.3,100,0,Math.PI*2);x.fill();

  x.font='700 10px Inter,sans-serif';x.fillStyle='rgba(255,255,255,.06)';
  x.textAlign='center';x.textBaseline='bottom';
  x.fillText(WATERMARK,hw,h-18);
  x.textAlign='left';x.textBaseline='alphabetic';
}}

function RR(x,a,b,w,h,r){{x.beginPath();x.moveTo(a+r,b);x.lineTo(a+w-r,b);x.quadraticCurveTo(a+w,b,a+w,b+r);x.lineTo(a+w,b+h-r);x.quadraticCurveTo(a+w,b+h,a+w-r,b+h);x.lineTo(a+r,b+h);x.quadraticCurveTo(a,b+h,a,b+h-r);x.lineTo(a,b+r);x.quadraticCurveTo(a,b,a+r,b);x.closePath()}}
function HR(h,a){{h=h.replace('#','');return`rgba(${{parseInt(h.substring(0,2),16)}},${{parseInt(h.substring(2,4),16)}},${{parseInt(h.substring(4,6),16)}},${{a}})`}}
function ST(m){{const t=document.getElementById('toast');t.textContent=m;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),2e3)}}
function cp(t,l){{navigator.clipboard.writeText(t).then(()=>ST(`Copied ${{l}}`))}}
function cpE(id,l){{cp(document.getElementById(id).textContent.trim(),l)}}
function dl(id,fn){{const c=document.getElementById(id),a=document.createElement('a');a.download=fn;a.href=c.toDataURL('image/png');a.click()}}
function downloadAllPNG(){{G.forEach(g=>{{setTimeout(()=>dl(`c${{g.id}}`,`gig-${{g.id}}-thumbnail.png`),g.id*300)}})}}

function dlPDF(id){{
  const g=G.find(x=>x.id===id);
  const t=`${{('=').repeat(64)}}
  FIVERR GIG #${{g.id}} — ${{g.img.headline}}
  PHASE ${{g.phase}} ${{g.phase===1?'— LAUNCH NOW':g.phase===2?'— AFTER 5 REVIEWS':'— AFTER LEVEL 2'}}
${{('=').repeat(64)}}

TITLE: ${{g.title}}
CHARS: ${{g.title.length}}/80
CATEGORY: ${{g.cat}}
TAGS: ${{g.tags.join(', ')}}
COMPETITION: ${{g.competition}}

${{('─').repeat(64)}}
  WHAT THIS GIG OFFERS
${{('─').repeat(64)}}
${{g.img.pdfWhat}}

${{('─').repeat(64)}}
  CROSS-SELL STRATEGY
${{('─').repeat(64)}}
${{g.xsell}}

${{('─').repeat(64)}}
  FULL DESCRIPTION (copy to Fiverr)
${{('─').repeat(64)}}
${{g.desc}}

${{('─').repeat(64)}}
  PRICING TIERS
${{('─').repeat(64)}}

  BASIC — ${{g.pricing.basic.name}} ($${{g.pricing.basic.price}})
  "${{g.pricing.basic.title}}"
  Delivery: ${{g.pricing.basic.del}} | Revisions: ${{g.pricing.basic.rev}}
${{g.pricing.basic.items.map(i=>'    \\u2713 '+i).join('\\n')}}

  STANDARD — ${{g.pricing.standard.name}} ($${{g.pricing.standard.price}}) \\u2605 MOST POPULAR
  "${{g.pricing.standard.title}}"
  Delivery: ${{g.pricing.standard.del}} | Revisions: ${{g.pricing.standard.rev}}
${{g.pricing.standard.items.map(i=>'    \\u2713 '+i).join('\\n')}}

  PREMIUM — ${{g.pricing.premium.name}} ($${{g.pricing.premium.price}})
  "${{g.pricing.premium.title}}"
  Delivery: ${{g.pricing.premium.del}} | Revisions: ${{g.pricing.premium.rev}}
${{g.pricing.premium.items.map(i=>'    \\u2713 '+i).join('\\n')}}

${{('═').repeat(64)}}`;
  const blob=new Blob([t],{{type:'text/plain'}});
  const a=document.createElement('a');a.download=`gig-${{g.id}}-phase${{g.phase}}-${{g.tags[0].replace(/\\s/g,'-')}}.txt`;a.href=URL.createObjectURL(blob);a.click();
}}

function cpA(id){{
  const g=G.find(x=>x.id===id);
  const t=`FIVERR GIG #${{g.id}} — PHASE ${{g.phase}} — ${{g.img.headline}}
${{('=').repeat(60)}}
TITLE: ${{g.title}}
CHARS: ${{g.title.length}}/80
CATEGORY: ${{g.cat}}
TAGS: ${{g.tags.join(', ')}}
COMPETITION: ${{g.competition}}
CROSS-SELL: ${{g.xsell}}

WHAT IT OFFERS:
${{g.img.pdfWhat}}

DESCRIPTION:
${{g.desc}}

PRICING:
BASIC - ${{g.pricing.basic.name}} ($${{g.pricing.basic.price}}) | ${{g.pricing.basic.del}} | ${{g.pricing.basic.rev}} rev
  ${{g.pricing.basic.items.join(' | ')}}
STANDARD - ${{g.pricing.standard.name}} ($${{g.pricing.standard.price}}) [POPULAR] | ${{g.pricing.standard.del}} | ${{g.pricing.standard.rev}} rev
  ${{g.pricing.standard.items.join(' | ')}}
PREMIUM - ${{g.pricing.premium.name}} ($${{g.pricing.premium.price}}) | ${{g.pricing.premium.del}} | ${{g.pricing.premium.rev}} rev
  ${{g.pricing.premium.items.join(' | ')}}
${{('=').repeat(60)}}`;
  cp(t,'all details');
}}

function copyAllGigs(){{
  let all='FIVERR DOMINATION STRATEGY\\n'+('=').repeat(60)+'\\n\\n';
  G.forEach(g=>{{
    all+=`GIG #${{g.id}} (Phase ${{g.phase}}) — ${{g.img.headline}}\\nTitle: ${{g.title}}\\nCategory: ${{g.cat}}\\nTags: ${{g.tags.join(', ')}}\\nCompetition: ${{g.competition}}\\nPricing: $${{g.pricing.basic.price}} / $${{g.pricing.standard.price}} / $${{g.pricing.premium.price}}\\nCross-sell: ${{g.xsell}}\\n\\n`;
  }});
  cp(all,'all gigs summary');
}}
</script>
</body>
</html>'''

output_path = os.path.join(os.path.dirname(config_path) or '.', 'fiverr-catalog.html')
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(html)

print(f'Generated {len(html)//1024}KB catalog: {output_path}')
print(f'Gigs: {len(gigs)} total ({len(p1)} Phase 1, {len(p2)} Phase 2, {len(p3)} Phase 3)')
print(f'Photo: {"embedded" if photo_b64 else "none (placeholder)"}')
print(f'Open in browser to review thumbnails and copy gig details.')
