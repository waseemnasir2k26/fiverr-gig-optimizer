# Fiverr Gig Audit

Audit an existing Fiverr gig with the offline `fiverr-gig` CLI and fix it.

1. If `fiverr-gig` is not on PATH, run `pip install -e .` in this repo.
2. Get the gig as JSON, YAML or Markdown (see `docs/input-formats.md`). If the user pasted the gig text, write it to `gig-audit-input.md` using the Markdown layout.
3. Run `fiverr-gig audit <file> --json` and read the result.
4. Rewrite the weakest parts the audit names. Rules: title starts "I will", max 80 characters with the main keyword in the first 50; exactly 5 tags of 20 characters or fewer; description max 1,200 characters with 3+ bullets and a call to action that keeps the buyer on Fiverr; three ascending packages; 3+ FAQs; at least one requirement.
5. Re-run the audit. Repeat until the score stops improving. Show the user before/after scores exactly as printed.
6. Run `fiverr-gig lint --text "<new description>"` on the final copy and fix any findings.

Never claim the score predicts ranking or sales. It checks form against Fiverr's limits and common best practice. Limits and their sources: `docs/fiverr-rules-2026.md`.
