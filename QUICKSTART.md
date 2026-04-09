# 🚀 QUICK START GUIDE - Smart Trading Recommendations

## Installation (One-Time Setup)

```bash
cd "Ethereum swing trading"

# Activate virtual environment
source venv/bin/activate

# Install new dependencies
pip install requests flask-cors

# Verify installation
python3 coinglass_client.py
```

You should see mock data output (this is normal - CoinGlass API requires authentication).

---

## 🎯 Get Your First Recommendation (30 seconds)

### Option 1: Command Line (Fastest)

```bash
python get_recommendation.py
```

**Output:**
- ✅ Trading recommendation (LONG/SHORT/WAIT)
- 📊 Confidence score
- 💰 Entry price, stop loss, take profit
- 🎯 Leverage suggestion
- 🧠 Detailed reasoning

### Option 2: Web Dashboard (Best UX)

```bash
python enhanced_dashboard.py
```

Then open: **http://127.0.0.1:5003**

**Features:**
- Beautiful visual interface
- Real-time recommendation updates
- Parabolic bull run detector
- Liquidation zone visualization
- One-click refresh

---

## 📊 Example Workflow

### Daily Trading Routine:

**1. Morning Check (7:00 AM)**
```bash
# Check if market is parabolic
python get_recommendation.py --parabolic-only
```

**2. If Parabolic Detected:**
```bash
# Get full recommendation with reasoning
python get_recommendation.py --save
```

**3. Review & Execute:**
- Check confidence score (>60% = good)
- Verify entry zone matches current price
- Set stop loss BEFORE entering trade
- Use recommended leverage (5x max)

**4. Monitor:**
```bash
# Start dashboard to monitor
python enhanced_dashboard.py
```

---

## 🎮 Interactive Examples

### Example 1: Check Parabolic Status

```bash
python get_recommendation.py --parabolic-only
```

**Sample Output:**
```
✅ PARABOLIC BULL RUN DETECTED!

Confidence: 85%
Distance from 200 SMA: +25.3%
SMA Slope (weekly): +4.5%

Criteria Met: 5/5

Detailed Criteria:
  ✓ Price >20% above 200 SMA
  ✓ SMA rising >3% per week
  ✓ All SMAs aligned
  ✓ Strong momentum
  ✓ High volume
```

**What to do:**
- **If YES** → Get full recommendation
- **If NO** → Wait, don't force trades

### Example 2: Get Full Recommendation

```bash
python get_recommendation.py
```

**Sample Output:**
```
🟢 RECOMMENDATION: GO LONG

   Entry: $3,450 - $3,520
   Stop Loss: $3,346
   Take Profit: $3,675
   Leverage: 5x

   Confidence: 85%
   Risk Level: MEDIUM

Reasoning:
✓ PARABOLIC BULL RUN detected (85% confidence)
  - Price +25.3% above 200 SMA
  - SMA slope: +4.5% per week
✓ Liquidation bias supports LONG (more shorts to squeeze)
✓ L/S ratio 0.85 - many shorts to squeeze
```

### Example 3: Use Web Dashboard

```bash
python enhanced_dashboard.py
```

Open http://127.0.0.1:5003 and click **"Get Recommendation"**

---

## ⚙️ Configuration

### Use Live CoinGlass Data (Optional)

**Free Tier (50 requests/day):**

1. Get API key: https://www.coinglass.com/pricing
2. Add to `.env`:
   ```
   COINGLASS_API_KEY=your_key_here
   ```
3. Update `coinglass_client.py` line 26:
   ```python
   def __init__(self, api_key=os.getenv('COINGLASS_API_KEY')):
   ```

**Fetch live data:**
```bash
python get_recommendation.py --fetch-coinglass
```

### Customize Strategy Parameters

Edit `recommendation_engine.py`:

