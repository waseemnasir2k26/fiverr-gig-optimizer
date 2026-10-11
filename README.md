# Fiverr Gig Optimizer: free Fiverr SEO audit, gig tool and Claude Code skill

[![tests](https://img.shields.io/badge/tests-51%20passing-brightgreen.svg)](tests/test_tools.py)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python 3.10 | 3.11 | 3.12](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](pyproject.toml)

An open-source **Fiverr gig optimizer** for sellers. Run `fiverr-gig audit` on your listing and get a 0-100 score with the exact fixes: title length and keyword placement, the 5 search tags, description, package ladder, FAQ, requirements and image sizes. It also lints your buyer messages for words that trip Fiverr's off-platform filter, does the 20% fee maths, and suggests tags for a niche. Everything runs offline in Python with no account and no API key. It also ships the original **Fiverr Claude Code skill** (`/fiverr-optimize`) that researches niches and writes the whole gig.

If you searched for "fiverr gig optimizer", "fiverr seo", "fiverr gig tool" or "fiverr claude", this is the toolkit built around those jobs. It checks the form of a listing against Fiverr's published limits. It cannot see Fiverr's ranking algorithm and does not promise orders.

## 60-second quickstart

```bash
git clone https://github.com/waseemnasir2k26/fiverr-gig-optimizer.git
cd fiverr-gig-optimizer
pip install -e .                                   # Python 3.10+, no dependencies

fiverr-gig audit examples/needs-work-gig.md        # score a gig and list fixes
fiverr-gig lint --text "Send me your email and I will pay you"   # check a message
fiverr-gig price --net 200 --hours 4               # what to quote to keep $200
fiverr-gig keywords "n8n lead automation"          # tag and title candidates
```

Audit your own gig: copy `examples/strong-gig.json` (or the Markdown example), replace the text with yours, run `fiverr-gig audit your-gig.json`. Add `--min-score 85` to make it a pass/fail gate in a script.

## What is in the toolkit

| Command                                 | What it does                                                                                                                                                                               | Offline                  |
| --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------ |
| `fiverr-gig audit FILE`                 | Scores a gig 0-100 across title, tags, description, packages, FAQ, requirements and images, and prints specific fixes. Reads JSON, YAML or Markdown.                                       | yes                      |
| `fiverr-gig lint`                       | Flags off-platform contact and payment words (email, pay, Discord, WhatsApp, URLs, handles, phone numbers) with safer wording. Calls out disguised spellings as worse than the plain word. | yes                      |
| `fiverr-gig price`                      | Net after Fiverr's 20% seller fee, the sticker price to quote for a net target, a Basic/Standard/Premium ladder, and net hourly rate.                                                      | yes                      |
| `fiverr-gig keywords SEED`              | Tag candidates (each 20 characters or fewer) and title drafts from a seed niche. Optional LLM extras with `--llm` if you set `FIVERR_GIG_LLM_*` variables. Off by default.                 | yes (LLM optional)       |
| `fiverr-gig rules`                      | Prints the limits the tools check. Sources in [docs/fiverr-rules-2026.md](docs/fiverr-rules-2026.md).                                                                                      | yes                      |
| `/fiverr-optimize`                      | Claude Code skill: interviews you, researches combo niches, writes a full multi-gig strategy and `gig-config.json`, then calls the audit.                                                  | needs Claude Code        |
| `/fiverr-audit`, `/fiverr-message-lint` | Claude Code commands that run the CLI and rewrite until the audit and lint are clean.                                                                                                      | needs Claude Code        |
| `build-catalog.py`, `build-pdfs.py`     | Original tools: HTML catalog with canvas thumbnails and editorial per-gig PDFs.                                                                                                            | PDFs need Chrome or Edge |

## Demo (real output from this repo)

```text
$ fiverr-gig audit examples/needs-work-gig.md
GIG: I will do a complete professional website design and development for your business with SEO and speed
SCORE: 43/100  grade F  [#########-----------]
  title         10/20
  tags          12/15
  description    6/15
  packages       6/20
  faq            2/10
  requirements   0/10
  images         7/10
FIXES:
  1. Title is 101 characters; the limit is 80. Cut 21.
  2. Tags over 20 characters are rejected in practice: wordpress website design and development.
  3. Description is thin (161 chars). Cover what you deliver, how it works, and who it is for (aim for 300+).
  4. Add a bulleted list of what the buyer gets (3+ bullets scan better than a paragraph).
  5. Remove off-platform contact or payment words: WhatsApp, email, pay.
  6. Prices must rise Basic < Standard < Premium.
  7. Give each package a delivery time that does not shrink as scope grows.
  8. List 2+ deliverables per package, growing from Basic to Premium.
  9. Packages have identical deliverables; differentiate them.
  10. Add 2 more FAQ(s).
  11. Answer each FAQ in a full sentence or two (40+ characters).
  12. Add buyer requirements so orders start with what you need (access, files, brand details).
  13. Image 800x600: Fiverr recommends 1280x769.
  14. Add a short gig video if you can; it is the one gallery slot most sellers leave empty.

```

```text
$ fiverr-gig lint examples/buyer-message.txt
5 issue(s), 4 high severity
  [high] 'email' (email) -> try: subscriber list / mailing list (if about marketing) or 'message me here'
  [medium] 'a call' (phone/call) -> try: message me here
  [high] 'Zoom' (video call tool) -> try: chat here (or use Fiverr's own meeting option if offered)
  [high] 'WhatsApp' (whatsapp) -> try: message me here
  [high] 'pay' (pay/payment) -> try: my fee / the order total

$ fiverr-gig price --net 200 --hours 4
Sticker price (gross): $250.00
Fiverr seller fee 20%:   -$50.00
You keep (net):        $200.00
Net per hour (4h):    $50.00
Buyer checkout (estimate): $263.75  (5.5% + small-order fee; check Fiverr's current fees page)

$ fiverr-gig keywords logo design
Seed: logo design  (offline heuristics; verify against Fiverr search suggestions)
Suggested 5 tags: logo design, logo design custom, logo design expert, logo design fast, logo design pro
All candidates:
  logo design            11 chars
  logo design custom     18 chars
  logo design expert     18 chars
  logo design fast       16 chars
  logo design pro        15 chars
  logo design service    19 chars
  custom logo design     18 chars
  expert logo design     18 chars
  fast logo design       16 chars
  pro logo design        15 chars
  service logo design    19 chars
  design custom          13 chars
  design expert          13 chars
  design freelancer      17 chars
  design professional    19 chars
```

The example gigs are fictional and exist to exercise the tool. Scores in this README are what the code prints; they are not claims about any real gig.

## How the score works

Seven categories, 100 points: title 20, tags 15, description 15, packages 20, FAQ 10, requirements 10, images 10. Images are skipped (not scored, not penalised) if you do not list them. Each limit is tagged in [`fiverr_gig/rules.py`](fiverr_gig/rules.py) as official, reported, observed or heuristic, and [docs/fiverr-rules-2026.md](docs/fiverr-rules-2026.md) cites the source for each. Thresholds such as "3+ FAQs" and "300+ character description" are our heuristics, not Fiverr rules, and the doc says so.

## FAQ

**Will a high score rank my gig?** No. The score says the listing is well-formed. Fiverr ranking depends on things the tool cannot see: conversion, reviews, response time, category competition and Fiverr's own weighting.

**What are Fiverr's limits for a gig?** 80 characters for the title (about 50 are safe on the gig card), 1,200 for the description, 5 search tags, 3 packages, and a gallery of up to 3 images, 1 video and 2 PDFs. Image size is 1280 x 769 recommended. See the sources table in the docs; the 20-character tag limit is observed rather than officially documented.

**How much does Fiverr take?** 20% of the order amount, so to keep $200 you quote $250. Buyers pay a service fee on top, which is why `price` also prints an estimated buyer total. That fee figure is an estimate because Fiverr's help pages disagree on the small-order part.

**Is the message lint Fiverr's real filter?** No. Fiverr does not publish its filter. The list comes from messages that were blocked in real use. A clean result is not a guarantee, and rewording never makes it acceptable to move a buyer off the platform.

**Does it use AI?** The CLI is deterministic and offline. The optional `--llm` flag sends only your seed niche to an OpenAI-compatible endpoint you configure with `FIVERR_GIG_LLM_BASE_URL`, `FIVERR_GIG_LLM_API_KEY` and `FIVERR_GIG_LLM_MODEL`. The Claude Code skill uses Claude, of course.

**Does it log in to Fiverr or post for me?** No. No scraping, no logged-in browser automation, no auto-messaging. You paste your own gig text in and copy the result back out yourself.

**Can I audit several gigs at once?** Yes. Point `audit` at a `gig-config.json` with a `gigs` list and every gig is scored.

## Honest comparison with other open-source Fiverr tools

Checked with the GitHub API on 2026-10-12 (descriptions, file trees, stars at that time). We did not run the other tools.

| Repo | What it is | Where it differs |
|---|---|---|
| [Ahad690/fiverr-gig-optimizer](https://github.com/Ahad690/fiverr-gig-optimizer) | Claude Code skill and plugin with a competition and pricing scoring approach, a contribution dataset and a PRD (MIT) | Similar name, skill-first. A good pick if you want its crowd-sourced dataset. This repo adds an installable offline CLI with a rule-based audit, message lint and fee calculator, and CI-tested code |
| [madezmedia/fiverr-gig-optimizer](https://github.com/madezmedia/fiverr-gig-optimizer) | Streamlit web app for gig optimization (MIT) | A hosted-app style tool; last push January 2025 at the time of checking. This repo needs no server, key or UI |
| Generic ChatGPT/Claude "Fiverr gig prompt" lists | Prompts that write a title and description | Fine for drafting. They do not check your result against character limits, tag rules or package structure, which is what the audit does |

If one of these fits you better, use it. They can be combined: write with a skill, then run `fiverr-gig audit` over the output.

## Using it with Claude Code

Open Claude Code in this folder and run `/fiverr-optimize`. It collects your services, researches combo niches, writes `gig-config.json`, runs `fiverr-gig audit` and fixes the findings, then builds the HTML catalog and PDFs. `/fiverr-audit` audits one existing gig; `/fiverr-message-lint` checks a message before you send it.

## Original catalog and PDF tools

```bash
cp config-example.json gig-config.json   # edit with your gigs
python build-catalog.py                  # fiverr-catalog.html with 1280x769 canvas thumbnails and copy buttons
python build-pdfs.py                     # one editorial PDF per gig into pdfs/ (needs Chrome or Edge)
```

`docs/guide.html` is a printable step-by-step guide (Ctrl+P, Save as PDF). The audit reads `gig-config.json` directly, so `fiverr-gig audit gig-config.json` works on whatever `/fiverr-optimize` produced.

## Project layout

```
fiverr_gig/        the pip-installable package (audit, lint, pricing, keywords, cli)
tests/             pytest suite
examples/          3 sample gigs and a sample buyer message (fictional)
docs/              Fiverr rules with sources, input formats, printable guide
.claude/commands/  /fiverr-optimize, /fiverr-audit, /fiverr-message-lint
build-catalog.py   HTML catalog generator
build-pdfs.py      PDF generator
```

## Development

```bash
pip install -e ".[dev]"
python -m pytest -q
```

The suite was run locally on Python 3.11. A GitHub Actions workflow for Python 3.10, 3.11 and 3.12 is in [`ci/github-actions-ci.yml`](ci/github-actions-ci.yml); copy it to `.github/workflows/ci.yml` to enable it (pushing workflow files needs a token with the `workflow` scope, which the release tooling did not have). If a Fiverr limit changes, edit `fiverr_gig/rules.py`, `docs/fiverr-rules-2026.md` and the affected tests, and open a PR.

## License

MIT. Use it, change it, sell gigs with it.

## Work with SkynetLabs

Built by [Waseem Nasir](https://www.skynetjoe.com/?utm_source=github&utm_medium=readme&utm_campaign=fiverr-gig-optimizer) at SkynetLabs — n8n + AI automation for small businesses.

- Hire on Fiverr: https://www.fiverr.com/agencies/skynetjoellc
- Hire on Upwork: https://www.upwork.com/freelancers/muhammadwaseemnasir
- Book a free call: https://calendly.com/skynetlabs/schedule-a-free-consultation
