# 🔴 Real-Time WebSocket Trading System

## 🚀 New Real-Time Capabilities

Your Ethereum swing trading system now has **live market data streaming** via Kraken WebSocket!

---

## 📡 What You Get

### **Real-Time Data Streams:**
- ✅ **Live Price Updates** - Current ETH price every second
- ✅ **Ticker Data** - Bid/Ask spread, volume, 24h stats
- ✅ **OHLC Candles** - Watch candles form in real-time (4-hour default)
- ✅ **Live Trades** - Real-time trade feed from Kraken
- ✅ **Order Book** - Level 2 market depth (bids/asks)
- ✅ **Continuous Analysis** - Market analysis updates every 60 seconds
- ✅ **Instant Alerts** - Get notified of significant changes immediately

---

## 🎯 Three Ways to Use Real-Time Data

### **1. Real-Time Monitor (Recommended)** 📊

Full dashboard with live analysis and alerts.

```bash
cd "/Users/nihal/cursor-projects/Ethereum swing trading"
source venv/bin/activate
python realtime_monitor.py
```

**What You See:**
```
================================================================================
                    REAL-TIME ETHEREUM MARKET MONITOR
================================================================================

2026-03-23 12:34:56 | 💰 $3,245.67 | Bid: $3,245.50 | Ask: $3,246.00 | Spread: $0.50 | 🟢 Candle: +2.3% | L2: $3,245.50/$3,246.00 | 🟢 ENTER LONG (85%)

================================================================================
📊 MARKET ANALYSIS UPDATE - 12:35:00
================================================================================

💰 Current Price: $3,245.67

🚀 Parabolic Bull Run: YES
   Confidence: 85%
   Criteria Met: 5/5
   Distance from 200 SMA: +25.3%

🟢 Recommendation: ENTER LONG
   Confidence: 85%
   Risk Level: MEDIUM

📊 Trading Levels:
   Entry Zone: $3,200.00 - $3,260.00
   Stop Loss: $3,100.00 (-4.5%)
   Take Profit: $3,400.00 (+4.8%)
   Risk/Reward: 1:2.1

🧠 Key Points:
   • Parabolic bull run detected (85% confidence)
   • Price +25.3% above 200 SMA
   • Strong momentum confirmed
   • High volume support
   • Multiple confirmations aligned
```

**Features:**
- Live price ticker in header
- Full market analysis every 60 seconds
- Automatic alerts on significant changes
- Shows parabolic status, recommendation, confidence
- Trading levels (entry, stop, target)

---

### **2. Basic WebSocket Client** 🔌

Just stream raw market data.

```bash
python realtime_client.py
```

**What You See:**
```
============================================================
Starting Real-Time WebSocket Client for ETH/USD
============================================================

✓ WebSocket connected to wss://ws.kraken.com
✓ Subscribed to ticker for ETHUSD
✓ Subscribed to ohlc for ETHUSD
✓ Subscribed to trade for ETHUSD
✓ Subscribed to book for ETHUSD

============================================================
LIVE MARKET DATA STREAM
============================================================

12:34:56 | Price: $3,245.67 | Bid: $3,245.50 | Ask: $3,246.00 | Vol: 125,456 | Candle: O:3240.00 H:3250.00 L:3235.00 C:3245.67
```

**Use Cases:**
- Quick price checks
- Testing WebSocket connection
- Raw data feed for custom integrations

---

### **3. Python API Integration** 💻

Use in your own scripts:

```python
from realtime_client import KrakenWebSocketClient

# Create client
client = KrakenWebSocketClient(pair='ETH/USD')

# Start streaming
client.start()

# Wait for data to flow
import time
time.sleep(2)

# Get current price
price = client.get_current_price()
print(f"Current ETH Price: ${price:,.2f}")

# Get full ticker
ticker = client.get_ticker()
print(f"Bid: ${ticker['bid']:,.2f}")
print(f"Ask: ${ticker['ask']:,.2f}")
print(f"24h Volume: {ticker['volume_24h']:,.0f} ETH")

# Get forming candle
candle = client.get_current_ohlc()
print(f"Current 4H Candle:")
print(f"  Open:  ${candle['open']:,.2f}")
print(f"  High:  ${candle['high']:,.2f}")
print(f"  Low:   ${candle['low']:,.2f}")
print(f"  Close: ${candle['close']:,.2f}")

# Get recent trades
trades = client.get_recent_trades(count=5)
for trade in trades:
    side = "BUY" if trade['side'] == 'b' else "SELL"
    print(f"{trade['timestamp']}: {side} {trade['volume']:.4f} ETH @ ${trade['price']:,.2f}")

# Get order book
order_book = client.get_order_book(depth=5)
print("\nTop 5 Bids:")
for price, volume in order_book['bids']:
    print(f"  ${price:,.2f} - {volume:.4f} ETH")
print("\nTop 5 Asks:")
for price, volume in order_book['asks']:
    print(f"  ${price:,.2f} - {volume:.4f} ETH")

# Stop when done
client.stop()
```

