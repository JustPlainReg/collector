import os
import requests
import urllib.parse
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

ebay_app_id = os.getenv("EBAY_APP_ID")
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

FINDING_API_URL = "https://svcs.ebay.com/services/search/FindingService/v1"


def fetch_sold_listings(keywords: str, category_id: str = None, max_results: int = 100) -> list[dict]:
    # Build base params normally
    base = {
        "OPERATION-NAME": "findCompletedItems",
        "SERVICE-VERSION": "1.0.0",
        "SECURITY-APPNAME": ebay_app_id,
        "RESPONSE-DATA-FORMAT": "JSON",
        "keywords": keywords,
        "sortOrder": "EndTimeSoonest",
        "paginationInput.entriesPerPage": min(max_results, 100),
    }
    if category_id:
        base["categoryId"] = category_id

    # itemFilter params must NOT have parentheses URL-encoded — build manually
    query = urllib.parse.urlencode(base)
    query += "&itemFilter(0).name=SoldItemsOnly&itemFilter(0).value=true"

    response = requests.get(f"{FINDING_API_URL}?{query}")
    if not response.ok:
        print(f"  Status: {response.status_code}")
        print(f"  Body: {response.text[:1000]}")
    response.raise_for_status()

    data = response.json()
    search_result = data.get("findCompletedItemsResponse", [{}])[0].get("searchResult", [{}])[0]
    return search_result.get("item", [])


def parse_listing(item: dict) -> dict | None:
    try:
        price = float(item["sellingStatus"][0]["currentPrice"][0]["__value__"])
        currency = item["sellingStatus"][0]["currentPrice"][0]["@currencyId"]
        sold_at = item["listingInfo"][0]["endTime"][0]
        listing_id = item["itemId"][0]
        title = item["title"][0]
        return {
            "source": "ebay",
            "source_listing_id": listing_id,
            "sold_price": price,
            "currency": currency,
            "sold_at": sold_at,
            "title": title,
        }
    except (KeyError, IndexError, ValueError):
        return None


def upsert_price_history(item_id: str, listings: list[dict], variant_id: str = None):
    rows = []
    for listing in listings:
        parsed = parse_listing(listing)
        if not parsed:
            continue
        rows.append({
            "item_id": item_id,
            "variant_id": variant_id,
            "source": parsed["source"],
            "source_listing_id": parsed["source_listing_id"],
            "sold_price": parsed["sold_price"],
            "currency": parsed["currency"],
            "sold_at": parsed["sold_at"],
        })

    if not rows:
        print("  No valid listings to insert.")
        return

    # upsert — the unique(source, source_listing_id) constraint prevents duplicates
    result = supabase.table("price_history").upsert(rows, on_conflict="source,source_listing_id").execute()
    print(f"  Upserted {len(rows)} listings.")


def run(search: str, item_id: str, variant_id: str = None, category_id: str = None):
    print(f"Fetching sold listings for: {search}")
    listings = fetch_sold_listings(search, category_id=category_id)
    print(f"  Found {len(listings)} listings")
    upsert_price_history(item_id, listings, variant_id=variant_id)


if __name__ == "__main__":
    run(
        search="Jordan 1 Retro Low OG Fragment Travis Scott",
        item_id="13bf116b-4f99-4b53-b1e6-ba6488539073",
    )
