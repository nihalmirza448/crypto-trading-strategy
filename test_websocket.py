"""
Quick test of WebSocket connection
"""
import time
from realtime_client import KrakenWebSocketClient

print("Testing Kraken WebSocket Connection...")
print("=" * 60)

# Create client
client = KrakenWebSocketClient(pair='ETH/USD')

# Start client
print("\nAttempting to connect...")
if client.start():
    print("\n✅ WebSocket connected successfully!")
    print("\nWaiting for data (10 seconds)...")
    time.sleep(10)

    # Check what data we received
    print("\n" + "=" * 60)
    print("DATA RECEIVED:")
    print("=" * 60)

    price = client.get_current_price()
    if price:
        print(f"✓ Current Price: ${price:,.2f}")
    else:
        print("✗ No price data yet")

    ticker = client.get_ticker()
    if ticker:
        print(f"✓ Ticker Data: Bid ${ticker['bid']:,.2f} | Ask ${ticker['ask']:,.2f}")
        print(f"  24h Volume: {ticker['volume_24h']:,.0f} ETH")
    else:
        print("✗ No ticker data yet")

    candle = client.get_current_ohlc()
    if candle:
        print(f"✓ Current Candle: O:{candle['open']:.2f} H:{candle['high']:.2f} L:{candle['low']:.2f} C:{candle['close']:.2f}")
    else:
        print("✗ No OHLC data yet")

    trades = client.get_recent_trades(count=3)
    if trades:
        print(f"✓ Recent Trades: {len(trades)} trades received")
        for trade in trades[:3]:
            side = "BUY" if trade['side'] == 'b' else "SELL"
            print(f"  {side} {trade['volume']:.4f} ETH @ ${trade['price']:,.2f}")
    else:
        print("✗ No trade data yet")

    order_book = client.get_order_book(depth=3)
    if order_book['bids'] or order_book['asks']:
        print(f"✓ Order Book:")
        if order_book['bids']:
            print(f"  Best Bid: ${order_book['bids'][0][0]:,.2f} ({order_book['bids'][0][1]:.4f} ETH)")
        if order_book['asks']:
            print(f"  Best Ask: ${order_book['asks'][0][0]:,.2f} ({order_book['asks'][0][1]:.4f} ETH)")
    else:
        print("✗ No order book data yet")

    print("\n" + "=" * 60)
    print("✅ WebSocket test successful!")
    print("=" * 60)

    # Stop client
    client.stop()
else:
    print("\n✗ Failed to connect to WebSocket")

print("\nTest complete.")