---

## ⚙️ Configuration Options

### **Change Analysis Interval:**

Edit `realtime_monitor.py`:
```python
# Analyze every 30 seconds (more frequent)
monitor = RealTimeMarketMonitor(pair='ETH/USD', analysis_interval=30)

# Analyze every 5 minutes (less frequent)
monitor = RealTimeMarketMonitor(pair='ETH/USD', analysis_interval=300)
```

### **Change OHLC Timeframe:**

Edit `realtime_client.py` line 174:
```python
# 1-hour candles
self._subscribe_ohlc(interval=60)

# 15-minute candles
self._subscribe_ohlc(interval=15)

# Daily candles
self._subscribe_ohlc(interval=1440)
```

### **Custom Alert Callbacks:**

```python
from realtime_monitor import RealTimeMarketMonitor

def my_alert_handler(alert, analysis):
    """Custom alert handler"""
    if alert['severity'] == 'CRITICAL':
        # Send Discord notification
        # Send email
        # Play sound
        print(f"🚨 CRITICAL: {alert['message']}")

    # Log to file
    with open('alerts.log', 'a') as f:
        f.write(f"{alert['timestamp']}: {alert['message']}\n")

monitor = RealTimeMarketMonitor(pair='ETH/USD', analysis_interval=60)
monitor.on_alert_callback = my_alert_handler
monitor.start()
```

---

## 📊 Available Data

### **1. Current Price**
```python
price = client.get_current_price()
# Returns: float (e.g., 3245.67)
```

### **2. Ticker Data**
```python
ticker = client.get_ticker()
# Returns: {
#     'timestamp': datetime,
#     'ask': float,
#     'bid': float,
#     'last': float,
#     'volume_24h': float,
#     'vwap_24h': float,
#     'trades_24h': int,
#     'low_24h': float,
#     'high_24h': float,
#     'open_today': float,
#     'spread': float,
#     'spread_pct': float
# }
```

### **3. Current OHLC Candle**
```python
candle = client.get_current_ohlc()
# Returns: {
#     'timestamp': datetime,
#     'end_time': datetime,
#     'open': float,
#     'high': float,
#     'low': float,
#     'close': float,
#     'vwap': float,
#     'volume': float,
#     'count': int
# }
```

### **4. Recent Trades**
```python
trades = client.get_recent_trades(count=10)
# Returns: list of {
#     'timestamp': datetime,
#     'price': float,
#     'volume': float,
#     'side': str,  # 'b' or 's'
#     'order_type': str  # 'm' or 'l'
# }
```

### **5. Order Book**
```python
book = client.get_order_book(depth=5)
# Returns: {
#     'bids': [[price, volume], ...],
#     'asks': [[price, volume], ...]
# }
```

### **6. Market Summary**
```python
summary = client.get_market_summary()
# Returns: everything above in one dict
```

---

## 🚨 Alert Types

The real-time monitor automatically triggers alerts for:

### **1. Recommendation Change** ⚠️ HIGH
```
Recommendation changed: WAIT → ENTER LONG
```

### **2. Parabolic Status Change** 🚨 CRITICAL
```
Market ENTERED parabolic bull run!
Market EXITED parabolic bull run!
```

### **3. Significant Price Move** 📊 MEDIUM
```
Significant price move: +3.5%
```

---

## 💡 Use Cases

### **Day Trading:**
```bash
# Monitor with 30-second analysis updates
python realtime_monitor.py
```
- Get instant price updates
- React to market changes quickly
- See candle formation in real-time

