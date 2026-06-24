"""
Curated seed list for sneakers and sports cards.
Creates items + variants, then pulls eBay Browse prices for each.
"""
import os
import ssl
import base64
import requests
import urllib3
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings()
load_dotenv()

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

EBAY_APP_ID = os.getenv("EBAY_APP_ID")
EBAY_CERT_ID = os.getenv("EBAY_CERT_ID")
BROWSE_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"
OAUTH_URL = "https://api.ebay.com/identity/v1/oauth2/token"

_token_cache = {"token": None}

# ---------------------------------------------------------------------------
# Curated item lists
# ---------------------------------------------------------------------------

SNEAKERS = [
    {"name": "Nike Air Jordan 1 Retro High OG Chicago 1985", "brand": "Nike", "search": "Jordan 1 Retro High OG Chicago 1985", "colorway": "White/Black-Varsity Red"},
    {"name": "Nike Air Jordan 1 Retro High OG Bred Toe", "brand": "Nike", "search": "Jordan 1 Retro High Bred Toe", "colorway": "Black/Gym Red-White"},
    {"name": "Nike Air Jordan 1 Retro High Off-White Chicago", "brand": "Nike", "search": "Jordan 1 Retro High Off-White Chicago", "colorway": "White/University Red"},
    {"name": "Nike Air Jordan 1 Retro High Shattered Backboard", "brand": "Nike", "search": "Jordan 1 Retro High Shattered Backboard", "colorway": "Starfish/Black-Sail"},
    {"name": "Nike Air Jordan 1 Low Travis Scott Fragment", "brand": "Nike", "search": "Jordan 1 Low Travis Scott Fragment", "colorway": "Military Blue/Black-White"},
    {"name": "Nike Air Jordan 3 Retro White Cement", "brand": "Nike", "search": "Jordan 3 Retro White Cement", "colorway": "White/Fire Red-Cement Grey"},
    {"name": "Nike Air Jordan 4 Retro Off-White Sail", "brand": "Nike", "search": "Jordan 4 Retro Off-White Sail", "colorway": "Sail/Black-Muslin"},
    {"name": "Nike Air Jordan 11 Retro Space Jam 2016", "brand": "Nike", "search": "Jordan 11 Retro Space Jam 2016", "colorway": "Black/Concord-White"},
    {"name": "Nike Air Jordan 6 Retro Carmine 2021", "brand": "Nike", "search": "Jordan 6 Retro Carmine 2021", "colorway": "White/Carmine-Black"},
    {"name": "Nike Dunk Low Retro Panda", "brand": "Nike", "search": "Nike Dunk Low Panda White Black", "colorway": "White/Black"},
    {"name": "Nike SB Dunk Low Pro Pigeon", "brand": "Nike", "search": "Nike SB Dunk Low Pigeon NYC", "colorway": "Neutral Grey/Neutral Grey"},
    {"name": "Nike SB Dunk Low Diamond Supply Tiffany", "brand": "Nike", "search": "Nike SB Dunk Low Diamond Tiffany", "colorway": "Turquoise/Black"},
    {"name": "Nike Air Force 1 Low Travis Scott Cactus Jack", "brand": "Nike", "search": "Air Force 1 Travis Scott Cactus Jack", "colorway": "Sail/Sail"},
    {"name": "Nike Air Max 1 Lucky Green", "brand": "Nike", "search": "Nike Air Max 1 Lucky Green", "colorway": "White/Lucky Green"},
    {"name": "Adidas Yeezy Boost 350 V2 Zebra", "brand": "Adidas", "search": "Yeezy Boost 350 V2 Zebra", "colorway": "White/Core Black/Red"},
    {"name": "Adidas Yeezy Boost 350 V2 Bred", "brand": "Adidas", "search": "Yeezy Boost 350 V2 Bred Black Red", "colorway": "Core Black/Red"},
    {"name": "Adidas Yeezy Boost 700 Wave Runner", "brand": "Adidas", "search": "Yeezy 700 Wave Runner", "colorway": "Solid Grey/Chalk White/Dark Grey"},
    {"name": "Adidas Yeezy Boost 350 V2 Beluga 2.0", "brand": "Adidas", "search": "Yeezy 350 V2 Beluga 2.0", "colorway": "Bold Orange/Grey"},
    {"name": "New Balance 550 White Green", "brand": "New Balance", "search": "New Balance 550 White Green", "colorway": "White/Green"},
    {"name": "Nike Air Jordan 1 Retro High Royal Toe", "brand": "Nike", "search": "Jordan 1 Retro High Royal Toe", "colorway": "Black/White-Varsity Royal"},
]

