import os
import ssl
import time
import requests
import urllib3
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings()
load_dotenv()

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

TCG_BASE = "https://api.pokemontcg.io/v2"
TCG_HEADERS = {"X-Api-Key": os.getenv("POKEMON_TCG_API_KEY")}
PAGE_SIZE = 250
BATCH_SIZE = 50  # items to insert per Supabase call

FINISH_LABELS = {
    "normal": "Normal",
    "holofoil": "Holo",
    "reverseHolofoil": "Reverse Holo",
    "1stEditionHolofoil": "1st Edition Holo",
    "1stEditionNormal": "1st Edition Normal",
    "unlimitedHolofoil": "Unlimited Holo",
}

# Set ONLY_SETS to a list of set IDs to limit import, or None for all cards
# Example: ONLY_SETS = ["base1", "base2", "neo1"]
ONLY_SETS = None  # Import all cards


def get_category_id() -> str:
    res = supabase.table("categories").select("id").eq("slug", "trading-cards").single().execute()
    return res.data["id"]


def get_existing_tcg_ids() -> set:
    print("Loading existing card IDs from database...")
    existing = set()
    page = 0
    page_size = 1000
    while True:
        res = supabase.table("items")\
            .select("metadata")\
            .not_.is_("metadata", "null")\
            .range(page * page_size, (page + 1) * page_size - 1)\
            .execute()
        rows = res.data or []
        for row in rows:
            tcg_id = (row.get("metadata") or {}).get("tcg_id")
            if tcg_id:
                existing.add(tcg_id)
        if len(rows) < page_size:
            break
        page += 1
    print(f"  Found {len(existing)} cards already in DB.")
    return existing


def fetch_page(page: int) -> tuple[list, int]:
    params = {"page": page, "pageSize": PAGE_SIZE, "orderBy": "set.releaseDate"}
    if ONLY_SETS:
        set_filter = " OR ".join(f'set.id:{s}' for s in ONLY_SETS)
        params["q"] = set_filter
    resp = requests.get(f"{TCG_BASE}/cards", headers=TCG_HEADERS, params=params, verify=False)
    resp.raise_for_status()
    data = resp.json()
    return data.get("data", []), data.get("totalCount", 0)


def import_batch(cards: list[dict], category_id: str) -> int:
    if not cards:
        return 0

    # Build item rows
    item_rows = []
    for card in cards:
        set_name = card.get("set", {}).get("name", "")
        number = card.get("number", "")
        name = f"{card['name']} - {set_name} #{number}" if set_name else card["name"]
        image = card.get("images", {}).get("large") or card.get("images", {}).get("small")
        item_rows.append({
            "name": name,
            "brand": "Pokemon",
            "category_id": category_id,
            "image_url": image,
            "metadata": {
                "tcg_id": card["id"],
                "set": set_name,
                "set_id": card.get("set", {}).get("id"),
                "number": number,
                "rarity": card.get("rarity"),
                "supertype": card.get("supertype"),
                "hp": card.get("hp"),
                "types": card.get("types"),
            },
        })

    items_res = supabase.table("items").insert(item_rows).execute()
    inserted_items = items_res.data

    # Build variant rows — track metadata for price insertion
    variant_rows = []
    variant_meta = []  # parallel list: (card, finish) per variant row

    for card, item in zip(cards, inserted_items):
        tcg_prices = card.get("tcgplayer", {}).get("prices", {})
        if tcg_prices:
            for finish, _ in tcg_prices.items():
                variant_rows.append({
                    "item_id": item["id"],
                    "variant_type": "finish",
                    "variant_value": FINISH_LABELS.get(finish, finish),
                    "grader": None,
                })
                variant_meta.append((card, item["id"], finish))
        else:
            # No price finishes — create a basic Raw variant
            variant_rows.append({
                "item_id": item["id"],
                "variant_type": "condition",
                "variant_value": "Raw",
                "grader": None,
            })
            variant_meta.append((card, item["id"], None))

    variants_res = supabase.table("item_variants").insert(variant_rows).execute()
    inserted_variants = variants_res.data

    # Build price history rows
    price_rows = []
    for variant, (card, item_id, finish) in zip(inserted_variants, variant_meta):
        if not finish:
            continue
        price_data = card.get("tcgplayer", {}).get("prices", {}).get(finish, {})
        market = price_data.get("market") or price_data.get("mid")
        if market:
            price_rows.append({
                "item_id": item_id,
                "variant_id": variant["id"],
                "source": f"tcg_tcgplayer_{finish}",
                "source_listing_id": f"tcg-{item_id[:8]}-{finish}",
                "sold_price": market,
                "currency": "USD",
                "sold_at": datetime.utcnow().isoformat(),
            })

        # Also grab cardmarket avg30 on the first finish only
        if finish == list(card.get("tcgplayer", {}).get("prices", {}).keys())[0]:
            avg30 = card.get("cardmarket", {}).get("prices", {}).get("avg30")
            if avg30:
                price_rows.append({
                    "item_id": item_id,
                    "variant_id": variant["id"],
                    "source": "tcg_cardmarket_avg30",
                    "source_listing_id": f"tcg-{item_id[:8]}-cardmarket",
                    "sold_price": avg30,
                    "currency": "EUR",
                    "sold_at": datetime.utcnow().isoformat(),
                })

    if price_rows:
        supabase.table("price_history").upsert(price_rows, on_conflict="source,source_listing_id").execute()

    return len(inserted_items)


def run():
    category_id = get_category_id()
    existing_ids = get_existing_tcg_ids()

    page = 1
    total_imported = 0
    total_cards = None

    print("Starting Pokemon card import...")
    while True:
        cards, total_count = fetch_page(page)
        if total_cards is None:
            total_cards = total_count
            print(f"Total cards in API: {total_cards}")

        if not cards:
            break

        # Filter out already-imported cards
        new_cards = [c for c in cards if c["id"] not in existing_ids]

        # Process in sub-batches
        for i in range(0, len(new_cards), BATCH_SIZE):
            batch = new_cards[i:i + BATCH_SIZE]
            count = import_batch(batch, category_id)
            total_imported += count
            for card in batch:
                existing_ids.add(card["id"])

        skipped = len(cards) - len(new_cards)
        print(f"Page {page}: {len(new_cards)} imported, {skipped} skipped | Total so far: {total_imported}")

        if len(cards) < PAGE_SIZE:
            break

        page += 1
        time.sleep(0.1)  # be polite to the API

    print(f"\nDone! Imported {total_imported} new Pokemon cards.")


if __name__ == "__main__":
    run()
