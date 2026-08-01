# Contributing

Three kinds of contribution are useful here, in descending order of value.

## 1. A signal that misfires

The only thing this repository sells is that its numbers survive being checked
by hand. So a counter-example is worth more than a feature.

If a pattern signal in [`scripts/analyze.py`](scripts/analyze.py) counts
something it should not — or misses something it should catch — open an issue
with:

- the file it got wrong (path in `corpus/`)
- the line that triggered it, or the line it missed
- which way it is wrong (false positive / false negative)

Precedent: the first directory-tree detector matched any bullet containing a
slash and reported 69%. A ten-file hand sample showed 60% of those were wrong.
The corrected detector reports 17%. That issue was the most valuable
contribution the project has had.

## 2. A missing repository

Either open an issue with the URL, or do it yourself:

```bash
python scripts/collect.py --targets owner/repo
python scripts/analyze.py
```

Then commit `corpus/owner__repo/`, the regenerated `data/`, and `PATTERNS.md`.

Inclusion bar: the repository should be something a stranger would recognise or
learn from — a widely used project, or an unusually well-written instruction
file. "Has an AGENTS.md" is not by itself interesting; there are millions.

## 3. Removal

If you maintain a repository in this corpus and want it out, open an issue.
It is removed the same day, no discussion and no need to explain. This applies
regardless of licence.

---

## Ground rules for code

- **Standard library only.** The weekly workflow runs with no install step, and
  it stays that way. A dependency is a way for this to break on a Monday
  morning when nobody is looking.
- **Never widen the licence allowlist without checking the terms.** Storing
  something we may not store is the one failure this project cannot recover
  from. Ambiguity resolves to metadata tier.
- **Generated files are generated.** `data/index.json`, `data/index.csv` and
  `PATTERNS.md` are rebuilt by `scripts/analyze.py`. Do not hand-edit them; the
  next refresh will silently overwrite your change.
- **The collector must stay idempotent.** Re-running without upstream changes
  must produce an empty diff. If it does not, that is a bug worth reporting.

## Running the checks

```bash
python scripts/collect.py --targets vercel/next.js   # should be a no-op the second time
python scripts/analyze.py
git diff --stat
```
