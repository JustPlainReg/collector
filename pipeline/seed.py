import os
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

def seed_price_history(item_id: str, base_price: float, variance: float, num_sales: int, variant_id: str = None):
    """Insert realistic fake sold listings spread over the last 6 months."""
    rows = []
    for i in range(num_sales):
        days_ago = random.randint(0, 180)
        sold_at = datetime.utcnow() - timedelta(days=days_ago)
        price = round(base_price + random.uniform(-variance, variance), 2)
        price = max(price, 1.0)
        rows.append({
            "item_id": item_id,
            "variant_id": variant_id,
            "source": "ebay",
            "source_listing_id": f"SEED-{item_id[:8]}-{i}",
            "sold_price": price,
            "currency": "USD",
            "sold_at": sold_at.isoformat(),
        })

    result = supabase.table("price_history").upsert(rows, on_conflict="source,source_listing_id").execute()
    print(f"  Seeded {len(rows)} price history rows.")


if __name__ == "__main__":
    # Jordan 1 Fragment x Travis Scott
    FRAGMENT_ID = "13bf116b-4f99-4b53-b1e6-ba6488539073"

    print("Seeding Jordan 1 Fragment x Travis Scott (raw)...")
    seed_price_history(FRAGMENT_ID, base_price=2000, variance=300, num_sales=60)

    print("Done.")
