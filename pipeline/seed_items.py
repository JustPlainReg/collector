import os
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

# ---------------------------------------------------------------------------
# Item catalog with realistic pricing
# ---------------------------------------------------------------------------

ITEMS = [
    # --- TRADING CARDS ---
    {
        "category": "trading-cards",
        "name": "Charizard 1st Edition Base Set Holo",
        "brand": "Pokemon",
        "metadata": {"game": "Pokemon", "set": "Base Set 1st Edition", "number": "4/102", "rarity": "Holo Rare"},
        "variants": [
            {"type": "condition", "value": "Raw",    "grader": None,  "price": 14000, "variance": 2500},
            {"type": "grade",     "value": "9",      "grader": "PSA", "price": 80000, "variance": 12000},
            {"type": "grade",     "value": "10",     "grader": "PSA", "price": 380000,"variance": 50000},
        ],
    },
    {
        "category": "trading-cards",
        "name": "Shadowless Charizard Base Set Holo",
        "brand": "Pokemon",
        "metadata": {"game": "Pokemon", "set": "Base Set Shadowless", "number": "4/102", "rarity": "Holo Rare"},
        "variants": [
            {"type": "condition", "value": "Raw",    "grader": None,  "price": 4000,  "variance": 800},
            {"type": "grade",     "value": "9",      "grader": "PSA", "price": 18000, "variance": 3000},
            {"type": "grade",     "value": "10",     "grader": "PSA", "price": 50000, "variance": 8000},
        ],
    },
    {
        "category": "trading-cards",
        "name": "Blastoise 1st Edition Base Set Holo",
        "brand": "Pokemon",
        "metadata": {"game": "Pokemon", "set": "Base Set 1st Edition", "number": "2/102", "rarity": "Holo Rare"},
        "variants": [
            {"type": "condition", "value": "Raw",    "grader": None,  "price": 3500,  "variance": 700},
            {"type": "grade",     "value": "9",      "grader": "PSA", "price": 14000, "variance": 2500},
            {"type": "grade",     "value": "10",     "grader": "PSA", "price": 100000,"variance": 18000},
        ],
    },
    {
        "category": "trading-cards",
        "name": "Lugia 1st Edition Neo Genesis Holo",
        "brand": "Pokemon",
        "metadata": {"game": "Pokemon", "set": "Neo Genesis 1st Edition", "number": "9/111", "rarity": "Holo Rare"},
        "variants": [
            {"type": "condition", "value": "Raw",    "grader": None,  "price": 1200,  "variance": 300},
            {"type": "grade",     "value": "9",      "grader": "PSA", "price": 6000,  "variance": 1000},
            {"type": "grade",     "value": "10",     "grader": "PSA", "price": 30000, "variance": 5000},
        ],
    },
    {
        "category": "trading-cards",
        "name": "Espeon Gold Star",
        "brand": "Pokemon",
        "metadata": {"game": "Pokemon", "set": "POP Series 5", "number": "16/17", "rarity": "Gold Star"},
        "variants": [
            {"type": "condition", "value": "Raw",    "grader": None,  "price": 2000,  "variance": 400},
            {"type": "grade",     "value": "9",      "grader": "PSA", "price": 8000,  "variance": 1500},
            {"type": "grade",     "value": "10",     "grader": "PSA", "price": 28000, "variance": 5000},
        ],
    },
    {
        "category": "trading-cards",
        "name": "Black Lotus Alpha",
        "brand": "Magic: The Gathering",
        "metadata": {"game": "Magic: The Gathering", "set": "Alpha", "rarity": "Rare"},
        "variants": [
            {"type": "condition", "value": "Raw",    "grader": None,  "price": 35000, "variance": 6000},
            {"type": "grade",     "value": "9",      "grader": "PSA", "price": 120000,"variance": 20000},
            {"type": "grade",     "value": "10",     "grader": "PSA", "price": 500000,"variance": 80000},
        ],
    },
    {
        "category": "trading-cards",
        "name": "1952 Topps Mickey Mantle #311",
        "brand": "Topps",
        "metadata": {"game": "Baseball", "set": "1952 Topps", "number": "311", "player": "Mickey Mantle"},
        "variants": [
            {"type": "condition", "value": "Raw",    "grader": None,  "price": 25000, "variance": 5000},
            {"type": "grade",     "value": "7",      "grader": "PSA", "price": 150000,"variance": 25000},
            {"type": "grade",     "value": "9",      "grader": "PSA", "price": 1200000,"variance": 200000},
        ],
    },
    {
        "category": "trading-cards",
        "name": "LeBron James 2003-04 Upper Deck Exquisite Rookie Patch Auto",
        "brand": "Upper Deck",
        "metadata": {"game": "Basketball", "set": "2003-04 Exquisite Collection", "player": "LeBron James", "rarity": "Rookie Patch Auto"},
        "variants": [
            {"type": "condition", "value": "Raw",    "grader": None,  "price": 80000, "variance": 15000},
            {"type": "grade",     "value": "9",      "grader": "PSA", "price": 300000,"variance": 50000},
            {"type": "grade",     "value": "10",     "grader": "PSA", "price": 1800000,"variance": 300000},
        ],
    },

    # --- VIDEO GAMES ---
    {
        "category": "video-games",
        "name": "Super Mario Bros.",
        "brand": "Nintendo",
        "metadata": {"platform": "NES", "region": "NTSC", "publisher": "Nintendo", "year": 1985},
        "variants": [
            {"type": "condition", "value": "Loose",  "grader": None,   "price": 80,    "variance": 30},
            {"type": "condition", "value": "CIB",    "grader": None,   "price": 3000,  "variance": 600},
            {"type": "condition", "value": "Sealed", "grader": None,   "price": 70000, "variance": 15000},
            {"type": "grade",     "value": "9.0",    "grader": "WATA", "price": 55000, "variance": 10000},
        ],
    },
    {
        "category": "video-games",
        "name": "The Legend of Zelda",
        "brand": "Nintendo",
        "metadata": {"platform": "NES", "region": "NTSC", "publisher": "Nintendo", "year": 1987},
        "variants": [
            {"type": "condition", "value": "Loose",  "grader": None,   "price": 60,    "variance": 20},
            {"type": "condition", "value": "CIB",    "grader": None,   "price": 1500,  "variance": 400},
            {"type": "condition", "value": "Sealed", "grader": None,   "price": 50000, "variance": 12000},
            {"type": "grade",     "value": "9.0",    "grader": "WATA", "price": 40000, "variance": 8000},
        ],
    },
    {
        "category": "video-games",
        "name": "EarthBound",
        "brand": "Nintendo",
        "metadata": {"platform": "SNES", "region": "NTSC", "publisher": "Nintendo", "year": 1995},
        "variants": [
            {"type": "condition", "value": "Loose",  "grader": None,   "price": 250,   "variance": 60},
            {"type": "condition", "value": "CIB",    "grader": None,   "price": 900,   "variance": 200},
            {"type": "condition", "value": "Sealed", "grader": None,   "price": 9000,  "variance": 2000},
        ],
    },
    {
        "category": "video-games",
        "name": "Pokemon Red Version",
        "brand": "Nintendo",
        "metadata": {"platform": "Game Boy", "region": "NTSC", "publisher": "Nintendo", "year": 1998},
        "variants": [
            {"type": "condition", "value": "Loose",  "grader": None,   "price": 50,    "variance": 15},
            {"type": "condition", "value": "CIB",    "grader": None,   "price": 350,   "variance": 80},
            {"type": "condition", "value": "Sealed", "grader": None,   "price": 12000, "variance": 3000},
            {"type": "grade",     "value": "9.0",    "grader": "WATA", "price": 10000, "variance": 2000},
        ],
    },
    {
        "category": "video-games",
        "name": "Stadium Events",
        "brand": "Bandai",
        "metadata": {"platform": "NES", "region": "NTSC", "publisher": "Bandai", "year": 1987},
        "variants": [
            {"type": "condition", "value": "Loose",  "grader": None,   "price": 5000,  "variance": 1000},
            {"type": "condition", "value": "CIB",    "grader": None,   "price": 25000, "variance": 5000},
            {"type": "condition", "value": "Sealed", "grader": None,   "price": 200000,"variance": 40000},
        ],
    },
    {
        "category": "video-games",
        "name": "Chrono Trigger",
        "brand": "Square",
        "metadata": {"platform": "SNES", "region": "NTSC", "publisher": "Square", "year": 1995},
        "variants": [
            {"type": "condition", "value": "Loose",  "grader": None,   "price": 100,   "variance": 30},
            {"type": "condition", "value": "CIB",    "grader": None,   "price": 400,   "variance": 100},
            {"type": "condition", "value": "Sealed", "grader": None,   "price": 6000,  "variance": 1500},
        ],
    },

    # --- COMICS ---
    {
        "category": "comics",
        "name": "Amazing Fantasy #15",
        "brand": "Marvel Comics",
        "metadata": {"publisher": "Marvel", "issue": 15, "year": 1962, "key_issue": "First appearance of Spider-Man"},
        "variants": [
            {"type": "condition", "value": "Raw",    "grader": None,  "price": 8000,  "variance": 2000},
            {"type": "grade",     "value": "4.0",    "grader": "CGC", "price": 25000, "variance": 5000},
            {"type": "grade",     "value": "8.0",    "grader": "CGC", "price": 120000,"variance": 20000},
            {"type": "grade",     "value": "9.0",    "grader": "CGC", "price": 300000,"variance": 50000},
        ],
    },
    {
        "category": "comics",
        "name": "Amazing Spider-Man #1",
        "brand": "Marvel Comics",
        "metadata": {"publisher": "Marvel", "issue": 1, "year": 1963, "key_issue": "First solo Spider-Man series"},
        "variants": [
            {"type": "condition", "value": "Raw",    "grader": None,  "price": 3500,  "variance": 700},
            {"type": "grade",     "value": "6.0",    "grader": "CGC", "price": 12000, "variance": 2500},
            {"type": "grade",     "value": "9.0",    "grader": "CGC", "price": 55000, "variance": 10000},
            {"type": "grade",     "value": "9.6",    "grader": "CGC", "price": 180000,"variance": 30000},
        ],
    },
    {
        "category": "comics",
        "name": "X-Men #1",
        "brand": "Marvel Comics",
        "metadata": {"publisher": "Marvel", "issue": 1, "year": 1963, "key_issue": "First appearance of the X-Men"},
        "variants": [
            {"type": "condition", "value": "Raw",    "grader": None,  "price": 2000,  "variance": 500},
            {"type": "grade",     "value": "6.0",    "grader": "CGC", "price": 8000,  "variance": 1500},
            {"type": "grade",     "value": "9.0",    "grader": "CGC", "price": 40000, "variance": 7000},
        ],
    },
    {
        "category": "comics",
        "name": "Incredible Hulk #1",
        "brand": "Marvel Comics",
        "metadata": {"publisher": "Marvel", "issue": 1, "year": 1962, "key_issue": "First appearance of the Hulk"},
        "variants": [
            {"type": "condition", "value": "Raw",    "grader": None,  "price": 4000,  "variance": 900},
            {"type": "grade",     "value": "6.0",    "grader": "CGC", "price": 18000, "variance": 3500},
            {"type": "grade",     "value": "9.0",    "grader": "CGC", "price": 80000, "variance": 15000},
        ],
    },
    {
        "category": "comics",
        "name": "Batman #1",
        "brand": "DC Comics",
        "metadata": {"publisher": "DC", "issue": 1, "year": 1940, "key_issue": "First appearance of Joker and Catwoman"},
        "variants": [
            {"type": "condition", "value": "Raw",    "grader": None,  "price": 10000, "variance": 2500},
            {"type": "grade",     "value": "4.0",    "grader": "CGC", "price": 50000, "variance": 10000},
            {"type": "grade",     "value": "8.0",    "grader": "CGC", "price": 300000,"variance": 60000},
        ],
    },
    {
        "category": "comics",
        "name": "Fantastic Four #1",
        "brand": "Marvel Comics",
        "metadata": {"publisher": "Marvel", "issue": 1, "year": 1961, "key_issue": "First appearance of the Fantastic Four"},
        "variants": [
            {"type": "condition", "value": "Raw",    "grader": None,  "price": 3000,  "variance": 700},
            {"type": "grade",     "value": "6.0",    "grader": "CGC", "price": 12000, "variance": 2500},
            {"type": "grade",     "value": "9.0",    "grader": "CGC", "price": 60000, "variance": 12000},
        ],
    },
]

