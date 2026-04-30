# Fiverr Gig Optimizer

**AI-powered Claude Code skill that generates a complete Fiverr gig strategy** — optimized titles, descriptions, tags, pricing, professional thumbnails, and cross-sell funnels.

You tell it your services. It researches competition, finds blue-ocean combo-niches, and generates everything you need to dominate Fiverr.

## What You Get

- **Research-backed gig strategy** with combo-niche targeting (find keywords with 24 competitors instead of 10,000+)
- **Professional thumbnails** (1280x769px) with your photo, dark backgrounds, accent glows — the style that gets 25-40% higher CTR
- **Copy-paste ready** titles (under 80 chars), descriptions (under 1200 chars), and tags (5 per gig)
- **3-tier pricing** (Basic / Standard / Premium) optimized for Fiverr's algorithm
- **Phase-based rollout** — launch 3-4 gigs first, add premium upsells after reviews
- **Cross-sell funnel** — every gig mentions related gigs to maximize per-customer revenue
- **Editorial-design PDF per gig** — dark plum cover page, bone-cream content sheet, Fraunces serif + Inter body, white pricing cards w/ inverted STANDARD tier, magenta-accent FAQ blocks. Upload-ready for Fiverr "Gallery" PDFs.
- **Action plan** with week-by-week checklist

## Quick Start

### Prerequisites