```python
# Parabolic detection (line ~70)
MIN_DISTANCE_FROM_200SMA = 20  # Minimum % above 200 SMA
MIN_SMA_SLOPE_WEEKLY = 3.0     # Minimum weekly slope
MIN_CRITERIA_MET = 3           # Out of 5 total criteria

# Leverage (line ~180)
recommendation['leverage'] = 5  # Max 5x recommended

# Confidence adjustments (line ~187)
if liq_analysis['bias'] == 'LONG':
    recommendation['confidence'] += 10
```

---

## 🎯 Trading Strategy

### **ONLY Trade Parabolic Bull Runs**

**Setup Checklist:**
- ✅ Parabolic confidence >60%
- ✅ Distance from 200 SMA >20%
- ✅ SMA slope >3% per week
- ✅ Liquidation zones favor direction
- ✅ Long/Short ratio supports move

**Entry:**
- Wait for pullback to entry zone
- Use limit orders (better prices)
- Start with 50% position size

**Risk Management:**
- Stop loss: 3% (15% loss at 5x leverage)
- Take profit: 5% (25% gain at 5x leverage)
- Max hold time: 72 hours
- Risk only 2% of capital per trade

**Example Trade:**
```
Capital: $7,500
Risk per trade: $150 (2% of $7,500)
Position size: $7,500 × 50% = $3,750
Leverage: 5x
Position value: $18,750

Entry: $3,500
Stop: $3,395 (3% = $563 loss = 15% of $3,750)
Target: $3,675 (5% = $938 gain = 25% of $3,750)

Risk/Reward: 1:1.7 (acceptable)
Win rate needed: 37% (achievable!)
```

---

## 📈 Performance Tracking

### Save All Recommendations

```bash
# Saves to results/recommendation_TIMESTAMP.json
python get_recommendation.py --save
```

### Review Past Recommendations

```bash
# View recent recommendations
ls -lt results/recommendation_*.json | head -5
cat results/recommendation_20260323_120000.json
```

### Compare with Backtests

```bash
# Run backtest with original strategy
python backtester.py

# Compare recommendation confidence vs actual results
# High confidence (>70%) recommendations should have higher win rates
```

---

## 🐛 Common Issues & Fixes

### Issue: "Data file not found"

**Fix:**
```bash
python data_collector.py --days 1825
```

### Issue: "No module named 'requests'"

**Fix:**
```bash
source venv/bin/activate
pip install requests flask-cors
```

### Issue: "CoinGlass API error"

**Fix:**
- This is normal without API key
- System uses mock data automatically
- Get free API key for live data

### Issue: All recommendations say "WAIT"

**Fix:**
- Market is not parabolic
- This is GOOD - protects you from bad trades
- Wait for parabolic setup (happens 16% of time)

---

## 💡 Pro Tips

1. **Don't force trades** - Most of time, answer is WAIT
2. **Start small** - Use 50% position size first
3. **Paper trade first** - Test for 1 month before live
4. **Track everything** - Keep a trading journal
5. **Follow the system** - Don't override high confidence signals

---

## ⚠️ Important Reminders

- **Not financial advice** - Do your own research
- **High risk** - Only trade with money you can lose
- **Test first** - Paper trade before going live
- **Stay disciplined** - Follow stop losses religiously
- **Don't revenge trade** - One loss is not the end

---

## 🚀 Next Steps

1. **Test parabolic detection:**
   ```bash
   python get_recommendation.py --parabolic-only
   ```

2. **Get your first recommendation:**
   ```bash
   python get_recommendation.py --save
   ```

3. **Explore the dashboard:**
   ```bash
   python enhanced_dashboard.py
   ```

4. **Study the code:**
   - Read `recommendation_engine.py` to understand logic
   - Read `REALISTIC_TRADING_GUIDE.md` for strategy insights
   - Review backtest results in `results/` directory

---

## 📚 Additional Resources

- **NEW_FEATURES.md** - Detailed feature documentation
- **REALISTIC_TRADING_GUIDE.md** - Honest assessment of what works
- **BACKTEST_ANALYSIS.md** - Historical performance data
- **config.py** - All adjustable parameters

---

**Ready to trade smarter! 🎯**

Remember: The best trade is often no trade. Wait for 60%+ confidence parabolic setups.
