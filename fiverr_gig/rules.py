"""Fiverr platform limits used by the tools.

Every value carries a source note. "official" = stated on a help.fiverr.com
page when this release was written (October 2026). "observed" = seen live by the
maintainers or reported by sellers but not found on an official page. "heuristic"
= a SkynetLabs rule of thumb, not a platform rule. See docs/fiverr-rules-2026.md.
Fiverr changes its rules; re-check before relying on any number.
"""

TITLE_MAX = 80  # official: Gig Title field accepts up to 80 characters
TITLE_CARD_SAFE = 50  # official advice: keep titles under ~50 so the gig card does not cut them off
TITLE_PREFIX = "i will"  # observed: Fiverr gig titles are written as "I will ..."

TAGS_MAX = 5  # official/community: a gig takes up to 5 search tags
TAG_MAX_LEN = 20  # observed: tags over 20 characters are rejected (not found on an official page)

DESC_MAX = 1200  # official: description field takes up to 1,200 characters
DESC_MIN_GOOD = 300  # heuristic: shorter descriptions rarely cover scope, process and CTA
DESC_BULLET_MIN = 3  # heuristic

PACKAGE_TIERS = ("basic", "standard", "premium")  # official: Basic / Standard / Premium
FAQ_MIN_GOOD = 3  # heuristic (no official minimum found)
REQUIREMENTS_MIN_GOOD = 1  # heuristic: ask the buyer for what you need up front

IMG_RECOMMENDED = (1280, 769)  # official: recommended gig image size
IMG_MIN = (712, 430)  # official minimum
IMG_MAX = (4000, 2416)  # official maximum
GALLERY_MAX_IMAGES = 3  # official: up to 3 images, 1 video, 2 PDFs
GALLERY_MAX_VIDEOS = 1
GALLERY_MAX_PDFS = 2

SELLER_FEE = 0.20  # official comparison page + seller coupon help: flat 20% of the order amount
BUYER_FEE = 0.055  # official payment help: 5.5% buyer service fee
BUYER_SMALL_ORDER_FEE = 3.50  # reported on the payment help page for orders under $200; sources differ
BUYER_SMALL_ORDER_LIMIT = 200.0

# Heuristic ladder multipliers relative to the Basic price (Standard ~2.5x, Premium ~5x).
LADDER_MULTIPLIERS = {"basic": 1.0, "standard": 2.5, "premium": 5.0}
