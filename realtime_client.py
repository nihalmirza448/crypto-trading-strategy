"""
Real-Time WebSocket Client for Kraken
Streams live market data including price, OHLC candles, trades, and order book
"""
import websocket
import json
import threading
import time
from datetime import datetime
import pandas as pd
from collections import deque
import config

class KrakenWebSocketClient:
    """
    Real-time WebSocket client for Kraken exchange

    Features:
    - Live ticker data (current price, bid/ask, volume)
    - Real-time OHLC candles as they form
    - Live trades stream
    - Order book snapshots
    - Automatic reconnection
    - Thread-safe data access
    """

    def __init__(self, pair='ETH/USD'):
        self.ws_url = config.KRAKEN_WS_URL
        self.pair = pair
        self.ws = None
        self.running = False
        self.reconnect_delay = 5

        # Data storage
        self.current_price = None
        self.current_ticker = {}
        self.current_ohlc = {}
        self.recent_trades = deque(maxlen=100)
        self.order_book = {'bids': [], 'asks': []}

        # Callbacks for custom handling
        self.on_ticker_callback = None
        self.on_ohlc_callback = None
        self.on_trade_callback = None

        # Thread safety
        self.lock = threading.Lock()

        # Connection status
        self.connected = False
        self.last_heartbeat = time.time()

    def on_message(self, ws, message):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(message)

            # Skip system messages
            if isinstance(data, dict):
                if 'event' in data:
                    self._handle_event(data)
                return

            # Handle data messages (array format)
            if isinstance(data, list) and len(data) >= 2:
                channel_name = data[-2] if len(data) >= 3 else None
                channel_data = data[1]

                if 'ticker' in str(channel_name):
                    self._handle_ticker(channel_data)
                elif 'ohlc' in str(channel_name):
                    self._handle_ohlc(channel_data)
                elif 'trade' in str(channel_name):
                    self._handle_trade(channel_data)
                elif 'book' in str(channel_name):
                    self._handle_order_book(channel_data)

        except Exception as e:
            print(f"Error processing message: {e}")

    def _handle_event(self, data):
        """Handle system events"""
        event = data.get('event')

        if event == 'heartbeat':
            self.last_heartbeat = time.time()
        elif event == 'systemStatus':
            status = data.get('status')
            print(f"System status: {status}")
        elif event == 'subscriptionStatus':
            status = data.get('status')
            channel = data.get('channelName')
            pair = data.get('pair')
            if status == 'subscribed':
                print(f"✓ Subscribed to {channel} for {pair}")
            elif status == 'error':
                print(f"✗ Subscription error: {data.get('errorMessage')}")

    def _handle_ticker(self, data):
        """Handle ticker updates"""
        with self.lock:
            try:
                # Kraken ticker format:
                # {'a': [ask_price, whole_lot_volume, lot_volume],
                #  'b': [bid_price, whole_lot_volume, lot_volume],
                #  'c': [last_price, lot_volume],
                #  'v': [volume_today, volume_24h],
                #  'p': [vwap_today, vwap_24h],
                #  't': [trades_today, trades_24h],
                #  'l': [low_today, low_24h],
                #  'h': [high_today, high_24h],
                #  'o': [open_today, open_24h]}

                self.current_ticker = {
                    'timestamp': datetime.now(),
                    'ask': float(data['a'][0]),
                    'bid': float(data['b'][0]),
                    'last': float(data['c'][0]),
                    'volume_24h': float(data['v'][1]),
                    'vwap_24h': float(data['p'][1]),
                    'trades_24h': int(data['t'][1]),
                    'low_24h': float(data['l'][1]),
                    'high_24h': float(data['h'][1]),
                    'open_today': float(data['o'][0]),
                    'spread': float(data['a'][0]) - float(data['b'][0]),
                    'spread_pct': ((float(data['a'][0]) - float(data['b'][0])) / float(data['b'][0])) * 100
                }

                self.current_price = self.current_ticker['last']

                # Custom callback
                if self.on_ticker_callback:
                    self.on_ticker_callback(self.current_ticker)

            except Exception as e:
                print(f"Error handling ticker: {e}")

    def _handle_ohlc(self, data):
        """Handle OHLC candle updates"""
        with self.lock:
            try:
                # Kraken OHLC format:
                # [time, etime, open, high, low, close, vwap, volume, count]
                self.current_ohlc = {
                    'timestamp': datetime.fromtimestamp(float(data[0])),
                    'end_time': datetime.fromtimestamp(float(data[1])),
                    'open': float(data[2]),
                    'high': float(data[3]),
                    'low': float(data[4]),
                    'close': float(data[5]),
                    'vwap': float(data[6]),
                    'volume': float(data[7]),
                    'count': int(data[8])
                }

                # Update current price from candle
                self.current_price = self.current_ohlc['close']

                # Custom callback
                if self.on_ohlc_callback:
                    self.on_ohlc_callback(self.current_ohlc)

            except Exception as e:
                print(f"Error handling OHLC: {e}")

    def _handle_trade(self, data):
        """Handle trade updates"""
        with self.lock:
            try:
                # Kraken trade format: array of [price, volume, time, side, orderType, misc]
                for trade in data:
                    trade_data = {
                        'timestamp': datetime.fromtimestamp(float(trade[2])),
                        'price': float(trade[0]),
                        'volume': float(trade[1]),
                        'side': trade[3],  # 'b' for buy, 's' for sell
                        'order_type': trade[4]  # 'm' for market, 'l' for limit
                    }
                    self.recent_trades.append(trade_data)

                    # Custom callback
                    if self.on_trade_callback:
                        self.on_trade_callback(trade_data)

            except Exception as e:
                print(f"Error handling trade: {e}")

    def _handle_order_book(self, data):
        """Handle order book updates"""
        with self.lock:
            try:
                # Order book can be snapshot or update
                if 'as' in data and 'bs' in data:
                    # Snapshot
                    self.order_book['asks'] = [[float(x[0]), float(x[1])] for x in data['as']]
                    self.order_book['bids'] = [[float(x[0]), float(x[1])] for x in data['bs']]
                else:
                    # Update (a=asks, b=bids)
                    if 'a' in data:
                        for ask in data['a']:
                            price, volume = float(ask[0]), float(ask[1])
                            # Update or remove
                            self.order_book['asks'] = [x for x in self.order_book['asks'] if x[0] != price]
                            if volume > 0:
                                self.order_book['asks'].append([price, volume])
                    if 'b' in data:
                        for bid in data['b']:
                            price, volume = float(bid[0]), float(bid[1])
                            self.order_book['bids'] = [x for x in self.order_book['bids'] if x[0] != price]
                            if volume > 0:
                                self.order_book['bids'].append([price, volume])

                    # Sort
                    self.order_book['asks'].sort(key=lambda x: x[0])
                    self.order_book['bids'].sort(key=lambda x: x[0], reverse=True)

            except Exception as e:
                print(f"Error handling order book: {e}")

    def on_error(self, ws, error):
        """Handle WebSocket errors"""
        print(f"WebSocket error: {error}")
        self.connected = False

    def on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket connection close"""
        print(f"WebSocket connection closed: {close_status_code} - {close_msg}")
        self.connected = False

        if self.running:
            print(f"Reconnecting in {self.reconnect_delay} seconds...")
            time.sleep(self.reconnect_delay)
            self._connect()

    def on_open(self, ws):
        """Handle WebSocket connection open"""
        print(f"✓ WebSocket connected to {self.ws_url}")
        self.connected = True

        # Subscribe to channels
        self._subscribe_ticker()
        self._subscribe_ohlc()
        self._subscribe_trades()
        self._subscribe_order_book()

    def _subscribe_ticker(self):
        """Subscribe to ticker channel"""
        subscription = {
            "event": "subscribe",
            "pair": [self._format_pair(self.pair)],
            "subscription": {"name": "ticker"}
        }
        self.ws.send(json.dumps(subscription))

    def _subscribe_ohlc(self, interval=240):
        """Subscribe to OHLC channel (default: 240 minutes = 4 hours)"""
        subscription = {
            "event": "subscribe",
            "pair": [self._format_pair(self.pair)],
            "subscription": {"name": "ohlc", "interval": interval}
        }
        self.ws.send(json.dumps(subscription))

    def _subscribe_trades(self):
        """Subscribe to trades channel"""
        subscription = {
            "event": "subscribe",
            "pair": [self._format_pair(self.pair)],
            "subscription": {"name": "trade"}
        }
        self.ws.send(json.dumps(subscription))

    def _subscribe_order_book(self, depth=10):
        """Subscribe to order book channel"""
        subscription = {
            "event": "subscribe",
            "pair": [self._format_pair(self.pair)],
            "subscription": {"name": "book", "depth": depth}
        }
        self.ws.send(json.dumps(subscription))

    def _format_pair(self, pair):
        """Format pair for Kraken WebSocket API"""
        # Kraken WebSocket expects pairs with slashes: ETH/USD, BTC/USD, etc.
        # Ensure slash is present
        if '/' not in pair:
            # Try to add slash (e.g., ETHUSD -> ETH/USD)
            if 'ETH' in pair:
                pair = pair.replace('ETH', 'ETH/')
            elif 'BTC' in pair:
                pair = pair.replace('BTC', 'BTC/')
            elif 'XBT' in pair:
                pair = pair.replace('XBT', 'XBT/')

        # Kraken uses XBT instead of BTC for Bitcoin
        if 'BTC' in pair:
            pair = pair.replace('BTC', 'XBT')

        return pair

    def _connect(self):
        """Establish WebSocket connection"""
        websocket.enableTrace(False)
        self.ws = websocket.WebSocketApp(
            self.ws_url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open
        )

        # Run in separate thread
        ws_thread = threading.Thread(target=self.ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()

    def start(self):
        """Start the WebSocket client"""
        print(f"\n{'='*60}")
        print(f"Starting Real-Time WebSocket Client for {self.pair}")
        print(f"{'='*60}\n")

        self.running = True
        self._connect()

        # Wait for connection
        timeout = 10
        start_time = time.time()
        while not self.connected and time.time() - start_time < timeout:
            time.sleep(0.1)

        if not self.connected:
            print("Failed to connect to WebSocket")
            return False

        return True

    def stop(self):
        """Stop the WebSocket client"""
        print("\nStopping WebSocket client...")
        self.running = False
        if self.ws:
            self.ws.close()
        self.connected = False

    def get_current_price(self):
        """Get current market price"""
        with self.lock:
            return self.current_price

    def get_ticker(self):
        """Get current ticker data"""
        with self.lock:
            return self.current_ticker.copy() if self.current_ticker else None

    def get_current_ohlc(self):
        """Get current forming OHLC candle"""
        with self.lock:
            return self.current_ohlc.copy() if self.current_ohlc else None

    def get_recent_trades(self, count=10):
        """Get recent trades"""
        with self.lock:
            return list(self.recent_trades)[-count:]

    def get_order_book(self, depth=5):
        """Get order book snapshot"""
        with self.lock:
            return {
                'bids': self.order_book['bids'][:depth],
                'asks': self.order_book['asks'][:depth]
            }

    def get_market_summary(self):
        """Get complete market summary"""
        with self.lock:
            ticker = self.get_ticker()
            ohlc = self.get_current_ohlc()
            order_book = self.get_order_book(depth=5)

            summary = {
                'timestamp': datetime.now(),
                'connected': self.connected,
                'current_price': self.current_price,
                'ticker': ticker,
                'current_candle': ohlc,
                'order_book': order_book,
                'recent_trades_count': len(self.recent_trades)
            }

            return summary


def display_live_data(client, duration=60):
    """Display live market data for specified duration"""
    print(f"\n{'='*60}")
    print("LIVE MARKET DATA STREAM")
    print(f"{'='*60}\n")

    start_time = time.time()

    try:
        while time.time() - start_time < duration:
            # Get current data
            price = client.get_current_price()
            ticker = client.get_ticker()
            ohlc = client.get_current_ohlc()
            order_book = client.get_order_book(depth=3)

            # Clear screen (optional)
            # print('\033[2J\033[H')

            print(f"\r{datetime.now().strftime('%H:%M:%S')} | ", end='')

            if price:
                print(f"Price: ${price:,.2f} | ", end='')

            if ticker:
                print(f"Bid: ${ticker['bid']:,.2f} | Ask: ${ticker['ask']:,.2f} | ", end='')
                print(f"Vol: {ticker['volume_24h']:,.0f} | ", end='')

            if ohlc:
                print(f"Candle: O:{ohlc['open']:.2f} H:{ohlc['high']:.2f} L:{ohlc['low']:.2f} C:{ohlc['close']:.2f}", end='')

            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\nStopped by user")


def main():
    """Main function to demonstrate real-time client"""
    client = KrakenWebSocketClient(pair='ETH/USD')

    # Optional: Add custom callbacks
    def on_price_update(ticker):
        # Custom logic when price updates
        pass

    client.on_ticker_callback = on_price_update

    # Start client
    if client.start():
        print("\n✓ Real-time data streaming active!\n")

        # Display live data for 5 minutes
        try:
            display_live_data(client, duration=300)
        except KeyboardInterrupt:
            print("\n\nStopping...")
        finally:
            client.stop()
    else:
        print("Failed to start WebSocket client")


if __name__ == "__main__":
    main()
