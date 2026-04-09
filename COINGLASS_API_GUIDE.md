# 🔑 CoinGlass API - Complete Integration Guide

## 📍 **Official Resources**

| Resource | URL |
|----------|-----|
| **CoinGlass Main Site** | https://www.coinglass.com/ |
| **API Pricing** | https://www.coinglass.com/pricing |
| **API Documentation** | https://open-api-v3.coinglass.com/api |
| **Support** | support@coinglass.com |

---

## 🎟️ **Getting Your API Key**

### **Step-by-Step:**

1. **Visit:** https://www.coinglass.com/pricing

2. **Sign Up / Login:**
   - Click "Sign Up" or "Login"
   - Use email or social login

3. **Choose Plan:**

   | Plan | Cost | Requests/Day | Best For |
   |------|------|--------------|----------|
   | Free | $0 | 50 | Testing |
   | Basic | $20/mo | 500 | Personal |
   | Pro | $50/mo | 2,000 | Active Trading |
   | Enterprise | $200+/mo | 10,000+ | Professional |

4. **Get API Key:**
   - Go to Dashboard → API Keys
   - Click "Create New Key"
   - Copy your key (e.g., `CG-abc123xyz456...`)

---

## 🔐 **Installing Your API Key**

### **Method 1: Environment Variable (Recommended) ✅**

**1. Create/Edit `.env` file:**
```bash
cd "Ethereum swing trading"
nano .env
```

**2. Add your key:**
```bash
# CoinGlass API Key
COINGLASS_API_KEY=CG-your-actual-api-key-here

# Other existing keys
KRAKEN_API_KEY=your_kraken_key
KRAKEN_API_SECRET=your_kraken_secret
```

**3. Save and test:**
```bash
python coinglass_client.py
```

### **Method 2: Direct in Code (Not Recommended)**

```python
from coinglass_client import CoinGlassClient

# Pass API key directly
client = CoinGlassClient(api_key='CG-your-key-here')
```

⚠️ **Security Warning:** Don't commit API keys to Git!

---

## 📡 **API Endpoints Implemented**

### **Base URL:**
```
https://open-api.coinglass.com/public/v2
```

### **Authentication:**
```python
headers = {
    'coinglassSecret': 'your_api_key_here'
}
```

---

## 🔥 **Available Endpoints in Your Code**

### **1. Liquidation Heatmap** 📊

**Endpoint:** `/liquidation_heatmap`

**Function:**
```python
client.get_liquidation_heatmap(symbol='ETH', exchange='All')
```

**Returns:**
```python
{
    'longs': [(price, amount), ...],      # Long liquidations below price
    'shorts': [(price, amount), ...],     # Short liquidations above price
    'current_price': 3500.00,
    'high_risk_long_level': 3325.00,      # Where longs get liquidated
    'high_risk_short_level': 3675.00,     # Where shorts get liquidated
    'total_long_liquidations': 200000000,
    'total_short_liquidations': 205000000
}
```

**Use Cases:**
- Find support levels (long liquidation clusters)
- Find resistance levels (short liquidation clusters)
- Avoid entering near major liquidation zones
- Predict price magnets

**Example:**
```python
from coinglass_client import CoinGlassClient

client = CoinGlassClient()
liq = client.get_liquidation_heatmap(symbol='ETH')

print(f"High Risk Long Liquidation: ${liq['high_risk_long_level']:,.0f}")
print(f"High Risk Short Liquidation: ${liq['high_risk_short_level']:,.0f}")

# Trading logic
if current_price < liq['high_risk_short_level'] * 1.02:
    print("Close to short liquidations - potential squeeze upward!")
```

---

### **2. Volume Profile** 📈

**Function:**
```python
client.get_volume_profile(symbol='ETH', timeframe='1d')
```

**Returns:**
```python
{
    'price_levels': [3200, 3210, 3220, ...],
    'volumes': [1000, 1500, 2000, ...],
    'poc': 3260.53,          # Point of Control (most volume)
    'vah': 3850.00,          # Value Area High (70% volume)
    'val': 3150.00,          # Value Area Low
    'timeframe': '1d'
}
```

**Use Cases:**
- Identify fair value zones
- Find high-volume nodes (strong support/resistance)
- Plan entries at Value Area Low
- Plan exits at Value Area High

**Example:**
```python
vp = client.get_volume_profile(symbol='ETH', timeframe='1d')

print(f"Point of Control: ${vp['poc']:,.2f}")
print(f"Value Area: ${vp['val']:,.2f} - ${vp['vah']:,.2f}")

# Trading logic
if current_price <= vp['val']:
    print("At value area low - good entry for long!")
```