SPORTS_CARDS = [
    {"name": "1952 Topps Mickey Mantle #311", "brand": "Topps", "sport": "Baseball", "year": 1952, "search": "1952 Topps Mickey Mantle 311"},
    {"name": "1986-87 Fleer Michael Jordan Rookie #57", "brand": "Fleer", "sport": "Basketball", "year": 1986, "search": "1986 Fleer Michael Jordan Rookie 57"},
    {"name": "1986-87 Fleer Michael Jordan Sticker #8", "brand": "Fleer", "sport": "Basketball", "year": 1986, "search": "1986 Fleer Michael Jordan Sticker 8"},
    {"name": "2003-04 Upper Deck Exquisite LeBron James Rookie Patch Auto #78", "brand": "Upper Deck", "sport": "Basketball", "year": 2003, "search": "2003 Upper Deck Exquisite LeBron James Rookie Patch Auto"},
    {"name": "1979-80 Topps Wayne Gretzky Rookie #18", "brand": "Topps", "sport": "Hockey", "year": 1979, "search": "1979 Topps Wayne Gretzky Rookie 18"},
    {"name": "2011 Topps Update Mike Trout Rookie #US175", "brand": "Topps", "sport": "Baseball", "year": 2011, "search": "2011 Topps Update Mike Trout Rookie US175"},
    {"name": "2009 Bowman Chrome Mike Trout Draft Auto", "brand": "Bowman", "sport": "Baseball", "year": 2009, "search": "2009 Bowman Chrome Mike Trout Draft Auto"},
    {"name": "2000 Topps Chrome Tom Brady Rookie #144", "brand": "Topps", "sport": "Football", "year": 2000, "search": "2000 Topps Chrome Tom Brady Rookie 144"},
    {"name": "2018 Panini National Treasures Patrick Mahomes Rookie Patch Auto", "brand": "Panini", "sport": "Football", "year": 2018, "search": "2018 National Treasures Patrick Mahomes Rookie Patch Auto"},
    {"name": "2018 Topps Update Shohei Ohtani Rookie #US1", "brand": "Topps", "sport": "Baseball", "year": 2018, "search": "2018 Topps Update Shohei Ohtani Rookie US1"},
    {"name": "1951 Bowman Willie Mays Rookie #305", "brand": "Bowman", "sport": "Baseball", "year": 1951, "search": "1951 Bowman Willie Mays Rookie 305"},
    {"name": "1989 Upper Deck Ken Griffey Jr. Rookie #1", "brand": "Upper Deck", "sport": "Baseball", "year": 1989, "search": "1989 Upper Deck Ken Griffey Jr Rookie 1"},
    {"name": "2017 Panini Prizm Luka Doncic Rookie #280", "brand": "Panini", "sport": "Basketball", "year": 2017, "search": "2017 Panini Prizm Luka Doncic Rookie"},
    {"name": "2019 Panini Prizm Ja Morant Rookie #249", "brand": "Panini", "sport": "Basketball", "year": 2019, "search": "2019 Panini Prizm Ja Morant Rookie"},
    {"name": "1955 Topps Sandy Koufax Rookie #123", "brand": "Topps", "sport": "Baseball", "year": 1955, "search": "1955 Topps Sandy Koufax Rookie 123"},
    {"name": "2020 Topps Chrome Fernando Tatis Jr. Rookie Auto", "brand": "Topps", "sport": "Baseball", "year": 2020, "search": "2020 Topps Chrome Fernando Tatis Jr Rookie Auto"},
    {"name": "1969 Topps Reggie Jackson Rookie #260", "brand": "Topps", "sport": "Baseball", "year": 1969, "search": "1969 Topps Reggie Jackson Rookie 260"},
    {"name": "2018 Panini Prizm Trae Young Rookie #78", "brand": "Panini", "sport": "Basketball", "year": 2018, "search": "2018 Panini Prizm Trae Young Rookie"},
    {"name": "2003-04 Topps Chrome LeBron James Rookie #111", "brand": "Topps", "sport": "Basketball", "year": 2003, "search": "2003 Topps Chrome LeBron James Rookie 111"},
    {"name": "1996-97 Topps Chrome Kobe Bryant Rookie #138", "brand": "Topps", "sport": "Basketball", "year": 1996, "search": "1996 Topps Chrome Kobe Bryant Rookie 138"},
]

