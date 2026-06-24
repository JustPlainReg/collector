import os
import ssl
import requests
import urllib3
from dotenv import load_dotenv
from supabase import create_client, Client

ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings()
load_dotenv()

supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY"),
)

POKEMON_TCG_API = "https://api.pokemontcg.io/v2/cards"


def fetch_pokemon_image(card_name: str) -> str | None:
    response = requests.get(POKEMON_TCG_API, params={"q": f'name:"{card_name}"', "pageSize": 1}, verify=False)
    if not response.ok:
        return None
    data = response.json().get("data", [])
    if not data:
        return None
    return data[0].get("images", {}).get("large")


def update_item_image(item_id: str, image_url: str):
    supabase.table("items").update({"image_url": image_url}).eq("id", item_id).execute()


def run():
    items = supabase.table("items")\
        .select("id, name, brand, categories(slug)")\
        .is_("image_url", None)\
        .execute().data

    for item in items:
        category = item.get("categories", {})
        slug = category.get("slug") if isinstance(category, dict) else None

        if slug != "trading-cards":
            continue

        name = item["name"]
        print(f"Searching: {name}")

        # Trim to just the Pokemon/card name for better API matches
        search_term = name.split(" 1st")[0].split(" Base")[0].split(" Neo")[0]\
                         .split(" Gold")[0].split(" Alpha")[0].strip()

        image_url = fetch_pokemon_image(search_term)
        if image_url:
            update_item_image(item["id"], image_url)
            print(f"  ✓ {search_term}")
        else:
            print(f"  ✗ No image found for {search_term}")


if __name__ == "__main__":
    run()
