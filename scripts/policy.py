"""What we are allowed to store, and what we only describe.

This corpus redistributes files written by other people. That is fine under
permissive and copyleft licences as long as provenance travels with the file —
and it is *not* fine for a repository that ships no licence at all, where the
default is all rights reserved.

So the corpus has two tiers:

  full      — the file is stored verbatim, with source, commit SHA and licence
  metadata  — only structure is stored (headings, counts, links). No body text.

The metadata tier is not a limitation to apologise for: structural analysis of
an unlicensed file is fair, and it keeps the dataset usable for research
without laundering anyone's copyright.
"""

from __future__ import annotations

# SPDX ids (lowercased) whose terms permit redistribution with attribution.
REDISTRIBUTABLE = {
    "mit", "apache-2.0", "bsd-2-clause", "bsd-3-clause", "bsd-4-clause",
    "isc", "mpl-2.0", "unlicense", "cc0-1.0", "0bsd", "zlib", "epl-2.0",
    "gpl-2.0", "gpl-3.0", "lgpl-2.1", "lgpl-3.0", "agpl-3.0",
    "cc-by-4.0", "cc-by-sa-4.0", "artistic-2.0", "postgresql", "wtfpl",
}

TIER_FULL = "full"
TIER_METADATA = "metadata"


def license_id(repo: dict) -> str | None:
    """Extract a lowercase SPDX id from a repository payload."""
    lic = repo.get("license") or {}
    spdx = lic.get("spdx_id") or ""
    if not spdx or spdx in ("NOASSERTION", "NONE"):
        return None
    return spdx.lower()


def tier_for(repo: dict) -> tuple[str, str]:
    """Return (tier, reason) for a repository payload."""
    spdx = license_id(repo)
    if spdx is None:
        return TIER_METADATA, "no declared licence — all rights reserved by default"
    if spdx in REDISTRIBUTABLE:
        return TIER_FULL, f"redistributable under {spdx}"
    return TIER_METADATA, f"licence {spdx} not on the redistribution allowlist"
