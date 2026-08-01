#!/usr/bin/env python3
"""Discover repositories that ship agent instruction files, and pull them in.

Two discovery strategies, because neither is sufficient alone:

  code-search  Direct hits via the code search API. Precise, but needs a token
               and is capped at 1000 results per query, so it is sliced by size.
  repo-sweep   Walk popular repositories by language / star band and probe for
               the files. Slower, but finds files that code search misses and
               works when code search is unavailable.

Both feed the same writer, which is idempotent: re-running only rewrites files
whose upstream blob SHA changed. That is what makes the weekly diff meaningful
instead of a wall of noise.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import time

import gh
import licenses
import policy

ROOT = pathlib.Path(__file__).resolve().parent.parent
CORPUS = ROOT / "corpus"

# Filenames that steer a coding agent. Order matters: it is the display order.
TARGET_FILES = [
    "AGENTS.md",
    "CLAUDE.md",
    ".cursorrules",
    "GEMINI.md",
    ".github/copilot-instructions.md",
]

LANGUAGES = [
    "typescript", "python", "javascript", "go", "rust", "java",
    "ruby", "php", "c%2B%2B", "c%23", "swift", "kotlin", "elixir", "zig",
]


def slug(owner: str, repo: str) -> str:
    return f"{owner}__{repo}".replace("/", "_")


def entry_dir(owner: str, repo: str) -> pathlib.Path:
    return CORPUS / slug(owner, repo)


def load_meta(owner: str, repo: str) -> dict:
    path = entry_dir(owner, repo) / "meta.json"
    if path.exists():
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError:
            return {}
    return {}


def discover_code_search(limit: int) -> list[tuple[str, str]]:
    """Find repos via code search, sliced by file size to dodge the 1000 cap."""
    found: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    size_bands = ["<2000", "2000..6000", "6000..20000", ">20000"]

    for filename in ("AGENTS.md", "CLAUDE.md"):
        for band in size_bands:
            if len(found) >= limit:
                return found
            query = f"path:/{filename} size:{band}"
            gh.log(f"  code search: {query}")
            try:
                for item in gh.search_code(query, per_page=100, pages=3):
                    repo = item.get("repository") or {}
                    key = (repo.get("owner", {}).get("login"), repo.get("name"))
                    if not all(key) or key in seen:
                        continue
                    seen.add(key)
                    found.append(key)
                    if len(found) >= limit:
                        return found
            except Exception as err:  # code search is the flaky one; never fatal
                gh.log(f"  code search unavailable ({err}) — falling back to sweep")
                return found
    return found


def discover_repo_sweep(limit: int, min_stars: int) -> list[tuple[str, str]]:
    """Walk popular repos per language and probe them for agent files."""
    found: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for language in LANGUAGES:
        if len(found) >= limit:
            break
        query = f"language:{language} stars:>{min_stars} pushed:>2026-01-01"
        gh.log(f"  repo sweep: {query}")
        try:
            for repo in gh.search_repositories(query, per_page=100, pages=2):
                owner = (repo.get("owner") or {}).get("login")
                name = repo.get("name")
                if not owner or not name or (owner, name) in seen:
                    continue
                seen.add((owner, name))
                found.append((owner, name))
                if len(found) >= limit:
                    break
        except Exception as err:
            gh.log(f"  sweep failed for {language}: {err}")
            continue
    return found


def resolve_license(repo: dict) -> dict:
    """Ensure the repo payload carries an SPDX id, detecting it if necessary.

    Search results routinely omit licence metadata, and the storage tier hangs
    off it — so when it is missing we read the LICENSE file and identify it by
    text. Anything unrecognised stays unlicensed, which is the safe default.
    """
    if policy.license_id(repo):
        return repo

    owner = (repo.get("owner") or {}).get("login")
    name = repo.get("name")
    branch = repo.get("default_branch") or "main"

    # Fast path: the API names the licence directly. One request instead of
    # probing dozens of filenames over raw.
    try:
        payload = gh.request(f"/repos/{owner}/{name}/license")
        spdx = ((payload.get("license") or {}).get("spdx_id") or "").lower()
        if spdx and spdx not in ("noassertion", "none"):
            repo["license"] = {"spdx_id": spdx.upper(), "_detected_from": "api"}
            return repo
    except Exception:
        pass

    for filename in licenses.LICENSE_FILENAMES:
        text = gh.raw_file(owner, name, filename, branch)
        if not text:
            continue
        spdx = licenses.detect_from_text(text)
        if spdx:
            repo["license"] = {"spdx_id": spdx.upper(), "_detected_from": filename}
            return repo
    return repo


# raw.githubusercontent.com does not resolve "HEAD" — a real branch name is
# required, so likely defaults are probed in order. Next.js defaults to
# "canary", which is exactly the case a main/master-only guess gets wrong.
CANDIDATE_BRANCHES = ("main", "master", "canary", "develop", "dev", "trunk", "next")
PROBE_FILES = ("README.md", "readme.md", "README.rst", "package.json", "AGENTS.md")


def detect_branch(owner: str, name: str, known: str | None = None) -> str | None:
    """Find a branch that actually serves files over raw."""
    order = ([known] if known else []) + [b for b in CANDIDATE_BRANCHES if b != known]
    for branch in order:
        for probe in PROBE_FILES:
            if gh.raw_file(owner, name, probe, branch) is not None:
                return branch
    return None


def repo_stub(owner: str, name: str, previous: dict | None = None) -> dict | None:
    """Build a minimal repo payload without the REST API.

    Used when the API is unreachable or the token is repository-scoped. Star
    counts and topics are unavailable this way, but the corpus still gets the
    files, the licence and a working permalink — which is most of the value.
    """
    branch = detect_branch(owner, name, (previous or {}).get("default_branch"))
    if branch is None:
        return None

    return {
        "owner": {"login": owner},
        "name": name,
        "full_name": f"{owner}/{name}",
        "html_url": f"https://github.com/{owner}/{name}",
        "default_branch": branch,
        "stargazers_count": 0,
        "topics": [],
        "_metadata_source": "raw",
    }


def collect_repo(owner: str, name: str, prefetched: dict | None = None) -> dict | None:
    """Fetch every target file present in one repository. Returns its record."""
    if prefetched is not None:
        repo = prefetched
    else:
        try:
            repo = gh.request(f"/repos/{owner}/{name}")
        except gh.NotFound:
            return None
        except Exception:
            repo = repo_stub(owner, name, load_meta(owner, name))
            if repo is None:
                return None

    # Seed a stub payload with what a previous, better-informed run already
    # knew. Without this, a run with no API access silently downgrades entries
    # from `full` to `metadata` and orphans their stored files.
    if repo.get("_metadata_source") == "raw":
        previous = load_meta(owner, name)
        if previous:
            repo.setdefault("default_branch", previous.get("default_branch"))
            if previous.get("default_branch"):
                repo["default_branch"] = previous["default_branch"]
            if previous.get("license") and not policy.license_id(repo):
                repo["license"] = {"spdx_id": previous["license"].upper()}

    repo = resolve_license(repo)
    files: dict[str, dict] = {}
    for filename in TARGET_FILES:
        got = gh.get_file(owner, name, filename, ref=repo.get("default_branch"))
        if got is None:
            continue
        text, sha = got
        if not text.strip():
            continue
        files[filename] = {"text": text, "sha": sha}

    if not files:
        return None

    tier, reason = policy.tier_for(repo)

    # A stub payload (built without the REST API) knows the files but not the
    # stars, language or description. Never let it overwrite richer metadata
    # that a previous authenticated run already recorded.
    previous = load_meta(owner, name) if repo.get("_metadata_source") == "raw" else {}

    def keep(field: str, value):
        return previous.get(field) if previous.get(field) not in (None, 0, [], "") else value

    record = {
        "owner": owner,
        "repo": name,
        "full_name": repo.get("full_name"),
        "url": repo.get("html_url"),
        "description": keep("description", repo.get("description")),
        "stars": keep("stars", repo.get("stargazers_count", 0)),
        "language": keep("language", repo.get("language")),
        "topics": keep("topics", repo.get("topics", [])[:12]),
        "default_branch": repo.get("default_branch"),
        "license": policy.license_id(repo),
        "tier": tier,
        "tier_reason": reason,
        "pushed_at": keep("pushed_at", repo.get("pushed_at")),
        "files": {},
    }

    target = entry_dir(owner, name)
    target.mkdir(parents=True, exist_ok=True)

    for filename, blob in files.items():
        stored_name = filename.replace("/", "_")
        info = {
            "source_path": filename,
            "sha": blob["sha"],
            "bytes": len(blob["text"].encode("utf-8")),
            "lines": blob["text"].count("\n") + 1,
            "permalink": (
                f"{repo.get('html_url')}/blob/{repo.get('default_branch')}/{filename}"
            ),
        }
        if tier == policy.TIER_FULL:
            (target / stored_name).write_text(blob["text"], encoding="utf-8")
            info["stored"] = stored_name
        else:
            # Structure only: headings are facts about the document, not the
            # document. Safe to keep even when the file itself is not.
            info["stored"] = None
            info["headings"] = [
                line.strip()
                for line in blob["text"].splitlines()
                if line.lstrip().startswith("#")
            ][:60]
        record["files"][filename] = info

    (target / "meta.json").write_text(
        json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["auto", "code-search", "repo-sweep"], default="auto")
    parser.add_argument("--limit", type=int, default=120, help="max repositories to probe")
    parser.add_argument("--min-stars", type=int, default=2000)
    parser.add_argument("--targets", nargs="*", help="explicit owner/repo pairs to collect")
    parser.add_argument("--candidates", nargs="*", default=None,
                        help="JSON files holding pre-fetched /search/repositories payloads")
    args = parser.parse_args()

    CORPUS.mkdir(parents=True, exist_ok=True)

    prefetched: dict[tuple[str, str], dict] = {}
    if args.candidates:
        for path in args.candidates:
            payload = json.loads(pathlib.Path(path).read_text())
            for repo in payload.get("items", payload if isinstance(payload, list) else []):
                owner = (repo.get("owner") or {}).get("login")
                name = repo.get("name")
                if owner and name:
                    prefetched[(owner, name)] = repo
        gh.log(f"loaded {len(prefetched)} pre-fetched repositories")

    if args.targets:
        candidates = []
        for item in args.targets:
            if "/" not in item:
                gh.log(f"skipping malformed target {item!r}, expected owner/repo")
                continue
            owner, _, name = item.partition("/")
            candidates.append((owner, name))
    elif prefetched:
        candidates = sorted(
            prefetched, key=lambda k: -prefetched[k].get("stargazers_count", 0)
        )[: args.limit]
    else:
        gh.log(f"discovering candidates (mode={args.mode}, limit={args.limit})")
        candidates = []
        if args.mode in ("auto", "code-search"):
            candidates += discover_code_search(args.limit)
        if args.mode in ("auto", "repo-sweep") and len(candidates) < args.limit:
            candidates += discover_repo_sweep(args.limit - len(candidates), args.min_stars)

    seen: set[tuple[str, str]] = set()
    ordered = [c for c in candidates if not (c in seen or seen.add(c))]
    gh.log(f"probing {len(ordered)} repositories")

    added = updated = skipped = 0
    for index, (owner, name) in enumerate(ordered, 1):
        before = load_meta(owner, name)
        try:
            record = collect_repo(owner, name, prefetched.get((owner, name)))
        except gh.RateLimited as err:
            gh.log(f"stopping early: {err}")
            break
        except Exception as err:
            gh.log(f"  !! {owner}/{name}: {err}")
            continue

        if record is None:
            skipped += 1
        elif not before:
            added += 1
            gh.log(f"  + {owner}/{name} ({record['tier']}, {len(record['files'])} files)")
        else:
            before_shas = {k: v.get("sha") for k, v in (before.get("files") or {}).items()}
            after_shas = {k: v.get("sha") for k, v in record["files"].items()}
            if before_shas != after_shas:
                updated += 1
                gh.log(f"  ~ {owner}/{name}")

        if index % 25 == 0:
            gh.log(f"  ...{index}/{len(ordered)}")
        time.sleep(0.15)

    gh.log(f"done: {added} added, {updated} updated, {skipped} without agent files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
