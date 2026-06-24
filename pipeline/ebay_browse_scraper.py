import os
import ssl
import base64
import requests
import urllib3
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client

ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings()
load_dotenv()

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

EBAY_APP_ID = os.getenv("EBAY_APP_ID")
EBAY_CERT_ID = os.getenv("EBAY_CERT_ID")
OAUTH_URL = "https://api.ebay.com/identity/v1/oauth2/token"
BROWSE_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"

_token_cache = {"token": None, "expires_at": None}


def get_access_token() -> str:
    """Get or refresh the eBay OAuth application token."""
    if _token_cache["token"] and _token_cache["expires_at"] > datetime.utcnow():
        return _token_cache["token"]

    credentials = base64.b64encode(f"{EBAY_APP_ID}:{EBAY_CERT_ID}".encode()).decode()
    response = requests.post(
        OAUTH_URL,
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={
            "grant_type": "client_credentials",
            "scope": "https://api.ebay.com/oauth/api_scope",
        },
        verify=False,
    )
    response.raise_for_status()
    data = response.json()
    _token_cache["token"] = data["access_token"]
    _token_cache["expires_at"] = datetime.utcnow() + timedelta(seconds=data["expires_in"] - 60)
    return _token_cache["token"]


def search_listings(keywords: str, limit: int = 50) -> list[dict]:
    """Search eBay Browse API for active listings."""
    token = get_access_token()
    response = requests.get(
        BROWSE_URL,
        headers={
            "Authorization": f"Bearer {token}",
            "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
            "Content-Type": "application/json",
        },
        params={
            "q": keywords,
            "filter": "buyingOptions:{FIXED_PRICE}",
            "sort": "price",
            "limit": limit,
        },
        verify=False,
    )
    response.raise_for_status()
    return response.json().get("itemSummaries", [])


def upsert_price_history(item_id: str, variant_id: str | None, listings: list[dict]):
    """Insert Browse API listings as price history rows."""
    rows = []
    for item in listings:
        try:
            price = float(item["price"]["value"])
            currency = item["price"]["currency"]
            listing_id = item["itemId"]
            rows.append({
                "item_id": item_id,
                "variant_id": variant_id,
                "source": "ebay_browse",
                "source_listing_id": listing_id,
                "sold_price": price,
                "currency": currency,
                "sold_at": datetime.utcnow().isoformat(),
            })
        except (KeyError, ValueError):
            continue

    if not rows:
        print("  No valid listings found.")
        return

    supabase.table("price_history").upsert(rows, on_conflict="source,source_listing_id").execute()
    print(f"  Upserted {len(rows)} listings.")


def run(search: str, item_id: str, variant_id: str | None = None):
    print(f"Searching eBay Browse: {search}")
    listings = search_listings(search)
    print(f"  Found {len(listings)} listings")
    upsert_price_history(item_id, variant_id, listings)


if __name__ == "__main__":
    # Fetch all non-trading-card items and search eBay for each
    items = supabase.table("items")\
        .select("id, name, brand, metadata, categories(slug), item_variants(id, variant_type, variant_value, grader)")\
        .execute().data

    for item in items:
        category = item.get("categories", {})
        slug = category.get("slug") if isinstance(category, dict) else None

        # Skip Pokemon/trading cards — handled by Pokemon TCG API
        if slug == "trading-cards":
            continue

        name = item["name"]
        variants = item.get("item_variants", [])
        metadata = item.get("metadata", {}) or {}

        if variants:
            for v in variants:
                label = f"{v['grader']} {v['variant_value']}" if v["grader"] else v["variant_value"]
                # Build a targeted search for this variant
                if slug == "sneakers":
                    search = f"{name} {label}"
                elif slug == "video-games":
                    platform = metadata.get("platform", "")
                    search = f"{name} {platform} {label}".strip()
                elif slug == "comics":
                    search = f"{name} {label} comic"
                else:
                    search = f"{name} {label}"

                run(search=search, item_id=item["id"], variant_id=v["id"])
        else:
            run(search=name, item_id=item["id"])
