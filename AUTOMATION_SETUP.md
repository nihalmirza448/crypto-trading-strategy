# 🤖 Automated ETH Trading System

## ✅ Active Cron Jobs

Your Ethereum trading system now runs automatically in the background, even when Claude is not active!

### **Job 1: Daily Data Updates** 📊
- **Schedule:** Every day at 12:03 AM
- **Command:** Updates last 7 days of ETH price data
- **Log File:** `logs/data_updates.log`

### **Job 2: Market Analysis & Alerts** 🚨
- **Schedule:** Every 4 hours (12:07 AM, 4:07 AM, 8:07 AM, 12:07 PM, 4:07 PM, 8:07 PM)
- **Command:** Analyzes market, detects changes, sends Discord alerts
- **Log File:** `logs/market_analysis.log`

---

## 📋 What Happens Automatically

### **Every 4 Hours:**
1. ✅ Analyzes current ETH market conditions
2. ✅ Checks for parabolic bull run (5 criteria)
3. ✅ Fetches CoinGlass data (liquidations, sentiment)
4. ✅ Compares to previous state
5. ✅ **Sends Discord alert ONLY if significant changes:**
   - Parabolic status changes
   - Recommendation changes (WAIT → LONG, etc.)
   - Confidence changes >20%
   - Price moves >5%

### **Every Day at Midnight:**
1. ✅ Downloads fresh ETH price data
2. ✅ Updates historical database
3. ✅ Keeps data current for analysis

---

## 🔔 Discord Alerts

**To receive alerts, add your Discord webhook to `.env`:**

```bash
# Edit .env file
nano .env

# Add this line:
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_HERE
```

**Get a Discord webhook:** See `DISCORD_SETUP.md`

---

## 📊 Monitor the System

### **View Recent Analysis:**
```bash
cd "Ethereum swing trading"

# View latest analysis results
cat results/last_market_state.json | jq .

# View all saved reports
ls -lht results/market_analysis_*.json | head -5
```

### **Check Logs:**
```bash
# Market analysis log (every 4 hours)
tail -f logs/market_analysis.log

# Data updates log (daily)
tail -f logs/data_updates.log

# View last 50 lines
tail -50 logs/market_analysis.log
```

### **Test Manually:**
```bash
cd "Ethereum swing trading"
source venv/bin/activate

# Run analysis now (force alert)
python market_analyzer.py --force-alert

# Run data update now
python data_collector.py --days 7
```

---

## 🛠️ Manage Cron Jobs

### **View All Jobs:**
```bash
crontab -l
```

### **Edit Jobs:**
```bash
crontab -e
```

### **Remove All Jobs:**
```bash
crontab -r
```

### **Disable Temporarily:**
Comment out jobs in crontab:
```bash
crontab -e

# Add # at start of line to disable:
# 7 */4 * * * cd "/Users/nihal/cursor-projects/..." ...
```

---

## ⚙️ Customize Schedule

### **Change Analysis Frequency:**

```bash
crontab -e
```

**Options:**

```bash
# Every 2 hours (more frequent)
7 */2 * * * cd "/Users/nihal/..." && source venv/bin/activate && python market_analyzer.py >> logs/market_analysis.log 2>&1

# Every 6 hours (less frequent)
7 */6 * * * cd "/Users/nihal/..." && source venv/bin/activate && python market_analyzer.py >> logs/market_analysis.log 2>&1

# Only during trading hours (9 AM - 9 PM, every 4 hours)
7 9,13,17,21 * * * cd "/Users/nihal/..." && source venv/bin/activate && python market_analyzer.py >> logs/market_analysis.log 2>&1

# Only on weekdays
7 */4 * * 1-5 cd "/Users/nihal/..." && source venv/bin/activate && python market_analyzer.py >> logs/market_analysis.log 2>&1
```

---

## 🔍 Troubleshooting

### **Issue: No Discord alerts**

**Check:**
1. Is webhook URL in `.env` file?
   ```bash
   cat .env | grep DISCORD_WEBHOOK_URL
   ```

2. Are there significant changes?
   ```bash
   # Force alert to test
   python market_analyzer.py --force-alert
   ```

3. Check logs:
   ```bash
   tail -50 logs/market_analysis.log
   ```

