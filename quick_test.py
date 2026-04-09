"""Quick 5-second WebSocket test"""
import time
import sys
from realtime_client import KrakenWebSocketClient

print("Testing Kraken WebSocket (5 seconds)...")
print("=" * 60)

try:
    client = KrakenWebSocketClient(pair='ETH/USD')

    if client.start():
        print("✓ Connected!")
        time.sleep(5)

        price = client.get_current_price()
        if price:
            print(f"✓ Live Price: ${price:,.2f}")

        ticker = client.get_ticker()
        if ticker:
            print(f"✓ Bid/Ask: ${ticker['bid']:,.2f} / ${ticker['ask']:,.2f}")

        client.stop()
        print("✅ WebSocket working!")
    else:
        print("✗ Connection failed")
        sys.exit(1)

except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)
