import os
import ssl
import time
import urllib3
import requests

ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings()

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.environ['SUPABASE_URL']
SUPABASE_SERVICE_KEY = os.environ['SUPABASE_SERVICE_KEY']
EBAY_APP_ID = os.environ['EBAY_APP_ID']
EBAY_CERT_ID = os.environ['EBAY_CERT_ID']

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

COMICS = [
    "Action Comics #1",
    "Detective Comics #27",
    "Amazing Fantasy #15",
    "Amazing Spider-Man #1 1963",
    "X-Men #1 1963",
    "Fantastic Four #1 1961",
    "Incredible Hulk #1 1962",
    "Tales of Suspense #39 Iron Man",
    "Captain America Comics #1 1941",
    "Batman #1 1940",
    "Superman #1 1939",
    "Avengers #1 1963",
    "New Mutants #98 Deadpool",
    "Giant-Size X-Men #1 1975",
    "Walking Dead #1 2003",
    "Spawn #1 1992",
    "Teenage Mutant Ninja Turtles #1 1984",
    "Justice League of America #1 1960",
    "Flash Comics #1 1940",
    "Wonder Woman #1 1942",
    "Green Lantern #76 1970",
    "Uncanny X-Men #94 1975",
    "Iron Fist #14 Spider-Man",
    "Tomb of Dracula #10 Blade",
    "Amazing Spider-Man #300 Venom",
]

COMIC_VARIANTS = ["Raw", "CGC 9.8", "CGC 9.6", "CGC 9.4", "CGC 8.0"]

EBAY_TOKEN_URL = 'https://api.ebay.com/identity/v1/oauth2/token'
EBAY_BROWSE_URL = 'https://api.ebay.com/buy/browse/v1/item_summary/search'

def get_ebay_token():
    r = requests.post(
        EBAY_TOKEN_URL,
        auth=(EBAY_APP_ID, EBAY_CERT_ID),
        data={'grant_type': 'client_credentials', 'scope': 'https://api.ebay.com/oauth/api_scope'},
        verify=False,
    )
    return r.json().get('access_token')

def search_ebay(token, query, limit=3):
    headers = {'Authorization': f'Bearer {token}', 'X-EBAY-C-MARKETPLACE-ID': 'EBAY_US'}
    params = {
        'q': query,
        'filter': 'buyingOptions:{FIXED_PRICE}',
        'limit': limit,
        'sort': 'price',
    }
    r = requests.get(EBAY_BROWSE_URL, headers=headers, params=params, verify=False)
    return r.json().get('itemSummaries', [])

def get_category_id():
    res = supabase.table('categories').select('id').eq('slug', 'comics').execute()
    return res.data[0]['id'] if res.data else None

def main():
    category_id = get_category_id()
    if not category_id:
        print("Comics category not found")
        return

    token = get_ebay_token()
    print(f"Got eBay token")

    for comic_name in COMICS:
        print(f"\nProcessing: {comic_name}")

        # Check if already exists
        existing = supabase.table('items').select('id').eq('name', comic_name).eq('category_id', category_id).execute()
        if existing.data:
            print(f"  Already exists, skipping")
            continue

        # Fetch eBay listing for image + price
        listings = search_ebay(token, f"{comic_name} comic", limit=3)
        image_url = None
        ebay_price = None

        for listing in listings:
            if listing.get('image', {}).get('imageUrl'):
                image_url = listing['image']['imageUrl']
            price = listing.get('price', {})
            if price.get('value'):
                ebay_price = float(price['value'])
                break

        # Insert item
        item_res = supabase.table('items').insert({
            'name': comic_name,
            'brand': None,
            'category_id': category_id,
            'image_url': image_url,
            'metadata': {'source': 'seed'},
        }).execute()

        if not item_res.data:
            print(f"  Failed to insert item")
            continue

        item_id = item_res.data[0]['id']
        print(f"  Inserted item {item_id}, image: {'yes' if image_url else 'no'}")

        # Insert variants
        for variant_value in COMIC_VARIANTS:
            grader = None
            if variant_value.startswith('CGC'):
                grader = 'CGC'
                grade = variant_value.split(' ')[1]
                variant_val = grade
            else:
                variant_val = variant_value

            variant_res = supabase.table('item_variants').insert({
                'item_id': item_id,
                'variant_type': 'grade',
                'variant_value': variant_val,
                'grader': grader,
            }).execute()

            if not variant_res.data:
                continue

            variant_id = variant_res.data[0]['id']

            # Add price data for Raw variant from eBay
            if variant_value == 'Raw' and ebay_price:
                supabase.table('price_history').insert({
                    'item_id': item_id,
                    'variant_id': variant_id,
                    'source': 'ebay_browse',
                    'source_listing_id': f"seed_{item_id}_{variant_value}",
                    'sold_price': ebay_price,
                    'sold_at': '2025-01-01T00:00:00Z',
                }).execute()

        print(f"  Done — {len(COMIC_VARIANTS)} variants, price: {'$' + str(ebay_price) if ebay_price else 'none'}")
        time.sleep(0.3)

    print("\nComics seed complete!")

if __name__ == '__main__':
    main()
