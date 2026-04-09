# 🔔 Discord Alerts Setup Guide

## 📊 **Market Analysis with Discord Notifications**

Your system can now send automatic alerts to Discord when market conditions change!

---

## 🎯 **What You Get**

### **Automatic Alerts When:**
- ✅ Market enters/exits parabolic bull run
- ✅ Recommendation changes (WAIT → LONG or vice versa)
- ✅ Confidence level changes significantly (>20%)
- ✅ Major price movements (>5%)

### **Alert Includes:**
- 💰 Current ETH price
- 📊 Trading recommendation (LONG/SHORT/WAIT)
- 🚀 Parabolic status
- 📈 Confidence score
- 🎯 Entry/stop/target levels
- 🧠 Key reasoning
- ⏰ Timestamp

---

## 🔑 **Step 1: Create Discord Webhook** (2 Minutes)

### **Option A: Your Own Discord Server**

1. **Open Discord** → Go to your server
2. **Server Settings** → Click gear icon
3. **Integrations** → Click "Integrations"
4. **Webhooks** → Click "Webhooks"
5. **New Webhook** → Click "New Webhook"
6. **Name it:** "ETH Market Analyzer"
7. **Choose channel:** #trading-alerts (or any channel)
8. **Copy Webhook URL** → Looks like:
   ```
   https://discord.com/api/webhooks/123456789/abcdefghijklmnop...
   ```

### **Option B: Test Server (Public)**

If you don't have a Discord server, create one:
1. Click **+** (Add a Server)
2. Click **Create My Own**
3. Name it: "Trading Alerts"
4. Follow steps above to create webhook

---

## 💾 **Step 2: Add Webhook to .env File** (30 Seconds)

### **Quick Command:**

```bash
cd "Ethereum swing trading"

# Add your Discord webhook
echo 'DISCORD_WEBHOOK_URL=your_webhook_url_here' >> .env
```

### **Or Edit Manually:**

```bash
nano .env
```

Add this line:
```bash
# Discord Webhook for Market Alerts
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/123456789/abcdefghijklmnop...
```

**Save:** Press `Ctrl+X`, then `Y`, then `Enter`

---

## ✅ **Step 3: Test Discord Alert** (30 Seconds)

### **Send Test Alert:**

```bash
cd "Ethereum swing trading"
source venv/bin/activate
python market_analyzer.py --force-alert
```

**You should see in Discord:**
- 📊 Beautiful embed with market data
- 🟢/🔴/⚪ Color-coded by recommendation
- 📈 All key metrics
- 🧠 Trading reasoning

---

## 🚀 **Step 4: Run Market Analysis**

### **Manual Run:**

```bash
# Run analysis (only alerts on changes)
python market_analyzer.py

# Force alert even if no changes
python market_analyzer.py --force-alert
```

### **Output:**
```
📊 ETHEREUM MARKET ANALYSIS
💰 Current ETH Price: $2,079.61
⚪ STATUS: NOT IN PARABOLIC BULL RUN
⚪ ACTION: WAIT

📢 CHANGE DETECTED:
   First analysis - no previous state to compare

✅ Discord alert sent successfully!
```

---

## 🤖 **Step 5: Automate with Cron** (Optional)

### **Run Every 4 Hours:**

```bash
# Edit crontab
crontab -e

# Add this line (checks every 4 hours)
0 */4 * * * cd "/Users/nihal/cursor-projects/Ethereum swing trading" && source venv/bin/activate && python market_analyzer.py >> logs/market_analysis.log 2>&1
```

### **Alternative Schedules:**

```bash
# Every hour
0 * * * * ...

# Every 6 hours
0 */6 * * * ...

# Twice daily (9 AM and 9 PM)
0 9,21 * * * ...

# Only on weekdays at market open (9:30 AM)
30 9 * * 1-5 ...
```

---

## 📊 **What the Alert Looks Like**

### **Discord Embed Format:**

```
┌─────────────────────────────────────┐
│ 🟢 ETH Market Alert - ENTER LONG    │
│ Parabolic bull run detected!        │
├─────────────────────────────────────┤
│ 💰 Current Price    | $3,500.00     │
│ 📊 Confidence       | 85%           │
│ ⚠️ Risk Level       | MEDIUM        │
│ 🚀 Parabolic Status | ✅ YES        │
│ 📈 Criteria Met     | 5/5           │
│ 📊 Distance 200 SMA | +25.3%        │
│ 🎯 Entry Zone       | $3,450-$3,520 │
│ 🛑 Stop Loss        | $3,346        │
│ 🎯 Take Profit      | $3,675        │
│                                     │
│ 🧠 Key Reasoning:                   │
│ • Parabolic bull run (85% conf)    │
│ • Price +25.3% above 200 SMA       │
│ • SMA slope: +4.5% per week        │
└─────────────────────────────────────┘
Analysis Time: 2026-03-23 01:00:00
```

### **Color Coding:**
- 🟢 **Green:** ENTER LONG (high confidence)
- 🔴 **Red:** CONSIDER SHORT
- ⚪ **Gray:** WAIT (no setup)

---

## 🎛️ **Advanced Options**

### **Custom Webhook per Run:**

```bash
python market_analyzer.py --webhook "https://discord.com/api/webhooks/..."
```

### **Check Without Alert:**

