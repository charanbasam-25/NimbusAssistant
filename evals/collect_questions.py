"""Collect candidate FastAPI questions from the Stack Exchange API.

Raw API pages and candidate records are written below data/raw/questions/, which
is Git-ignored. These are candidates only: they are not evaluation labels.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import time
from collections.abc import Iterable
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw" / "questions"
API_URL = "https://api.stackexchange.com/2.3/questions"
API_USER_AGENT = "NimbusCapstoneQuestionCollector/1.0 (educational evaluation research)"


class _TextExtractor(HTMLParser):
    """Extract readable HTML text while measuring whether a post is code-only."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.code_chars = 0
        self._code_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"pre", "code"}:
            self._code_depth += 1
        if tag in {"p", "li", "br", "div"}:
            self.parts.append(" ")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"pre", "code"} and self._code_depth:
            self._code_depth -= 1
        if tag in {"p", "li", "pre", "div"}:
            self.parts.append(" ")

    def handle_data(self, data: str) -> None:
        self.parts.append(data)
        if self._code_depth:
            self.code_chars += len(data)


def plain_text(markup: str) -> tuple[str, int]:
    parser = _TextExtractor()
    parser.feed(markup)
    text = re.sub(r"\s+", " ", html.unescape("".join(parser.parts))).strip()
    return text, parser.code_chars


def _is_english(title: str, body: str) -> bool:
    sample = f"{title} {body}"
    if re.search(r"[¿¡áéíóúñüàèìòùçâêîôûäëïöü]", sample, re.IGNORECASE):
        return False
    letters = [character for character in sample if character.isalpha()]
    if len(letters) < 20:
        return False
    ascii_letters = sum(character.isascii() for character in letters)
    return ascii_letters / len(letters) >= 0.85


def _is_code_dump(title: str, body: str, code_chars: int) -> bool:
    if not body:
        return True
    # Code-heavy posts with almost no readable explanation are poor standalone
    # question candidates, even if Stack Overflow's title is descriptive.
    return code_chars >= 240 and code_chars / max(1, len(body)) >= 0.72 and len(body) < 800


def _is_off_topic(title: str, body: str, tags: Iterable[str]) -> bool:
    combined = f"{title} {body}".casefold()
    normalized_tags = {tag.casefold() for tag in tags}
    if "fastapi" not in normalized_tags:
        return True
    if (
        "sqlalchemy" in normalized_tags
        and "fastapi" not in title.casefold()
        and not (
            "fastapi" in body.casefold()
            and any(term in combined for term in ("dependency", "request", "endpoint", "route"))
        )
    ):
        return True
    cloud_hosts = ("heroku", "vercel", "railway", "render.com", "aws lambda", "azure functions")
    return any(host in combined for host in cloud_hosts) and not any(
        term in combined for term in ("fastapi app", "fastapi application", "fastapi route")
    )


def parse_question(item: dict, collected_on: str | None = None) -> dict | None:
    """Return a normalized candidate, or None when it fails the corpus filters."""
    title = html.unescape(str(item.get("title", ""))).strip()
    body_markup = str(item.get("body", ""))
    body, code_chars = plain_text(body_markup)
    tags = item.get("tags", [])
    if not title or not body or not isinstance(tags, list):
        return None
    if not (item.get("accepted_answer_id") or int(item.get("score", 0)) >= 2):
        return None
    if not _is_english(title, body) or _is_code_dump(title, body, code_chars):
        return None
    if _is_off_topic(title, body, tags):
        return None
    question_id = item.get("question_id")
    if not question_id:
        return None
    excerpt = body[:700].rstrip()
    if len(body) > len(excerpt):
        excerpt = excerpt.rsplit(" ", 1)[0] + "…"
    return {
        "source": "stackoverflow",
        "source_id": str(question_id),
        "url": item.get("link", f"https://stackoverflow.com/q/{question_id}"),
        "title": title,
        "body_excerpt": excerpt,
        "tags": sorted({str(tag) for tag in tags}),
        "score": int(item.get("score", 0)),
        "created_at": item.get("creation_date"),
        "has_accepted_answer": bool(item.get("accepted_answer_id")),
        "license": "CC BY-SA 4.0",
        "collected_on": collected_on or date.today().isoformat(),
    }


def filter_questions(items: Iterable[dict], collected_on: str | None = None) -> list[dict]:
    """Normalize, filter and deterministically deduplicate API question items."""
    candidates: list[dict] = []
    seen_ids: set[str] = set()
    seen_titles: set[str] = set()
    for item in items:
        candidate = parse_question(item, collected_on=collected_on)
        if candidate is None:
            continue
        title_key = re.sub(r"[^a-z0-9]+", " ", candidate["title"].casefold()).strip()
        if candidate["source_id"] in seen_ids or title_key in seen_titles:
            continue
        seen_ids.add(candidate["source_id"])
        seen_titles.add(title_key)
        candidates.append(candidate)
    return sorted(candidates, key=lambda row: (-row["score"], int(row["source_id"])))


def fetch_page(page: int, cache_dir: Path = RAW_DIR) -> dict:
    """Fetch one API page, reusing its raw cache when available."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / f"stackoverflow-page-{page:02d}.json"
    if cache_path.exists():
        return json.loads(cache_path.read_text(encoding="utf-8"))
    params = urlencode(
        {
            "tagged": "fastapi",
            "site": "stackoverflow",
            "sort": "votes",
            "order": "desc",
            "pagesize": 100,
            "page": page,
            "filter": "withbody",
        }
    )
    request = Request(f"{API_URL}?{params}", headers={"User-Agent": API_USER_AGENT})
    with urlopen(request, timeout=30) as response:
        payload = json.load(response)
    cache_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def collect(max_pages: int, cache_dir: Path = RAW_DIR, pause_seconds: float = 0.0) -> list[dict]:
    """Collect pages until the requested limit, API quota, or paging end."""
    items: list[dict] = []
    for page in range(1, max_pages + 1):
        payload = fetch_page(page, cache_dir)
        items.extend(payload.get("items", []))
        backoff = payload.get("backoff", 0)
        if backoff:
            time.sleep(max(float(backoff), pause_seconds))
        elif pause_seconds:
            time.sleep(pause_seconds)
        if payload.get("quota_remaining", 1) <= 0 or not payload.get("has_more", False):
            break
    return filter_questions(items)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pages", type=int, default=2, help="maximum Stack Exchange pages")
    parser.add_argument("--pause", type=float, default=0.0, help="extra pause between API pages")
    parser.add_argument("--output", type=Path, default=RAW_DIR / "candidates.jsonl")
    args = parser.parse_args()
    if args.pages < 1 or args.pause < 0:
        parser.error("--pages must be positive and --pause cannot be negative")
    candidates = collect(args.pages, pause_seconds=args.pause)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in candidates),
        encoding="utf-8",
    )
    print(f"Wrote {len(candidates)} candidates to {args.output}")
    if not __import__("os").environ.get("GH_TOKEN"):
        print("GitHub Discussions source skipped: GH_TOKEN is not set.")


if __name__ == "__main__":
    main()
