# Changelog

All notable changes to this project are documented in this file.

## [2.0.0] - 2026-10-12

Adds a real, tested, offline CLI. Existing tools (`build-catalog.py`, `build-pdfs.py`, `/fiverr-optimize`) are unchanged in behaviour.

### Added
- `fiverr-gig` pip-installable package (Python 3.10+, no runtime dependencies) with `audit`, `lint`, `price`, `keywords` and `rules` commands.
- `audit`: 0-100 gig score across title, tags, description, packages, FAQ, requirements and images, with specific fixes; reads JSON, YAML (optional PyYAML) and Markdown, and the existing `gig-config.json` format.
- `lint`: off-platform contact and payment word detection with safer wording; flags disguised spellings.
- `price`: net after Fiverr's 20% seller fee, sticker price for a net target, ladder suggestion, net hourly rate, estimated buyer total.
- `keywords`: offline tag (20 characters or fewer) and title candidates; optional LLM step behind `--llm` and `FIVERR_GIG_LLM_*` variables, off by default.
- 51 pytest tests and a GitHub Actions workflow template for Python 3.10, 3.11, 3.12 in `ci/github-actions-ci.yml` (copy it to `.github/workflows/` to enable).
- `examples/` with three fictional sample gigs and a sample message.
- `docs/fiverr-rules-2026.md` (limits with sources and confidence labels) and `docs/input-formats.md`.
- Claude Code commands `/fiverr-audit` and `/fiverr-message-lint`; `/fiverr-optimize` now audits its own output (Step 3b).

### Changed
- README rewritten. Removed unsourced percentage claims (CTR and impressions lifts, competition multiples) from the README and the skill; they were never measured by this project.
- Replaced the old "Hire Me" block with a short SkynetLabs footer.

## [2026.09] - 2026-09-16

- Maintenance review of fiverr-gig-optimizer — a Claude Code skill plus Python tooling that turns a list of services into a full Fiverr gig strategy: titles, descriptions, tags, 3-tier pricing, thumbnails and cross-sell funnels.
- Status: the skill entry point is `.claude/commands/fiverr-optimize.md`; `build-catalog.py` builds the gig catalog and `build-pdfs.py` renders the editorial per-gig PDFs (dark plum cover, bone-cream sheet, Fraunces/Inter). Configuration is driven from `config-example.json`, and `docs/` holds the guide as HTML plus a rendered PDF. MIT licensed.
- Reviewed September 2026: documentation refreshed, changelog started, and the repo versioned as v2026.09. No script or skill logic was changed.
- Known gaps: no CHANGELOG before this release; no package.json or other manifest, so no version bump applied; no tests, CI workflow or pinned Python dependency list (no requirements.txt) despite the README requiring Python 3.8+.