```bash
# Just analyze, no Discord (unless changes detected)
python market_analyzer.py
```

### **Force Alert Always:**

```bash
# Always send to Discord
python market_analyzer.py --force-alert
```

---

## 📁 **Report Files**

Every analysis saves two files:

### **1. Current State** (for change detection):
```
results/last_market_state.json
```

### **2. Detailed Analysis** (timestamped):
```
results/market_analysis_20260323_005925.json
```

**View report:**
```bash
cat results/market_analysis_*.json | jq .
```

---

## 🔍 **Troubleshooting**

### **Issue: "No Discord webhook URL"**

**Fix:**
```bash
# Check .env
cat .env | grep DISCORD

# Add if missing
echo 'DISCORD_WEBHOOK_URL=your_url' >> .env
```

### **Issue: "Failed to send Discord alert"**

**Causes:**
1. Invalid webhook URL
2. Webhook deleted
3. No internet connection

**Fix:**
```bash
# Test webhook manually
curl -X POST "your_webhook_url" \
  -H "Content-Type: application/json" \
  -d '{"content": "Test message"}'
```

### **Issue: "Alert not sending on changes"**

**Check:**
```bash
# View last state
cat results/last_market_state.json

# Force new analysis
rm results/last_market_state.json
python market_analyzer.py
```

---

## 📊 **When You'll Get Alerts**

### **Scenario 1: Parabolic Detected** 🚀

**Before:**
```json
{
  "parabolic": {"is_parabolic": false},
  "recommendation": {"action": "WAIT", "confidence": 0}
}
```

**After:**
```json
{
  "parabolic": {"is_parabolic": true},
  "recommendation": {"action": "ENTER LONG", "confidence": 85}
}
```

**Discord Alert:**
```
🚀 PARABOLIC BULL RUN DETECTED!
📊 Recommendation changed: WAIT → ENTER LONG
```

---

### **Scenario 2: Confidence Increase** 📈

**Before:**
```json
{"recommendation": {"confidence": 40}}
```

**After:**
```json
{"recommendation": {"confidence": 75}}
```

**Discord Alert:**
```
📈 Confidence changed: 40% → 75%
```

---

### **Scenario 3: Major Price Move** 💰

**Before:**
```json
{"current_price": 2000}
```

**After:**
```json
{"current_price": 2150}
```

**Discord Alert:**
```
💰 Significant price move: $2,000 → $2,150 (+7.5%)
```

---

## 💡 **Best Practices**

### **1. Test First**
```bash
python market_analyzer.py --force-alert
```
Verify Discord message looks good.

### **2. Set Up Monitoring**
```bash
# Add to cron for automatic checks
0 */4 * * * python market_analyzer.py
```

### **3. Check Logs**
```bash
# Create logs directory
mkdir -p logs

# View logs
tail -f logs/market_analysis.log
```

### **4. Backup States**
```bash
# Backup last state before major changes
cp results/last_market_state.json results/backup_state.json
```

---

## 🎯 **Example Workflow**

### **Daily Trading Routine:**

**Morning (9:00 AM):**
```bash
python market_analyzer.py --force-alert
```
→ Check Discord for overnight changes

**During Day (Auto):**
```
Cron runs every 4 hours
→ Alerts if conditions change
```

**Evening (9:00 PM):**
```bash
python market_analyzer.py --force-alert
```
→ Final check before close

---

## 📚 **Command Reference**

```bash
# Basic analysis
python market_analyzer.py

# Force Discord alert
python market_analyzer.py --force-alert

# Custom webhook
python market_analyzer.py --webhook "https://..."

# Help
python market_analyzer.py --help
```

---

## 🎓 **Understanding Change Detection**

### **Significant Changes Tracked:**

| Change Type | Threshold | Alert |
|-------------|-----------|-------|
| Parabolic Status | Any change | ✅ Always |
| Recommendation | Any change | ✅ Always |
| Confidence | >20% change | ✅ Yes |
| Price | >5% move | ✅ Yes |
| Small changes | <thresholds | ❌ No alert |

### **Smart Filtering:**

System only alerts on **significant** changes, avoiding spam:
- ✅ Market enters parabolic = Alert
- ✅ WAIT → LONG = Alert
- ✅ Confidence 40% → 80% = Alert
- ❌ Price +1.5% = No alert (too small)
- ❌ Confidence 65% → 67% = No alert

---

## 🔐 **Security**

### **Protect Your Webhook:**

```bash
# Don't commit to Git
echo "DISCORD_WEBHOOK_URL=*" >> .gitignore

# Restrict file permissions
chmod 600 .env
```

### **Regenerate Webhook:**

If webhook is compromised:
1. Go to Discord → Server Settings → Integrations
2. Delete old webhook
3. Create new webhook
4. Update .env file

---

## ✅ **Quick Setup Checklist**

- [ ] Create Discord webhook
- [ ] Add to `.env` file
- [ ] Test with `--force-alert`
- [ ] Verify message in Discord
- [ ] Set up cron job (optional)
- [ ] Monitor for changes

---

## 🚀 **You're Ready!**

```bash
# Run your first analysis
python market_analyzer.py --force-alert
```

Check Discord for your first market alert! 🎉

---

**Questions?** Read: `market_analyzer.py` source code for details.
