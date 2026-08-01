"""Minimal GitHub REST client: stdlib only, rate-limit aware.

No third-party dependencies on purpose — the weekly Action should run on a bare
`actions/setup-python` with nothing to install and nothing to break.
"""

from __future__ import annotations

import base64
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.github.com"
RAW = "https://raw.githubusercontent.com"
UA = "agents-md-in-the-wild/1.0 (+https://github.com/sattva2020/agents-md-in-the-wild)"


class RateLimited(RuntimeError):
    pass


class NotFound(RuntimeError):
    pass


class Forbidden(RuntimeError):
    """403 that is a permissions problem, not a rate limit — retrying cannot help."""


# Some environments (scoped CI tokens, sandboxes) expose an api.github.com that
# refuses every repository call. Retrying those is pure latency, so after a few
# hard refusals we stop using the REST API for this process and go raw-only.
_hard_refusals = 0
_API_DISABLED_AFTER = 3


def api_available() -> bool:
    return _hard_refusals < _API_DISABLED_AFTER


def _token() -> str | None:
    for key in ("GITHUB_TOKEN", "GH_TOKEN"):
        val = os.environ.get(key)
        if val:
            return val.strip()
    return None


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def request(path: str, params: dict | None = None, *, raw: bool = False, retries: int = 4):
    """GET an API path. Returns parsed JSON, or bytes when raw=True.

    Handles secondary rate limits by honouring Retry-After / X-RateLimit-Reset
    instead of hammering the API, which is what gets tokens blocked.
    """
    url = path if path.startswith("http") else f"{API}{path}"
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"

    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": UA,
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = _token()
    if token:
        headers["Authorization"] = f"Bearer {token}"

    global _hard_refusals
    if not api_available() and "/search/" not in url:
        raise Forbidden("REST API disabled for this process after repeated refusals")

    last_err: Exception | None = None
    for attempt in range(retries):
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                body = resp.read()
                return body if raw else json.loads(body.decode("utf-8"))
        except urllib.error.HTTPError as err:
            last_err = err
            if err.code == 404:
                raise NotFound(url) from err
            if err.code in (403, 429):
                if not _is_rate_limit(err):
                    _hard_refusals += 1
                    raise Forbidden(f"{url}: {err.reason}") from err
                wait = _retry_after(err, attempt)
                log(f"  rate limited ({err.code}), waiting {wait}s — {url}")
                time.sleep(wait)
                continue
            if 500 <= err.code < 600:
                time.sleep(2 ** attempt)
                continue
            raise
        except (urllib.error.URLError, TimeoutError) as err:
            last_err = err
            time.sleep(2 ** attempt)

    raise RateLimited(f"giving up on {url}: {last_err}")


def _is_rate_limit(err: urllib.error.HTTPError) -> bool:
    """Tell a throttle apart from a refusal. Only the throttle is worth retrying."""
    if err.headers.get("Retry-After"):
        return True
    remaining = err.headers.get("X-RateLimit-Remaining")
    if remaining is not None and remaining.strip() == "0":
        return True
    body = ""
    try:
        body = (err.read() or b"").decode("utf-8", errors="replace").lower()
    except Exception:
        pass
    return "rate limit" in body or "abuse" in body or "secondary" in body


def _retry_after(err: urllib.error.HTTPError, attempt: int) -> int:
    retry_after = err.headers.get("Retry-After")
    if retry_after and retry_after.isdigit():
        return min(int(retry_after), 120)
    reset = err.headers.get("X-RateLimit-Reset")
    if reset and reset.isdigit():
        delta = int(reset) - int(time.time())
        if 0 < delta < 300:
            return delta + 2
    return min(60, 5 * (attempt + 1))


def rate_limit() -> dict:
    try:
        return request("/rate_limit")
    except Exception:
        return {}


def quote_path(path: str) -> str:
    """Percent-encode a repo path segment-by-segment, keeping the separators.

    urllib.parse.quote would turn ".github/copilot-instructions.md" into
    ".github%2Fcopilot-instructions.md", which the contents API rejects.
    """
    return "/".join(urllib.parse.quote(part) for part in path.split("/"))


def raw_file(owner: str, repo: str, path: str, ref: str = "HEAD") -> str | None:
    """Fetch a file over raw.githubusercontent.com.

    Used as a fallback when the REST API is unreachable or the token is scoped
    to a single repository (which is the case inside some CI sandboxes). Costs
    no API quota, but yields no blob SHA — callers hash the content instead.
    """
    url = f"{RAW}/{owner}/{repo}/{ref}/{quote_path(path)}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read(400_000)
            return body.decode("utf-8", errors="replace")
    except urllib.error.HTTPError as err:
        if err.code in (404, 403):
            return None
        return None
    except Exception:
        return None


def content_sha(text: str) -> str:
    """Git blob SHA-1 of the given text, so raw fetches produce comparable ids."""
    import hashlib

    payload = text.encode("utf-8")
    header = f"blob {len(payload)}\0".encode()
    return hashlib.sha1(header + payload).hexdigest()


def get_file(owner: str, repo: str, path: str, ref: str | None = None) -> tuple[str, str] | None:
    """Return (text, sha) for a file, or None when it does not exist.

    Skips anything that is not a regular file, and anything over 400 KB — a
    thousand-line AGENTS.md is interesting, a vendored blob is not.
    """
    params = {"ref": ref} if ref else None
    try:
        meta = request(f"/repos/{owner}/{repo}/contents/{quote_path(path)}", params)
    except NotFound:
        return None
    except Exception:
        text = raw_file(owner, repo, path, ref or "HEAD")
        return (text, content_sha(text)) if text is not None else None

    if isinstance(meta, list) or meta.get("type") != "file":
        return None
    if meta.get("size", 0) > 400_000:
        return None

    content = meta.get("content")
    if content and meta.get("encoding") == "base64":
        try:
            text = base64.b64decode(content).decode("utf-8", errors="replace")
        except Exception:
            return None
    elif meta.get("download_url"):
        text = request(meta["download_url"], raw=True).decode("utf-8", errors="replace")
    else:
        return None

    return text, meta.get("sha", "")


def search_repositories(query: str, *, per_page: int = 100, pages: int = 1, sort: str = "stars"):
    """Yield repository objects from the search API.

    The search API hard-caps at 1000 results per query, so callers slice the
    space by language / star band rather than paging past that.
    """
    for page in range(1, pages + 1):
        payload = request(
            "/search/repositories",
            {"q": query, "sort": sort, "order": "desc", "per_page": per_page, "page": page},
        )
        items = payload.get("items", [])
        for item in items:
            yield item
        if len(items) < per_page:
            return
        time.sleep(2)  # search API: 30 req/min authenticated


def search_code(query: str, *, per_page: int = 100, pages: int = 1):
    """Yield code-search hits. Requires an authenticated token; 10 req/min."""
    for page in range(1, pages + 1):
        payload = request(
            "/search/code", {"q": query, "per_page": per_page, "page": page}
        )
        items = payload.get("items", [])
        for item in items:
            yield item
        if len(items) < per_page:
            return
        time.sleep(7)