---

### **3. Long/Short Ratio** 📊

**Endpoint:** `/indicator/long-short-ratio`

**Function:**
```python
client.get_long_short_ratio(symbol='ETH', exchange='All')
```

**Returns:**
```python
{
    'ratio': 1.15,              # Longs/Shorts ratio
    'long_percentage': 53.5,    # % of traders long
    'short_percentage': 46.5,   # % of traders short
    'sentiment': 'NEUTRAL'      # BULLISH, BEARISH, or NEUTRAL
}
```

**Interpretation:**
- **Ratio > 1.5**: Too many longs → Potential dump (contrarian short)
- **Ratio < 0.7**: Too many shorts → Potential squeeze (contrarian long)
- **Ratio 0.8-1.2**: Balanced → Follow trend

**Example:**
```python
ls = client.get_long_short_ratio(symbol='ETH')

print(f"L/S Ratio: {ls['ratio']:.2f}")
print(f"Sentiment: {ls['sentiment']}")

# Contrarian trading
if ls['ratio'] < 0.8:
    print("Many shorts - potential short squeeze!")
elif ls['ratio'] > 1.5:
    print("Many longs - potential long liquidation!")
```

---

### **4. Open Interest** 💰

**Endpoint:** `/indicator/open-interest`

**Function:**
```python
client.get_open_interest(symbol='ETH')
```

**Returns:**
```python
{
    'total_oi': 5000000000,    # Total open interest in USD
    'change_24h': 2.5,         # 24h change percentage
    'trend': 'INCREASING'      # INCREASING or DECREASING
}
```

**Use Cases:**
- Measure market leverage
- Confirm trend strength
- Detect overleveraged markets

**Interpretation:**
- **OI Increasing + Price Up**: Strong bullish trend
- **OI Increasing + Price Down**: Strong bearish trend
- **OI Decreasing + Price Up**: Short covering (weak bull)
- **OI Decreasing + Price Down**: Long liquidations (weak bear)

---

### **5. Funding Rates** 💸

**Endpoint:** `/indicator/funding-rate`

**Function:**
```python
client.get_funding_rates(symbol='ETH')
```

**Returns:**
```python
{
    'average_rate': 0.0034,     # Average funding rate (hourly)
    'rates_by_exchange': [...],
    'sentiment': 'NEUTRAL'      # BULLISH or BEARISH
}
```

**Interpretation:**
- **Rate > 0.01%**: Longs pay shorts → Bullish sentiment
- **Rate < -0.01%**: Shorts pay longs → Bearish sentiment
- **Rate near 0%**: Neutral sentiment

---

### **6. Market Summary** 🌐

**Function:**
```python
client.get_market_summary(symbol='ETH')
```

**Returns:** All above data combined
```python
{
    'liquidations': {...},
    'volume_profile': {...},
    'long_short_ratio': {...},
    'open_interest': {...},
    'funding_rates': {...},
    'timestamp': '2026-03-23T00:30:00'
}
```

**Best For:** Complete market overview

---

## 🚀 **Quick Examples**

### **Example 1: Check Before Trading**

```python
from coinglass_client import CoinGlassClient

client = CoinGlassClient()

# Get liquidation zones
liq = client.get_liquidation_heatmap()

# Get sentiment
ls = client.get_long_short_ratio()

print(f"Support: ${liq['high_risk_long_level']:,.0f}")
print(f"Resistance: ${liq['high_risk_short_level']:,.0f}")
print(f"L/S Ratio: {ls['ratio']:.2f} ({ls['sentiment']})")

# Decision logic
if ls['ratio'] < 0.85 and current_price < liq['high_risk_short_level']:
    print("✅ Setup: Many shorts + near liquidations = LONG opportunity")
```

### **Example 2: Volume Profile Entry**

```python
vp = client.get_volume_profile(timeframe='1d')

print(f"POC (fair value): ${vp['poc']:,.2f}")
print(f"VAL (good entry): ${vp['val']:,.2f}")
print(f"VAH (good exit): ${vp['vah']:,.2f}")

# Entry logic
if current_price <= vp['val'] * 1.01:
    print("✅ At Value Area Low - good long entry")
    entry = vp['val']
    target = vp['vah']
    stop = vp['val'] * 0.97
```

### **Example 3: Complete Market Check**

