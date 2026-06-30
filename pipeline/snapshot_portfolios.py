import os
import ssl
import urllib3
from datetime import datetime, timezone

ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings()

from supabase import create_client

SUPABASE_URL = os.environ['SUPABASE_URL']
SUPABASE_SERVICE_KEY = os.environ['SUPABASE_SERVICE_KEY']

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def main():
    portfolio_res = supabase.table('portfolio_items').select('user_id, item_id, variant_id, quantity').execute()

    user_portfolios: dict = {}
    for row in portfolio_res.data:
        uid = row['user_id']
        if uid not in user_portfolios:
            user_portfolios[uid] = []
        user_portfolios[uid].append(row)

    now = datetime.now(timezone.utc)
    snapshot_at = now.replace(minute=0, second=0, microsecond=0).isoformat()

    print(f"Snapshotting portfolios for {len(user_portfolios)} user(s) at {snapshot_at}...")

    for user_id, items in user_portfolios.items():
        total_value = 0.0

        for item in items:
            q = supabase.table('current_prices').select('est_value').eq('item_id', item['item_id'])
            if item['variant_id']:
                q = q.eq('variant_id', item['variant_id'])
            price_res = q.execute()

            if price_res.data:
                price = float(price_res.data[0]['est_value'])
                total_value += price * (item['quantity'] or 1)

        supabase.table('portfolio_snapshots').upsert(
            {'user_id': user_id, 'total_value': round(total_value, 2), 'snapshot_at': snapshot_at},
            on_conflict='user_id,snapshot_at'
        ).execute()

        print(f"  {user_id[:8]}... → ${total_value:,.2f}")

    print(f"Done — {len(user_portfolios)} snapshot(s) saved.")

if __name__ == '__main__':
    main()
