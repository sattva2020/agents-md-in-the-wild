#!/usr/bin/env python3
"""Turn the corpus into an index and a patterns report.

The interesting question is not "who has an AGENTS.md" — it is "what do the
ones written by serious projects actually contain". So every stored file is
scanned for a fixed set of structural signals, and the report reports rates,
not vibes.

Outputs:
  data/index.json   every entry with per-file signals
  data/index.csv    the same, flattened, for spreadsheet spelunking
  PATTERNS.md       generated prose + tables, regenerated on every run
"""

from __future__ import annotations

import csv
import json
import pathlib
import re
import statistics
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parent.parent
CORPUS = ROOT / "corpus"
DATA = ROOT / "data"

CODE_FENCE = re.compile(r"^```", re.M)
HEADING = re.compile(r"^(#{1,6})\s+(.*)$", re.M)

# A directory map is a *block*, not a line. Matching single lines that merely
# contain a slash produced a 60% false-positive rate on a manual sample — any
# bullet mentioning `src/components/ui/` counted as a tree. So we require a run
# of consecutive tree-shaped lines instead.
BOX_CHARS = re.compile(r"[│├└┬┼]|\|--|`--|\+--")
# An indented path line: "  src/foo/  # comment" or "  crates/goose".
PATH_LINE = re.compile(r"^\s{1,12}[\w.@][\w.@ -]*/[\w.@/-]*\s*(?:[#—-]\s.*)?$")
TABLE_ROW = re.compile(r"^\s*\|")


def has_directory_map(text: str) -> bool:
    """True when the document contains a run of >=3 tree-shaped lines.

    Markdown tables are explicitly excluded: a table listing directories is a
    table, and counting it as a tree inflated this signal by ~20 points.
    """
    run = 0
    for line in text.splitlines():
        if not line.strip():
            continue
        if TABLE_ROW.match(line):
            run = 0
            continue
        if BOX_CHARS.search(line) or PATH_LINE.match(line):
            run += 1
            if run >= 3:
                return True
        else:
            run = 0
    return False


def _rx(pattern: str, flags=re.I | re.M):
    compiled = re.compile(pattern, flags)
    return lambda text: bool(compiled.search(text))


# Structural signals: (id, human label, predicate over the document text).
# Every predicate is deliberately narrow — this repository's only asset is that
# its numbers survive someone checking them by hand.
SIGNALS: list[tuple[str, str, object]] = [
    ("build_commands", "Build / run commands",
     _rx(r"^\s*#+.*\b(build|install|setup|getting started|development)\b")),
    ("test_commands", "How to run tests",
     _rx(r"\b(npm|pnpm|yarn|bun) (run )?test\b|\bpytest\b|\bgo test\b|\bcargo test\b"
         r"|\bmake test\b|\brspec\b|\bvitest\b|\bjest\b|\btox\b|\bphpunit\b")),
    ("code_style", "Code style rules",
     _rx(r"^\s*#+.*\b(style|conventions?|formatting|lint)\b")),
    ("architecture", "Architecture / layout overview",
     _rx(r"^\s*#+.*\b(architecture|structure|layout|overview|codebase|repository map)\b")),
    # "avoid" dropped: too weak to count as an explicit prohibition.
    ("prohibitions", "Explicit prohibitions (do not / never / must not)",
     _rx(r"\b(do not|don't|never|must not|should not|shouldn't)\b")),
    ("emphatic", "Emphatic markers (IMPORTANT / CRITICAL / ALWAYS)",
     _rx(r"\b(IMPORTANT|CRITICAL|ALWAYS|NEVER|MUST NOT)\b", re.M)),
    ("pr_conventions", "Commit / PR conventions",
     _rx(r"^\s*#+.*\b(commit|pull request|\bpr\b|branch|git)\b")),
    # "token" alone matched LLM-token talk, which is not secrets guidance.
    ("security", "Security or secrets guidance",
     _rx(r"\b(secret|credential|api[ -]key|\.env\b|access token|do not commit|never commit)\b")),
    ("dir_map", "Directory tree block", has_directory_map),
    ("file_refs", "Points at other files (@refs or links)",
     _rx(r"(^|\s)@[\w./-]+\.(md|ts|py|go|rs|json)|\]\([^)]+\.(md|ts|py|go|rs)\)")),
    ("agent_addressed", "Addresses the agent directly ('you')",
     _rx(r"\byou (should|must|are|will|can)\b")),
    # Only counts contrastive examples, not the phrase "for example".
    ("examples", "Contrastive examples (good vs bad)",
     _rx(r"(✅|❌|\bgood:|\bbad:|\bdo:|\bdon't:|\binstead of\b|\bprefer\b.{0,40}\bover\b)")),
]


def scan(text: str) -> dict:
    """Extract structural signals from one document."""
    headings = HEADING.findall(text)
    return {
        "bytes": len(text.encode("utf-8")),
        "lines": text.count("\n") + 1,
        "words": len(text.split()),
        "headings": len(headings),
        "max_heading_depth": max((len(h[0]) for h in headings), default=0),
        "code_blocks": CODE_FENCE.findall(text).__len__() // 2,
        "signals": {sid: bool(predicate(text)) for sid, _, predicate in SIGNALS},
    }