- [Claude Code](https://claude.ai/code) installed
- Python 3.8+ installed
- A professional headshot photo (PNG/JPG, 500x500px minimum)

### Step 1: Clone

```bash
git clone https://github.com/waseemnasir2k26/fiverr-gig-optimizer.git
cd fiverr-gig-optimizer
```

### Step 2: Run the Skill

Open Claude Code in this directory and run:

```
/fiverr-optimize
```

Claude will ask you for:
1. Your name and brand
2. Your services (list everything you can deliver)
3. Your photo path
4. Your current Fiverr gigs (if any)
5. Your revenue goal

Then it:
1. Researches Fiverr competition for your services
2. Identifies combo-niche opportunities with low competition
3. Designs a phase-based gig strategy
4. Generates a `gig-config.json` with all gig data
5. Runs `build-catalog.py` to create your HTML catalog
6. Runs `build-pdfs.py` to render editorial-design PDFs (one per gig) into `pdfs/`

### Step 3: Review & Create Gigs

Open `fiverr-catalog.html` in your browser. For each gig:
1. Click **"Copy Title"** → paste into Fiverr
2. Click **"Copy Desc"** → paste into Fiverr (full multi-line text via `cpDesc`)
3. Click **"Copy Tags"** → paste into Fiverr
4. Click **"PNG"** → download thumbnail → upload to Fiverr
5. Click **"PDF"** → download editorial PDF from `pdfs/` → upload to Fiverr Gig Gallery
6. Set pricing tiers to match the catalog

## Manual Usage (Without Claude Code)

1. Copy `config-example.json` to `gig-config.json`
2. Edit with your gig details
3. Place your photo in the repo directory
4. Run:

```bash
python build-catalog.py    # Generates fiverr-catalog.html
python build-pdfs.py       # Generates editorial PDFs into pdfs/
```

5. Open `fiverr-catalog.html` in your browser. PDFs land in `pdfs/`.

## Config Options

```bash
python build-catalog.py                          # Uses gig-config.json (default)
python build-catalog.py my-config.json           # Uses custom config file
python build-catalog.py --no-photo               # Generate without photo

python build-pdfs.py                             # Build PDFs from gig-config.json into pdfs/
python build-pdfs.py --config my.json --out out  # Custom paths
python build-pdfs.py --chrome /path/to/chrome    # Override browser binary
python build-pdfs.py --keep-html                 # Retain intermediate HTML for debugging
```

`build-pdfs.py` requires Google Chrome or Microsoft Edge installed (auto-detected on Windows / macOS / Linux). PDFs are rendered via headless Chromium `--print-to-pdf`.

## Fiverr Algorithm Insights (Built Into the Strategy)

| Signal | Impact | What We Do |
|--------|--------|-----------|
| Thumbnail with face | 25-40% higher CTR | Your photo centered in every thumbnail |
| Dark bg + bright accent | Highest performing style | Custom color per gig |
| Response time < 1 hour | Critical for ranking | Reminded in action plan |
| 5 reviews threshold | Algorithm visibility unlock | Phase 1 focuses on getting reviews |
| Same-category gigs | Traffic sharing boost | Gigs grouped by category |
| Bad gigs penalty | Drags down good gigs | Only create gigs you can deliver |
| Combo keywords | 10-100x less competition | e.g., "vapi + n8n" = ~24 gigs |
| Gig video | +30% impressions | In action plan for week 3-4 |

## File Structure

```
fiverr-gig-optimizer/
├── .claude/
│   └── commands/
│       └── fiverr-optimize.md    # Claude Code slash command
├── docs/
│   └── guide.html                # Printable PDF guide (open in browser → Print → Save as PDF)
├── examples/
│   └── (generated catalogs go here)
├── build-catalog.py              # Generates fiverr-catalog.html (catalog + thumbnails)
├── build-pdfs.py                 # Generates editorial PDFs (one per gig) via headless Chrome
├── config-example.json           # Example config to customize
├── gig-config.json               # Your config (generated by /fiverr-optimize)
├── fiverr-catalog.html           # Generated catalog (output)
├── pdfs/                         # Generated per-gig PDFs (output)
└── README.md                     # This file
```

## PDF Guide

Open `docs/guide.html` in your browser and print it (Ctrl+P / Cmd+P) → "Save as PDF". This creates a professional step-by-step guide you can share with anyone.

## Examples

See the `examples/` folder for sample catalogs generated with this tool.

## How It Works

1. **`/fiverr-optimize`** (Claude Code skill) interviews you about your services, researches Fiverr competition, and generates optimized gig data as `gig-config.json`

2. **`build-catalog.py`** reads the config and generates a single HTML file with:
   - HTML Canvas thumbnails rendered client-side (1280x769px)
   - Embedded base64 photo (no external dependencies)
   - Copy-paste buttons for every field (full-text desc copy, no truncation)
   - PDF download link per gig (points at `pdfs/`)
   - Print-friendly layout

3. **`build-pdfs.py`** reads the same config and renders one editorial PDF per gig via headless Chrome — A4, dark plum cover page, bone content sheet, Fraunces serif headers, white pricing cards w/ inverted STANDARD tier, magenta-accent FAQs, brand footer.

4. **You** open the HTML, review everything, download thumbnails + PDFs, and create gigs on Fiverr by copying the optimized content + uploading the PDF to the gig gallery.

## Credits

Built by [Waseem Nasir](https://www.skynetjoe.com) (Skynet Labs) using [Claude Code](https://claude.ai/code).

## License

MIT — Use it, modify it, make money with it.

---

<!-- SEO-HIRE-ME-BLOCK -->

## Hire Me

> **Need a Claude Code skill or AI agent for your business?**

I'm **Waseem Nasir** — founder of [Skynet Labs / SkynetJoe](https://www.skynetjoe.com), an AI Automation Agency. Custom Claude Code skills, AI agents, GPT-4/Claude/Gemini integrations.

**50+ live projects across:** Healthcare · Legal · Real Estate · E-Commerce · Logistics · HVAC · SaaS · Consulting

### Hire me
- 📅 **[Book a free strategy call](https://calendly.com/skynetlabs/schedule-a-free-consultation)**
- 💼 **[Hire on Fiverr](https://fiverr.com/agencies/skynetjoellc)**
- 🌐 **[skynetjoe.com](https://www.skynetjoe.com)**
- 📧 **info@skynetjoe.com**
- 💬 **[WhatsApp](https://wa.me/923001001957)**

### Related projects on my GitHub
- [ai-motivational-posts](https://github.com/waseemnasir2k26/ai-motivational-posts)
- [ai-video-editor](https://github.com/waseemnasir2k26/ai-video-editor)
- [aeo-content-engine](https://github.com/waseemnasir2k26/aeo-content-engine)
- [→ See all 50+ projects](https://github.com/waseemnasir2k26)

### Tags
`AI automation` · `n8n` · `GoHighLevel` · `Claude Code` · `Next.js` · `React` · `Python` · `freelance` · `hire me` · `agency`