### **Swing Trading:**
```bash
# Run with 5-minute analysis
# Monitor for significant changes
# Get alerted when conditions change
```

### **Position Monitoring:**
```python
# Check if you should exit/adjust position
from realtime_client import KrakenWebSocketClient

client = KrakenWebSocketClient(pair='ETH/USD')
client.start()

# Your entry price
entry_price = 3200.00

while True:
    current = client.get_current_price()
    pnl_pct = ((current - entry_price) / entry_price) * 100

    print(f"Current: ${current:,.2f} | PnL: {pnl_pct:+.2f}%")

    # Exit conditions
    if pnl_pct >= 5.0:
        print("✅ Take profit target hit!")
        break
    elif pnl_pct <= -2.0:
        print("🛑 Stop loss hit!")
        break

    time.sleep(1)
```

### **Market Research:**
```python
# Analyze order book depth
# Study trade patterns
# Calculate volume profiles in real-time
```

---

## 🔧 Troubleshooting

### **Issue: WebSocket won't connect**

**Check internet connection:**
```bash
ping ws.kraken.com
```

**Test WebSocket endpoint:**
```bash
curl -I https://www.kraken.com
```

**Restart client:**
```python
client.stop()
time.sleep(2)
client.start()
```

---

### **Issue: No data flowing**

**Check if subscribed:**
Look for these messages on start:
```
✓ Subscribed to ticker for ETHUSD
✓ Subscribed to ohlc for ETHUSD
✓ Subscribed to trade for ETHUSD
✓ Subscribed to book for ETHUSD
```

**Check connection status:**
```python
print(f"Connected: {client.connected}")
print(f"Last heartbeat: {client.last_heartbeat}")
```

---

### **Issue: Slow or delayed data**

**Reduce analysis frequency:**
```python
monitor = RealTimeMarketMonitor(pair='ETH/USD', analysis_interval=120)  # 2 minutes
```

**Close other applications** using bandwidth

**Check Kraken API status:** https://status.kraken.com

---

## 📈 Performance Tips

### **Optimize for Speed:**
```python
# Reduce order book depth
client._subscribe_order_book(depth=5)  # Instead of 10

# Only subscribe to needed channels
# Comment out unused subscriptions in on_open()

# Increase analysis interval
monitor = RealTimeMarketMonitor(analysis_interval=300)  # 5 minutes
```

### **Reduce CPU Usage:**
```python
# Disable verbose logging
websocket.enableTrace(False)

# Don't store too many trades
self.recent_trades = deque(maxlen=50)  # Instead of 100
```

---

## 🎯 Next Steps

### **1. Test WebSocket Connection:**
```bash
python realtime_client.py
```
Should connect and stream data for 5 minutes.

### **2. Try Real-Time Monitor:**
```bash
python realtime_monitor.py
```
See live analysis with alerts.

### **3. Integrate with Your Strategy:**
```python
# Use in your trading bot
# Add custom alert handlers
# Connect to Discord webhooks
# Log data to database
```

---

## 📊 Comparison: Historical vs Real-Time

| Feature | Historical (CSV) | Real-Time (WebSocket) |
|---------|------------------|----------------------|
| **Latency** | 4 hours - 24 hours | < 1 second |
| **Data** | Completed candles | Forming candles + ticks |
| **Use Case** | Swing trading, backtesting | Day trading, monitoring |
| **Updates** | Manual/Cron | Continuous stream |
| **Cost** | Free | Free (Kraken) |
| **CPU** | Low | Medium |

---

## 🔐 Security Notes

- ✅ WebSocket is **read-only** (no trading)
- ✅ No API keys needed for public data
- ✅ Kraken WebSocket is encrypted (WSS)
- ✅ No personal data sent

---

## ✅ Quick Start Checklist

- [ ] Test basic WebSocket: `python realtime_client.py`
- [ ] Try real-time monitor: `python realtime_monitor.py`
- [ ] Set custom analysis interval
- [ ] Add alert callbacks (optional)
- [ ] Integrate with existing system

---

## 🚀 You're Ready for Real-Time Trading!

```bash
# Start monitoring now
python realtime_monitor.py
```

Watch your ETH positions in real-time! 📈
