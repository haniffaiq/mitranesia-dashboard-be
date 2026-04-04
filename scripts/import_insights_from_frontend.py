from __future__ import annotations

import argparse
import json
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote_plus

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import create_engine_and_session
from app.models.insight_article import InsightArticle

ROOT_DIR = BACKEND_DIR.parent
DEFAULT_SOURCE = ROOT_DIR / "Mitra-Revamp" / "client" / "src" / "data" / "insights.ts"

MONTHS = {
    "Jan": 1,
    "Feb": 2,
    "Mar": 3,
    "Apr": 4,
    "Mei": 5,
    "Jun": 6,
    "Jul": 7,
    "Agu": 8,
    "Sep": 9,
    "Okt": 10,
    "Nov": 11,
    "Des": 12,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import insights from Mitra-Revamp frontend data into backend database.")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE, help="Path to Mitra-Revamp/client/src/data/insights.ts")
    parser.add_argument("--dry-run", action="store_true", help="Parse and print summary without writing to the database")
    return parser.parse_args()


def parse_frontend_date(value: str) -> datetime:
    day, month_name, year = value.split(" ")
    return datetime(int(year), MONTHS[month_name], int(day), 12, 0, 0, tzinfo=timezone.utc)


def normalize_image(value: str, slug: str) -> str:
    if value.startswith("http://") or value.startswith("https://"):
        return value
    return f"https://placehold.co/1200x675/png?text={quote_plus(slug)}"


def load_frontend_insights(source: Path) -> list[dict]:
    if not source.exists():
        raise FileNotFoundError(f"Source file not found: {source}")

    node_program = r"""
const fs = require("fs");
const vm = require("vm");

const sourcePath = process.argv[1];
const content = fs.readFileSync(sourcePath, "utf8");
const imports = Object.fromEntries(
  [...content.matchAll(/^import\s+(\w+)\s+from\s+"([^"]+)";$/gm)].map((match) => [match[1], match[2]])
);
const match = content.match(/export const INSIGHT_ARTICLES:\s*InsightArticle\[\]\s*=\s*(\[[\s\S]*?\n\]);/);

if (!match) {
  throw new Error("Could not find INSIGHT_ARTICLES array in insights.ts");
}

const sandbox = { ...imports };
const insights = vm.runInNewContext(match[1], sandbox);
process.stdout.write(JSON.stringify(insights));
"""

    result = subprocess.run(
        ["node", "-e", node_program, str(source)],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def sync_insight(db: Session, payload: dict) -> str:
    article = db.scalar(select(InsightArticle).where(InsightArticle.slug == payload["slug"]))
    action = "updated"
    if article is None:
        article = InsightArticle(id=uuid.uuid5(uuid.NAMESPACE_URL, payload["slug"]))
        db.add(article)
        action = "created"

    article.title = payload["title"]
    article.slug = payload["slug"]
    article.category = payload["category"]
    article.author = payload["author"]
    article.image = normalize_image(payload["image"], payload["slug"])
    article.excerpt = payload["excerpt"]
    article.read_time = payload["readTime"]
    article.content = payload["content"]
    article.status = "published"
    article.published_at = parse_frontend_date(payload["date"])
    return action


def main() -> int:
    args = parse_args()
    insights = load_frontend_insights(args.source)

    if args.dry_run:
        print(f"Parsed {len(insights)} insights from {args.source}")
        for insight in insights:
            print(f"- {insight['slug']}: {insight['date']}")
        return 0

    settings = get_settings()
    engine, session_local = create_engine_and_session(settings)

    created = 0
    updated = 0
    with session_local() as db:
        for payload in insights:
            action = sync_insight(db, payload)
            if action == "created":
                created += 1
            else:
                updated += 1
            print(f"{action}: {payload['slug']}")
        db.commit()

    print(f"Import complete. created={created}, updated={updated}, total={len(insights)}")
    engine.dispose()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
