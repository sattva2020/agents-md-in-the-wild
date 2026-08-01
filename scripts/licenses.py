"""Detect an SPDX licence id from licence text.

The search API does not always return licence metadata, and the corpus policy
depends on knowing the licence — so we identify it from the LICENSE file
itself. Matching is done on distinctive phrases rather than full text, which
survives the small edits projects make (copyright line, year, holder name).

Deliberately conservative: an unrecognised licence returns None and the entry
drops to metadata tier. Guessing wrong here means redistributing something we
should not, so ambiguity always resolves to "do not store".
"""

from __future__ import annotations

import re

_STEMS = ["LICENSE", "LICENCE", "COPYING", "COPYRIGHT",
          "LICENSE-MIT", "LICENSE-APACHE", "LICENSE-GPL", "LICENSE-AGPL", "LICENSE-BSD"]
_SUFFIXES = ["", ".md", ".txt", ".rst"]

# Case matters on raw.githubusercontent.com, and projects are inconsistent:
# Next.js ships `license.md`, most ship `LICENSE`. Probe both casings.
LICENSE_FILENAMES = [
    stem_case + suffix
    for stem in _STEMS
    for stem_case in (stem, stem.lower())
    for suffix in _SUFFIXES
]

# Order matters: the more specific fingerprint has to win. AGPL text contains
# most of the GPL text, so AGPL is tested first, and so on.
FINGERPRINTS: list[tuple[str, re.Pattern]] = [
    ("agpl-3.0", re.compile(r"GNU AFFERO GENERAL PUBLIC LICENSE.*Version 3", re.I | re.S)),
    ("lgpl-3.0", re.compile(r"GNU LESSER GENERAL PUBLIC LICENSE.*Version 3", re.I | re.S)),
    ("lgpl-2.1", re.compile(r"GNU LESSER GENERAL PUBLIC LICENSE.*Version 2\.1", re.I | re.S)),
    ("gpl-3.0", re.compile(r"GNU GENERAL PUBLIC LICENSE.*Version 3", re.I | re.S)),
    ("gpl-2.0", re.compile(r"GNU GENERAL PUBLIC LICENSE.*Version 2", re.I | re.S)),
    ("apache-2.0", re.compile(r"Apache License.*Version 2\.0", re.I | re.S)),
    ("mpl-2.0", re.compile(r"Mozilla Public License Version 2\.0", re.I)),
    ("epl-2.0", re.compile(r"Eclipse Public License - v ?2\.0", re.I)),
    ("cc0-1.0", re.compile(r"CC0 1\.0 Universal", re.I)),
    ("cc-by-sa-4.0", re.compile(r"Attribution-ShareAlike 4\.0 International", re.I)),
    ("cc-by-4.0", re.compile(r"Attribution 4\.0 International", re.I)),
    ("unlicense", re.compile(r"This is free and unencumbered software released into the public domain", re.I)),
    ("0bsd", re.compile(r"Permission to use, copy, modify, and/or distribute this software for any purpose with or without fee is hereby granted\.", re.I)),
    ("isc", re.compile(r"Permission to use, copy, modify,? and/or distribute this software", re.I)),
    ("bsd-3-clause", re.compile(r"Neither the name of.{0,120}nor the names of its contributors may be used to endorse", re.I | re.S)),
    ("bsd-2-clause", re.compile(r"Redistributions in binary form must reproduce the above copyright", re.I)),
    ("mit", re.compile(r"Permission is hereby granted, free of charge, to any person obtaining a copy", re.I)),
    ("wtfpl", re.compile(r"DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE", re.I)),
]


def detect_from_text(text: str) -> str | None:
    """Return a lowercase SPDX id, or None when nothing matches confidently."""
    if not text:
        return None
    head = text[:20_000]
    for spdx, pattern in FINGERPRINTS:
        if pattern.search(head):
            return spdx
    return None