---

### **Issue: Cron jobs not running**

**Check if cron daemon is running:**
```bash
# On macOS
sudo launchctl list | grep cron

# If not running, start it
sudo launchctl load -w /System/Library/LaunchDaemons/com.vixie.cron.plist
```

**Check system logs:**
```bash
# macOS
log show --predicate 'process == "cron"' --last 1h

# Or check mail for cron errors
mail
```

---

### **Issue: Python environment not found**

**Fix:**
```bash
# Make sure venv exists
ls -la "Ethereum swing trading/venv"

# If missing, recreate:
cd "Ethereum swing trading"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

### **Issue: Logs not updating**

**Check file permissions:**
```bash
ls -la "Ethereum swing trading/logs/"

# Fix if needed
chmod 755 "Ethereum swing trading/logs"
chmod 644 "Ethereum swing trading/logs"/*.log
```

---

## 📈 Example Workflow

### **Morning Routine:**

**1. Check overnight analysis:**
```bash
cd "Ethereum swing trading"

# View latest report
cat results/last_market_state.json | jq .

# Check Discord for any alerts
```

**2. Review logs:**
```bash
# See what happened overnight
tail -20 logs/market_analysis.log
```

**3. Check if data is current:**
```bash
# View latest data file
ls -lht historical_data/eth_usd_*.csv | head -1
```

---

### **Before Trading:**

**1. Run fresh analysis:**
```bash
python market_analyzer.py --force-alert
```

**2. Check recommendation:**
```bash
python get_recommendation.py --fetch-coinglass
```

**3. Review Discord alert (if sent)**

---

## 🔐 Security Best Practices

### **Protect Your Credentials:**
```bash
# Secure .env file (only you can read)
chmod 600 .env

# Don't commit to git
echo ".env" >> .gitignore
```

### **Monitor System Access:**
```bash
# Check who can read your crontab
ls -la /var/at/tabs/$(whoami) 2>/dev/null || echo "Crontab is secure"
```

---

## 📊 System Health Check

**Run this to verify everything is working:**

```bash
cd "Ethereum swing trading"

echo "=== Cron Jobs ==="
crontab -l | grep -v "^#"

echo ""
echo "=== Log Files ==="
ls -lh logs/

echo ""
echo "=== Latest Analysis ==="
if [ -f results/last_market_state.json ]; then
    cat results/last_market_state.json | jq -r '.recommendation.action, .parabolic.is_parabolic'
else
    echo "No analysis yet - will run at next scheduled time"
fi

echo ""
echo "=== Discord Webhook ==="
grep -q DISCORD_WEBHOOK_URL .env && echo "✅ Configured" || echo "⚠️  Not configured"

echo ""
echo "=== Virtual Environment ==="
[ -d venv ] && echo "✅ Exists" || echo "❌ Missing"
```

---

## 🎯 Next Steps

### **1. Set Up Discord (Optional but Recommended):**
See `DISCORD_SETUP.md` for instructions.

### **2. Wait for First Run:**
- Next analysis: Check `crontab -l` for schedule
- Or run manually: `python market_analyzer.py --force-alert`

### **3. Monitor for a Day:**
Watch logs to ensure everything runs smoothly:
```bash
tail -f logs/market_analysis.log
```

---

## 📚 Related Documentation

- `DISCORD_SETUP.md` - Set up Discord alerts
- `NEW_FEATURES.md` - Feature documentation
- `QUICKSTART.md` - Quick start guide
- `COINGLASS_API_GUIDE.md` - CoinGlass API reference

---

## 🚨 Emergency Commands

### **Stop All Automation:**
```bash
crontab -r
```

### **Stop Just Analysis (Keep Data Updates):**
```bash
crontab -l | grep -v "market_analyzer.py" | crontab -
```

### **Re-enable Default Schedule:**
```bash
# Copy from this file and paste into:
crontab -e
```

---

## ✅ Summary

**Your system is now running automatically!**

✅ Data updates daily at 12:03 AM
✅ Market analysis every 4 hours
✅ Discord alerts on significant changes
✅ All logs saved for review
✅ Works even when Claude is closed

**No action needed** - it just works! 🎉

Check `logs/market_analysis.log` periodically to see it in action.