# ---------------------------------------------------------------------------

def seed_price_history(item_id, variant_id, base_price, variance, num_sales=40):
    rows = []
    for i in range(num_sales):
        days_ago = random.randint(0, 180)
        sold_at = datetime.utcnow() - timedelta(days=days_ago)
        price = round(max(base_price + random.uniform(-variance, variance), 1.0), 2)
        rows.append({
            "item_id": item_id,
            "variant_id": variant_id,
            "source": "ebay",
            "source_listing_id": f"SEED-{item_id[:8]}-{variant_id[:8] if variant_id else 'novar'}-{i}",
            "sold_price": price,
            "currency": "USD",
            "sold_at": sold_at.isoformat(),
        })
    supabase.table("price_history").upsert(rows, on_conflict="source,source_listing_id").execute()


def run():
    # Fetch category slugs → IDs
    cats = supabase.table("categories").select("id, slug").execute().data
    cat_map = {c["slug"]: c["id"] for c in cats}

    for item_def in ITEMS:
        cat_id = cat_map[item_def["category"]]

        # Insert item
        item_res = supabase.table("items").insert({
            "category_id": cat_id,
            "name": item_def["name"],
            "brand": item_def["brand"],
            "metadata": item_def["metadata"],
        }).execute()
        item_id = item_res.data[0]["id"]
        print(f"Item: {item_def['name']}")

        for v in item_def["variants"]:
            # Insert variant
            var_res = supabase.table("item_variants").insert({
                "item_id": item_id,
                "variant_type": v["type"],
                "variant_value": v["value"],
                "grader": v["grader"],
            }).execute()
            variant_id = var_res.data[0]["id"]

            # Seed price history for this variant
            seed_price_history(item_id, variant_id, v["price"], v["variance"])
            label = f"{v['grader']} {v['value']}" if v["grader"] else v["value"]
            print(f"  ✓ {label} — ~${v['price']:,}")

    print("\nDone! All items seeded.")


if __name__ == "__main__":
    run()