def load_corpus() -> list[dict]:
    entries: list[dict] = []
    if not CORPUS.exists():
        return entries

    for meta_path in sorted(CORPUS.glob("*/meta.json")):
        try:
            record = json.loads(meta_path.read_text())
        except json.JSONDecodeError:
            continue

        for filename, info in (record.get("files") or {}).items():
            stored = info.get("stored")
            if stored:
                blob = meta_path.parent / stored
                if not blob.exists():
                    continue
                info["analysis"] = scan(blob.read_text(encoding="utf-8", errors="replace"))
            elif info.get("headings"):
                # Metadata tier: we still know the shape, just not the prose.
                joined = "\n".join(info["headings"])
                partial = scan(joined)
                partial["partial"] = True
                info["analysis"] = partial
        entries.append(record)
    return entries


def write_index(entries: list[dict]) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_note": "Regenerated by scripts/analyze.py — do not edit by hand.",
        "count_repositories": len(entries),
        "count_files": sum(len(e.get("files") or {}) for e in entries),
        "entries": sorted(entries, key=lambda e: -e.get("stars", 0)),
    }
    (DATA / "index.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    with (DATA / "index.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ["repository", "stars", "language", "license", "tier", "file", "bytes", "lines",
             "headings", "code_blocks"] + [sid for sid, _, _ in SIGNALS]
        )
        for entry in sorted(entries, key=lambda e: -e.get("stars", 0)):
            for filename, info in (entry.get("files") or {}).items():
                analysis = info.get("analysis") or {}
                signals = analysis.get("signals", {})
                writer.writerow(
                    [entry.get("full_name"), entry.get("stars"), entry.get("language"),
                     entry.get("license"), entry.get("tier"), filename,
                     analysis.get("bytes", ""), analysis.get("lines", ""),
                     analysis.get("headings", ""), analysis.get("code_blocks", "")]
                    + [int(bool(signals.get(sid))) for sid, _, _ in SIGNALS]
                )


def pct(part: int, whole: int) -> str:
    return f"{round(100 * part / whole)}%" if whole else "—"


def write_patterns(entries: list[dict]) -> None:
    full = [
        (entry, filename, info)
        for entry in entries
        for filename, info in (entry.get("files") or {}).items()
        if info.get("analysis") and not info["analysis"].get("partial")
    ]
    total = len(full)

    lines: list[str] = [
        "# What is actually in these files",
        "",
        "Generated by `scripts/analyze.py`. Every number below is computed from the "
        "corpus in this repository — nothing here is hand-written or estimated.",
        "",
        f"Analysed **{total} fully stored files** across **{len(entries)} repositories**. "
        "Files held at metadata tier (unlicensed upstream) are excluded from the "
        "percentages, since only their headings are available.",
        "",
    ]

    if not total:
        lines += ["_Corpus is empty — run `python scripts/collect.py` first._", ""]
        (ROOT / "PATTERNS.md").write_text("\n".join(lines), encoding="utf-8")
        return

    sizes = [info["analysis"]["lines"] for _, _, info in full]
    words = [info["analysis"]["words"] for _, _, info in full]
    lines += [
        "## Size",
        "",
        f"| Metric | Lines | Words |",
        f"|---|---:|---:|",
        f"| Median | {int(statistics.median(sizes))} | {int(statistics.median(words))} |",
        f"| Mean | {int(statistics.mean(sizes))} | {int(statistics.mean(words))} |",
        f"| Shortest | {min(sizes)} | {min(words)} |",
        f"| Longest | {max(sizes)} | {max(words)} |",
        "",
        "## How often each element appears",
        "",
        "| Element | Files | Share |",
        "|---|---:|---:|",
    ]

    counts = Counter()
    for _, _, info in full:
        for sid, present in info["analysis"]["signals"].items():
            if present:
                counts[sid] += 1

    for sid, label, _ in sorted(SIGNALS, key=lambda s: -counts[s[0]]):
        lines.append(f"| {label} | {counts[sid]} | {pct(counts[sid], total)} |")

    by_name = Counter(filename for _, filename, _ in full)
    lines += [
        "",
        "## Which filenames are in use",
        "",
        "| Filename | Repositories |",
        "|---|---:|",
    ]
    for filename, count in by_name.most_common():
        lines.append(f"| `{filename}` | {count} |")

    by_lang = Counter(e.get("language") or "—" for e in entries)
    lines += [
        "",
        "## Languages represented",
        "",
        "| Language | Repositories |",
        "|---|---:|",
    ]
    for language, count in by_lang.most_common(15):
        lines.append(f"| {language} | {count} |")

    tiers = Counter(e.get("tier") for e in entries)
    lines += [
        "",
        "## Storage tiers",
        "",
        f"- **full** — {tiers.get('full', 0)} repositories, file stored verbatim with provenance",
        f"- **metadata** — {tiers.get('metadata', 0)} repositories, structure only "
        "(upstream ships no redistributable licence)",
        "",
        "See [`scripts/policy.py`](scripts/policy.py) for the exact rule.",
        "",
    ]

    (ROOT / "PATTERNS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    entries = load_corpus()
    write_index(entries)
    write_patterns(entries)
    files = sum(len(e.get("files") or {}) for e in entries)
    print(f"indexed {len(entries)} repositories / {files} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