```python
summary = client.get_market_summary()

# Extract data
liq = summary['liquidations']
ls = summary['long_short_ratio']
oi = summary['open_interest']

print("="*60)
print("MARKET ANALYSIS")
print("="*60)
print(f"Liquidations: {liq['total_long_liquidations']/1e6:.0f}M longs, {liq['total_short_liquidations']/1e6:.0f}M shorts")
print(f"L/S Ratio: {ls['ratio']:.2f} ({ls['sentiment']})")
print(f"Open Interest: ${oi['total_oi']/1e9:.2f}B ({oi['trend']})")
print("="*60)
```

---

## ⚙️ **Rate Limits & Best Practices**

### **Free Tier (50 requests/day):**

**Daily Usage Strategy:**
```python
# Morning (1 request)
morning_summary = client.get_market_summary()

# Before each trade (1 request each)
pre_trade_check = client.get_liquidation_heatmap()

# Total: ~10 requests/day for 10 trades
```

**Efficient Usage:**
```python
# ✅ GOOD: Get all data once
summary = client.get_market_summary()  # 1 request
liq = summary['liquidations']
ls = summary['long_short_ratio']

# ❌ BAD: Multiple separate requests
liq = client.get_liquidation_heatmap()      # 1 request
ls = client.get_long_short_ratio()           # 1 request
oi = client.get_open_interest()              # 1 request
# Total: 3 requests for same data!
```

### **Built-in Rate Limiting:**

Your client already has rate limiting:
```python
self.min_request_interval = 1.0  # 1 second between requests
```

Change if needed:
```python
client = CoinGlassClient()
client.min_request_interval = 2.0  # 2 seconds between requests
```

---

## 🧪 **Testing Your API Key**

### **Test Script:**

```bash
cd "Ethereum swing trading"
python3 << 'EOF'
from coinglass_client import CoinGlassClient
import os

# Check if API key loaded
api_key = os.getenv('COINGLASS_API_KEY')
if api_key:
    print(f"✅ API Key loaded: {api_key[:8]}...")
else:
    print("⚠️  No API key found - using mock data")

# Test client
client = CoinGlassClient()
summary = client.get_market_summary(symbol='ETH')

print("\n✅ API Test Successful!")
print(f"L/S Ratio: {summary['long_short_ratio']['ratio']:.2f}")
EOF
```

---

## 🔍 **Troubleshooting**

### **Issue 1: "API Key not found"**

**Check .env file:**
```bash
cat .env | grep COINGLASS
```

**Should show:**
```
COINGLASS_API_KEY=CG-your-key-here
```

### **Issue 2: "500 Server Error"**

**Causes:**
1. Invalid API key
2. Rate limit exceeded
3. CoinGlass API temporarily down

**Solution:**
```python
# System falls back to mock data automatically
# Check if you're hitting rate limits
```

### **Issue 3: "Request failed"**

**Check:**
```python
from coinglass_client import CoinGlassClient

client = CoinGlassClient()
print(f"API Key: {client.api_key[:8] if client.api_key else 'None'}...")
```

---

## 📊 **Mock Data vs Live Data**

### **Currently (No API Key):**
- Uses realistic mock data
- Sufficient for testing
- No API costs
- Data is static

### **With API Key:**
- Real-time liquidation levels
- Accurate long/short ratios
- Current open interest
- Live funding rates
- Better trading decisions

---

## 💡 **Recommendation**

**For Your Use Case:**

1. **Start with FREE tier** (50 requests/day)
2. **Use mock data for backtesting** (no API needed)
3. **Use live data for actual trading** (get API key)
4. **Upgrade to Basic ($20/mo)** if making >50 requests/day

**Best Practice:**
```python
# Use in get_recommendation.py
python get_recommendation.py                # Mock data (free)
python get_recommendation.py --fetch-coinglass  # Live data (uses API)
```

---

## 🔗 **Additional Resources**

- **CoinGlass Blog:** https://www.coinglass.com/blog
- **Telegram Community:** https://t.me/coinglass
- **Twitter:** @coinglass_com
- **API Status:** Check website for outages

---

## 📝 **Summary Checklist**

- [ ] Visit https://www.coinglass.com/pricing
- [ ] Sign up and get API key
- [ ] Add key to `.env` file
- [ ] Test with `python coinglass_client.py`
- [ ] Use in recommendations with `--fetch-coinglass` flag

---

**Your system is already configured!** Just add your API key to `.env` when you get one. Until then, mock data works perfectly for testing! 🚀
