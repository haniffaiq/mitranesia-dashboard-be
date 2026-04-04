from __future__ import annotations

import argparse
import json
import subprocess
import sys
import uuid
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.db.session import create_engine_and_session
from app.models.merchant import Merchant
from app.models.merchant_package import MerchantPackage


ROOT_DIR = BACKEND_DIR.parent
DEFAULT_SOURCE = ROOT_DIR / "Mitra-Revamp" / "client" / "src" / "data" / "merchants.ts"


@dataclass
class FrontendPackage:
    name: str
    price: int
    description: str
    sort_order: int


@dataclass
class FrontendMerchant:
    id: uuid.UUID
    name: str
    slug: str
    category: str
    logo_url: str
    bep_months: int
    type: str
    packages: list[FrontendPackage]
    is_top_merchant: bool
    rating: Decimal | None
    description: str | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import merchants from Mitra-Revamp frontend data into backend database.")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE, help="Path to Mitra-Revamp/client/src/data/merchants.ts")
    parser.add_argument("--dry-run", action="store_true", help="Parse and print summary without writing to the database")
    return parser.parse_args()


def load_frontend_merchants(source: Path) -> list[FrontendMerchant]:
    if not source.exists():
        raise FileNotFoundError(f"Source file not found: {source}")

    node_program = r"""
const fs = require("fs");
const vm = require("vm");

const sourcePath = process.argv[1];
const content = fs.readFileSync(sourcePath, "utf8");
const match = content.match(/export const DUMMY_MERCHANTS:\s*MerchantProps\[\]\s*=\s*(\[[\s\S]*?\n\]);/);

if (!match) {
  throw new Error("Could not find DUMMY_MERCHANTS array in merchants.ts");
}

function createPackage(name, price, description) {
  return {
    id: name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, ""),
    name,
    price,
    description,
  };
}

function createDefaultPackages(basePrice) {
  const premiumPrice = Math.ceil((basePrice * 1.35) / 1000000) * 1000000;
  return [
    createPackage(
      "Paket Starter",
      basePrice,
      "Paket awal untuk memulai operasional outlet dengan kebutuhan utama yang paling esensial."
    ),
    createPackage(
      "Paket Premium",
      premiumPrice,
      "Paket pengembangan dengan dukungan perlengkapan dan aktivasi operasional yang lebih lengkap."
    ),
  ];
}

const sandbox = { createPackage, createDefaultPackages };
const merchants = vm.runInNewContext(match[1], sandbox);
process.stdout.write(JSON.stringify(merchants));
"""

    result = subprocess.run(
        ["node", "-e", node_program, str(source)],
        check=True,
        capture_output=True,
        text=True,
    )
    raw_merchants = json.loads(result.stdout)

    merchants: list[FrontendMerchant] = []
    for raw in raw_merchants:
        merchants.append(
            FrontendMerchant(
                id=uuid.UUID(raw["id"]),
                name=raw["name"],
                slug=raw["slug"],
                category=raw["category"],
                logo_url=raw["logoUrl"],
                bep_months=int(raw["bepMonths"]),
                type=raw["type"],
                packages=[
                    FrontendPackage(
                        name=item["name"],
                        price=int(item["price"]),
                        description=item["description"],
                        sort_order=index + 1,
                    )
                    for index, item in enumerate(raw["packages"])
                ],
                is_top_merchant=bool(raw.get("isTopMerchant", False)),
                rating=Decimal(str(raw["rating"])) if raw.get("rating") is not None else None,
                description=raw.get("description"),
            )
        )
    return merchants


def sync_merchant(db: Session, payload: FrontendMerchant) -> tuple[str, Merchant]:
    merchant = db.scalar(
        select(Merchant)
        .options(selectinload(Merchant.packages))
        .where((Merchant.id == payload.id) | (Merchant.slug == payload.slug))
    )

    action = "updated"
    if merchant is None:
        merchant = Merchant(id=payload.id)
        db.add(merchant)
        action = "created"

    merchant.name = payload.name
    merchant.slug = payload.slug
    merchant.category = payload.category
    merchant.type = payload.type
    merchant.logo_url = payload.logo_url
    merchant.bep_months = payload.bep_months
    merchant.rating = payload.rating
    merchant.is_active = True
    merchant.is_top_merchant = payload.is_top_merchant
    merchant.description = payload.description
    merchant.packages[:] = [
        MerchantPackage(
            name=item.name,
            price=item.price,
            description=item.description,
            sort_order=item.sort_order,
        )
        for item in payload.packages
    ]
    return action, merchant


def main() -> int:
    args = parse_args()
    merchants = load_frontend_merchants(args.source)

    if args.dry_run:
        print(f"Parsed {len(merchants)} merchants from {args.source}")
        for merchant in merchants:
            print(f"- {merchant.slug}: {len(merchant.packages)} packages")
        return 0

    settings = get_settings()
    engine, session_local = create_engine_and_session(settings)

    created = 0
    updated = 0

    with session_local() as db:
        for item in merchants:
            action, merchant = sync_merchant(db, item)
            if action == "created":
                created += 1
            else:
                updated += 1
            db.flush()
            print(f"{action}: {merchant.slug}")
        db.commit()

    print(f"Import complete. created={created}, updated={updated}, total={len(merchants)}")
    engine.dispose()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
