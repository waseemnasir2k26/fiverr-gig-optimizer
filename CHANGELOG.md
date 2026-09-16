# Changelog

All notable changes to this project are documented in this file.

## [2026.09] - 2026-09-16

- Maintenance review of fiverr-gig-optimizer — a Claude Code skill plus Python tooling that turns a list of services into a full Fiverr gig strategy: titles, descriptions, tags, 3-tier pricing, thumbnails and cross-sell funnels.
- Status: the skill entry point is `.claude/commands/fiverr-optimize.md`; `build-catalog.py` builds the gig catalog and `build-pdfs.py` renders the editorial per-gig PDFs (dark plum cover, bone-cream sheet, Fraunces/Inter). Configuration is driven from `config-example.json`, and `docs/` holds the guide as HTML plus a rendered PDF. MIT licensed.
- Reviewed September 2026: documentation refreshed, changelog started, and the repo versioned as v2026.09. No script or skill logic was changed.
- Known gaps: no CHANGELOG before this release; no package.json or other manifest, so no version bump applied; no tests, CI workflow or pinned Python dependency list (no requirements.txt) despite the README requiring Python 3.8+.
