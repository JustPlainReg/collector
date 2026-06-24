import os
import ssl
import requests
import urllib3
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client

ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings()
load_dotenv()

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

POKEMON_TCG_API = "https://api.pokemontcg.io/v2/cards"


def search_card(name: str) -> dict | None:
    response = requests.get(
        POKEMON_TCG_API,
        params={"q": f'name:"{name}"', "pageSize": 1},
        verify=False,
    )
    if not response.ok:
        return None
    data = response.json().get("data", [])
    return data[0] if data else None


def extract_prices(card: dict) -> list[dict]:
    """Pull TCGPlayer and Cardmarket prices from a card response."""
    prices = []
    now = datetime.utcnow()

    tcg = card.get("tcgplayer", {}).get("prices", {})
    for finish, price_data in tcg.items():
        market = price_data.get("market") or price_data.get("mid")
        low = price_data.get("low")
        high = price_data.get("high")
        if market:
            prices.append({"finish": finish, "source": "tcgplayer", "price": market, "low": low, "high": high})

    cardmarket = card.get("cardmarket", {}).get("prices", {})
    avg30 = cardmarket.get("avg30") or cardmarket.get("averageSellPrice")
    if avg30:
        prices.append({"finish": "market", "source": "cardmarket", "price": avg30, "low": None, "high": None})

    return prices


def upsert_prices(item_id: str, variant_id: str | None, prices: list[dict]):
    rows = []
    for p in prices:
        rows.append({
            "item_id": item_id,
            "variant_id": variant_id,
            "source": f"tcg_{p['source']}_{p['finish']}",
            "source_listing_id": f"tcg-{item_id[:8]}-{p['source']}-{p['finish']}",
            "sold_price": p["price"],
            "currency": "USD",
            "sold_at": datetime.utcnow().isoformat(),
        })

    if rows:
        supabase.table("price_history").upsert(rows, on_conflict="source,source_listing_id").execute()
        print(f"  Upserted {len(rows)} price points.")


def run():
    items = supabase.table("items")\
        .select("id, name, brand, categories(slug), item_variants(id, variant_type, variant_value, grader)")\
        .execute().data

    for item in items:
        category = item.get("categories", {})
        slug = category.get("slug") if isinstance(category, dict) else None
        if slug != "trading-cards":
            continue
        if item.get("brand") not in ("Pokemon",):
            continue

        name = item["name"]
        search_term = name.split(" 1st")[0].split(" Base")[0].split(" Neo")[0]\
                         .split(" Gold")[0].split(" Alpha")[0].strip()

        print(f"Fetching TCG prices: {name}")
        card = search_card(search_term)
        if not card:
            print("  ✗ Not found")
            continue

        prices = extract_prices(card)
        if not prices:
            print("  ✗ No price data")
            continue

        # Attach prices to the Raw variant if it exists, otherwise the item directly
        variants = item.get("item_variants", [])
        raw_variant = next((v for v in variants if v["variant_value"].lower() == "raw"), None)
        variant_id = raw_variant["id"] if raw_variant else None

        upsert_prices(item["id"], variant_id, prices)
        print(f"  ✓ {len(prices)} price points from TCGPlayer/Cardmarket")


if __name__ == "__main__":
    run()
