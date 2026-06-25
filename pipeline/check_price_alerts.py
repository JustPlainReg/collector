import os
import ssl
import urllib3
import requests

ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings()

from supabase import create_client

SUPABASE_URL = os.environ['SUPABASE_URL']
SUPABASE_SERVICE_KEY = os.environ['SUPABASE_SERVICE_KEY']

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

EXPO_PUSH_URL = 'https://exp.host/--/exponent-push-notification-service'

def send_push(token: str, title: str, body: str, data: dict = {}):
    try:
        requests.post(
            EXPO_PUSH_URL,
            json={'to': token, 'title': title, 'body': body, 'data': data},
            headers={'Content-Type': 'application/json'},
            timeout=10,
            verify=False,
        )
    except Exception as e:
        print(f"  Push failed: {e}")

def main():
    alerts = supabase.table('price_alerts').select('*').eq('triggered', False).execute()
    print(f"Checking {len(alerts.data)} active alerts...")

    triggered_ids = []

    for alert in alerts.data:
        item_id = alert['item_id']
        variant_id = alert['variant_id']
        target = float(alert['target_price'])
        direction = alert['direction']

        # Get current price
        price_q = supabase.table('current_prices').select('est_value').eq('item_id', item_id)
        if variant_id:
            price_q = price_q.eq('variant_id', variant_id)
        price_res = price_q.execute()

        if not price_res.data:
            continue

        current = float(price_res.data[0]['est_value'])

        hit = (direction == 'above' and current >= target) or \
              (direction == 'below' and current <= target)

        if not hit:
            continue

        # Get push token
        token_res = supabase.table('push_tokens').select('token').eq('user_id', alert['user_id']).execute()
        if not token_res.data:
            print(f"  No push token for user {alert['user_id']}, skipping")
            continue

        push_token = token_res.data[0]['token']

        # Get item name
        item_res = supabase.table('items').select('name').eq('id', item_id).execute()
        item_name = item_res.data[0]['name'] if item_res.data else 'An item'

        direction_word = 'risen above' if direction == 'above' else 'dropped below'
        body = f"{item_name} has {direction_word} ${target:,.0f}. Now: ${current:,.0f}"

        print(f"  Triggering alert: {body}")
        send_push(push_token, title='Price Alert 🔔', body=body, data={'itemId': item_id})
        triggered_ids.append(alert['id'])

    if triggered_ids:
        supabase.table('price_alerts').update({'triggered': True}).in_('id', triggered_ids).execute()

    print(f"Done — {len(triggered_ids)} alert(s) triggered out of {len(alerts.data)} checked.")

if __name__ == '__main__':
    main()