SNEAKER_VARIANTS = ["Deadstock", "Near Deadstock", "Used"]
CARD_VARIANTS = ["Raw", "PSA 9", "PSA 10", "BGS 9.5"]
GAME_VARIANTS = ["Loose", "CIB", "Sealed"]
FIGURE_VARIANTS = ["Mint in Box", "Opened"]

VIDEO_GAMES = [
    {"name": "Pokemon Red Version Game Boy", "brand": "Nintendo", "platform": "Game Boy", "search": "Pokemon Red Version Game Boy sealed"},
    {"name": "Pokemon Blue Version Game Boy", "brand": "Nintendo", "platform": "Game Boy", "search": "Pokemon Blue Version Game Boy sealed"},
    {"name": "Pokemon Gold Version Game Boy Color", "brand": "Nintendo", "platform": "Game Boy Color", "search": "Pokemon Gold Version Game Boy Color sealed"},
    {"name": "Super Mario Bros NES", "brand": "Nintendo", "platform": "NES", "search": "Super Mario Bros NES sealed"},
    {"name": "The Legend of Zelda NES", "brand": "Nintendo", "platform": "NES", "search": "Legend of Zelda NES sealed"},
    {"name": "Super Mario World SNES", "brand": "Nintendo", "platform": "SNES", "search": "Super Mario World SNES sealed"},
    {"name": "Super Mario 64 Nintendo 64", "brand": "Nintendo", "platform": "Nintendo 64", "search": "Super Mario 64 N64 sealed"},
    {"name": "The Legend of Zelda Ocarina of Time Nintendo 64", "brand": "Nintendo", "platform": "Nintendo 64", "search": "Zelda Ocarina of Time N64 sealed"},
    {"name": "GoldenEye 007 Nintendo 64", "brand": "Nintendo", "platform": "Nintendo 64", "search": "GoldenEye 007 N64 sealed"},
    {"name": "Pokemon Diamond Version Nintendo DS", "brand": "Nintendo", "platform": "Nintendo DS", "search": "Pokemon Diamond Version DS sealed"},
    {"name": "Earthbound SNES", "brand": "Nintendo", "platform": "SNES", "search": "Earthbound SNES sealed"},
    {"name": "Chrono Trigger SNES", "brand": "Square", "platform": "SNES", "search": "Chrono Trigger SNES sealed"},
    {"name": "Final Fantasy VII PlayStation", "brand": "Square", "platform": "PlayStation", "search": "Final Fantasy VII PS1 sealed"},
    {"name": "Metal Gear Solid PlayStation", "brand": "Konami", "platform": "PlayStation", "search": "Metal Gear Solid PS1 sealed"},
    {"name": "Conker's Bad Fur Day Nintendo 64", "brand": "Rare", "platform": "Nintendo 64", "search": "Conker's Bad Fur Day N64 sealed"},
    {"name": "Castlevania Symphony of the Night PlayStation", "brand": "Konami", "platform": "PlayStation", "search": "Castlevania Symphony of the Night PS1 sealed"},
    {"name": "Super Smash Bros Melee GameCube", "brand": "Nintendo", "platform": "GameCube", "search": "Super Smash Bros Melee GameCube sealed"},
    {"name": "Halo Combat Evolved Xbox", "brand": "Microsoft", "platform": "Xbox", "search": "Halo Combat Evolved Xbox sealed"},
    {"name": "The Legend of Zelda Majora's Mask Nintendo 64", "brand": "Nintendo", "platform": "Nintendo 64", "search": "Zelda Majora's Mask N64 sealed"},
    {"name": "Sonic the Hedgehog Sega Genesis", "brand": "Sega", "platform": "Sega Genesis", "search": "Sonic the Hedgehog Sega Genesis sealed"},
]

FIGURES = [
    {"name": "Hot Toys Iron Man Mark III MMS256", "brand": "Hot Toys", "search": "Hot Toys Iron Man Mark III MMS256"},
    {"name": "Hot Toys Batman The Dark Knight MMS236", "brand": "Hot Toys", "search": "Hot Toys Batman Dark Knight MMS236"},
    {"name": "Hot Toys Darth Vader Star Wars MMS452", "brand": "Hot Toys", "search": "Hot Toys Darth Vader Star Wars MMS452"},
    {"name": "Hot Toys Spider-Man No Way Home MMS624", "brand": "Hot Toys", "search": "Hot Toys Spider-Man No Way Home MMS624"},
    {"name": "Funko Pop Stan Lee Metallic #14 Vaulted", "brand": "Funko", "search": "Funko Pop Stan Lee Metallic 14 vaulted"},
    {"name": "Funko Pop Alien #14 Vaulted", "brand": "Funko", "search": "Funko Pop Alien 14 vaulted"},
    {"name": "Funko Pop Freddy Funko Clown #02", "brand": "Funko", "search": "Funko Pop Freddy Funko Clown 02"},
    {"name": "LEGO Star Wars Millennium Falcon 75192", "brand": "LEGO", "search": "LEGO Millennium Falcon 75192 sealed"},
    {"name": "LEGO Star Wars Death Star 10188", "brand": "LEGO", "search": "LEGO Death Star 10188 retired sealed"},
    {"name": "LEGO Creator Eiffel Tower 10307", "brand": "LEGO", "search": "LEGO Eiffel Tower 10307 sealed"},
    {"name": "Bearbrick Kaws Companion 1000%", "brand": "Medicom", "search": "Bearbrick Kaws Companion 1000%"},
    {"name": "Bearbrick Daft Punk 1000%", "brand": "Medicom", "search": "Bearbrick Daft Punk 1000%"},
    {"name": "Sideshow Collectibles Wolverine Premium Format", "brand": "Sideshow", "search": "Sideshow Wolverine Premium Format statue"},
    {"name": "MAFEX Batman Hush Version No.105", "brand": "Medicom", "search": "MAFEX Batman Hush 105"},
    {"name": "S.H. Figuarts Dragon Ball Z Son Goku", "brand": "Bandai", "search": "SH Figuarts Dragon Ball Son Goku"},
]

# ---------------------------------------------------------------------------
# eBay helpers
# ---------------------------------------------------------------------------

def get_token() -> str:
    if _token_cache["token"]:
        return _token_cache["token"]
    creds = base64.b64encode(f"{EBAY_APP_ID}:{EBAY_CERT_ID}".encode()).decode()
    res = requests.post(OAUTH_URL, headers={"Authorization": f"Basic {creds}", "Content-Type": "application/x-www-form-urlencoded"},
                        data={"grant_type": "client_credentials", "scope": "https://api.ebay.com/oauth/api_scope"}, verify=False)
    res.raise_for_status()
    _token_cache["token"] = res.json()["access_token"]
    return _token_cache["token"]


def ebay_search(keywords: str, limit: int = 20) -> list[dict]:
    try:
        res = requests.get(BROWSE_URL, headers={"Authorization": f"Bearer {get_token()}", "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"},
                           params={"q": keywords, "filter": "buyingOptions:{FIXED_PRICE}", "sort": "price", "limit": limit}, verify=False)
        res.raise_for_status()
        return res.json().get("itemSummaries", [])
    except Exception as e:
        print(f"    eBay error: {e}")
        return []


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def get_category_id(slug: str) -> str:
    res = supabase.table("categories").select("id").eq("slug", slug).single().execute()
    return res.data["id"]


def item_exists(name: str) -> bool:
    res = supabase.table("items").select("id").eq("name", name).execute()
    return len(res.data) > 0


def insert_item(name: str, brand: str, category_id: str, metadata: dict) -> str:
    res = supabase.table("items").insert({"name": name, "brand": brand, "category_id": category_id, "metadata": metadata}).execute()
    return res.data[0]["id"]


def insert_variants(item_id: str, variants: list[str]) -> dict[str, str]:
    rows = []
    for v in variants:
        parts = v.split(" ", 1)
        grader = parts[0] if parts[0] in ("PSA", "BGS", "CGC", "SGC") else None
        value = parts[1] if grader else v
        rows.append({"item_id": item_id, "variant_type": "grade" if grader else "condition", "variant_value": value, "grader": grader})
    res = supabase.table("item_variants").insert(rows).execute()
    return {v["variant_value"] if not v["grader"] else f"{v['grader']} {v['variant_value']}": v["id"] for v in res.data}


def insert_prices(item_id: str, variant_id: str, listings: list[dict]):
    rows = []
    for l in listings:
        try:
            rows.append({
                "item_id": item_id,
                "variant_id": variant_id,
                "source": "ebay_browse",
                "source_listing_id": l["itemId"],
                "sold_price": float(l["price"]["value"]),
                "currency": l["price"]["currency"],
                "sold_at": datetime.utcnow().isoformat(),
                "image_url": (l.get("image") or {}).get("imageUrl"),
            })
        except (KeyError, ValueError):
            continue
    if rows:
        supabase.table("price_history").upsert(rows, on_conflict="source,source_listing_id").execute()
    return rows


def update_item_image(item_id: str, image_url: str):
    supabase.table("items").update({"image_url": image_url}).eq("id", item_id).execute()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run():
    sneaker_cat = get_category_id("sneakers")
    card_cat = get_category_id("trading-cards")

    # --- Sneakers ---
    print("\n=== SNEAKERS ===")
    for s in SNEAKERS:
        if item_exists(s["name"]):
            print(f"  skip: {s['name']}")
            continue

        item_id = insert_item(s["name"], s["brand"], sneaker_cat, {"colorway": s["colorway"]})
        variant_map = insert_variants(item_id, SNEAKER_VARIANTS)

        # Use Deadstock variant for eBay pricing (closest to collectible value)
        ds_id = variant_map.get("Deadstock")
        listings = ebay_search(s["search"])
        rows = insert_prices(item_id, ds_id, listings)

        # Grab image from first eBay listing
        image_url = next((r["image_url"] for r in rows if r.get("image_url")), None)
        if image_url:
            update_item_image(item_id, image_url)

        print(f"  ✓ {s['name']} — {len(listings)} listings")

    # --- Sports Cards ---
    print("\n=== SPORTS CARDS ===")
    for c in SPORTS_CARDS:
        if item_exists(c["name"]):
            print(f"  skip: {c['name']}")
            continue

        item_id = insert_item(c["name"], c["brand"], card_cat, {"sport": c["sport"], "year": c["year"]})
        variant_map = insert_variants(item_id, CARD_VARIANTS)

        raw_id = variant_map.get("Raw")
        listings = ebay_search(c["search"])
        rows = insert_prices(item_id, raw_id, listings)

        image_url = next((r["image_url"] for r in rows if r.get("image_url")), None)
        if image_url:
            update_item_image(item_id, image_url)

        print(f"  ✓ {c['name']} — {len(listings)} listings")

    # --- Video Games ---
    print("\n=== VIDEO GAMES ===")
    game_cat = get_category_id("video-games")
    for g in VIDEO_GAMES:
        if item_exists(g["name"]):
            print(f"  skip: {g['name']}")
            continue

        item_id = insert_item(g["name"], g["brand"], game_cat, {"platform": g["platform"]})
        variant_map = insert_variants(item_id, GAME_VARIANTS)

        sealed_id = variant_map.get("Sealed")
        listings = ebay_search(g["search"])
        rows = insert_prices(item_id, sealed_id, listings)

        image_url = next((r["image_url"] for r in rows if r.get("image_url")), None)
        if image_url:
            update_item_image(item_id, image_url)

        print(f"  ✓ {g['name']} — {len(listings)} listings")

    # --- Figures & Toys ---
    print("\n=== FIGURES & TOYS ===")
    figure_cat = get_category_id("figures-toys")
    for f in FIGURES:
        if item_exists(f["name"]):
            print(f"  skip: {f['name']}")
            continue

        item_id = insert_item(f["name"], f["brand"], figure_cat, {})
        variant_map = insert_variants(item_id, FIGURE_VARIANTS)

        mib_id = variant_map.get("Mint in Box")
        listings = ebay_search(f["search"])
        rows = insert_prices(item_id, mib_id, listings)

        image_url = next((r["image_url"] for r in rows if r.get("image_url")), None)
        if image_url:
            update_item_image(item_id, image_url)

        print(f"  ✓ {f['name']} — {len(listings)} listings")

    print("\nDone!")


if __name__ == "__main__":
    run()
