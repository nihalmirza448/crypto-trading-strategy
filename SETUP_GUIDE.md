# Setup Guide for Ethereum Swing Trading System

## Quick Start

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

**Note on TA-Lib:** If you have issues installing `ta-lib`, you can comment it out in requirements.txt. The strategy uses custom indicators and doesn't strictly require TA-Lib.

### 2. Get Kraken API Keys (for data collection)

1. Go to https://www.kraken.com/
2. Sign up or log in
3. Navigate to Settings → API
4. Create a new API key with "Query Funds" and "Query Open Orders & Trades" permissions
5. Copy the API key and secret

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your Kraken API keys
```

### 4. Collect Historical Data

```bash
python data_collector.py
```

This will fetch 120 days of 1-minute ETH/USD data from Kraken. Takes about 2-3 minutes.

### 5. Run Backtest

```bash
python backtester.py
```

This will:
- Calculate technical indicators
- Run the momentum swing strategy
- Generate performance metrics
- Create visualization plots
- Save results to `results/` directory

## Understanding the Results

### Key Metrics to Watch:

1. **Win Rate**: Should be > 50% for this aggressive strategy
2. **Profit Factor**: Should be > 1.5 (gross profit / gross loss)
3. **Max Drawdown**: Critical - shows worst case loss
4. **Sharpe Ratio**: Risk-adjusted returns (> 1.0 is good)
5. **Liquidations**: Any liquidation is CRITICAL - means you'd lose entire capital

### Important Considerations:

- **Leverage amplifies both gains and losses**: 30x leverage means a 3.33% adverse move = 100% loss
- **Funding rates**: On perpetual contracts, you pay/receive funding every 8 hours
- **Slippage**: During volatile moves, you may not get your desired price
- **Exchange outages**: During peak volatility, exchanges can be slow or down

## Recommended UK Exchanges for Live Trading

### 1. Bybit (Recommended)
- **Pros**: Up to 100x leverage, fast execution, good API
- **Cons**: Not FCA regulated
- **Setup**: https://www.bybit.com/
- **API Docs**: https://bybit-exchange.github.io/docs/

### 2. OKX
- **Pros**: Up to 125x leverage, advanced features
- **Cons**: Complex interface for beginners
- **Setup**: https://www.okx.com/
- **API Docs**: https://www.okx.com/docs-v5/

### 3. Kraken (Conservative Option)
- **Pros**: FCA regulated, safest option, good reputation
- **Cons**: Only 5x leverage (not suitable for 100% return target)
- **Setup**: https://www.kraken.com/

### 4. dYdX (Decentralized)
- **Pros**: No KYC, up to 20x leverage, on-chain
- **Cons**: Less liquid, more complex
- **Setup**: https://dydx.exchange/

## Risk Management Setup

### Position Size Calculator

With 30x leverage and $1000 capital:
- Position size: $30,000
- Liquidation at: 3.33% adverse move
- 1% price move = 30% capital gain/loss

### Recommended Safety Measures:

1. **Start with lower leverage (10-15x)** until you're confident
2. **Use stop losses religiously** - set them BEFORE entering trade
3. **Never risk more than 2-5% per trade** on actual capital
4. **Keep emergency funds** on exchange to prevent liquidation
5. **Monitor funding rates** - can eat into profits

## Monitoring Tools Setup

### TradingView Alerts
1. Go to https://www.tradingview.com/
2. Set up chart for ETH/USD
3. Create alerts for:
   - 2% price move in 5 minutes
   - Volume spikes
   - RSI extremes

### CryptoWatch
1. https://cryptowat.ch/
2. Multi-exchange price monitoring
3. Set up alerts for price divergence

### Discord/Telegram Bots
- Create a bot to send you alerts
- Monitor position status
- Get liquidation warnings

## Paper Trading First!

Before risking real money:

1. **Use Testnet**: Most exchanges offer testnet trading
2. **Small position sizes**: Start with $100, not $1000
3. **Track performance**: Keep a trading journal
4. **Emotional control**: Make sure you can handle the volatility

## Optimization Tips

If backtest results aren't good:

1. **Adjust momentum threshold**: Try 1.5% or 2.5% instead of 2%
2. **Change volume multiplier**: Try 2x or 4x
3. **Modify take profit**: Maybe 2.5% or 4% works better
4. **Tighter stop loss**: Reduce from 2% to 1.5%
5. **Different timeframes**: Try 3-minute or 15-minute candles

Edit these in `config.py` and re-run backtest.

## Next Steps After Successful Backtest

1. ✅ Review metrics and ensure profitability
2. ✅ Run backtest on different time periods (forward testing)
3. ✅ Paper trade for 2-4 weeks
4. ✅ Start with small live positions ($100-200)
5. ✅ Gradually scale up as you gain confidence
6. ✅ Keep detailed records of all trades
7. ✅ Review and adjust strategy monthly

## Emergency Procedures

### If Position Goes Against You:
1. Don't panic
2. Check if stop loss will trigger
3. If necessary, manually close position
4. NEVER add to a losing position (no "averaging down")

### If Exchange is Down:
1. Have accounts on 2-3 exchanges
2. Keep emergency funds to close positions on another exchange
3. Consider hedging on another exchange

### If You Get Liquidated:
1. Stop trading immediately
2. Review what went wrong
3. Adjust risk management
4. Start smaller when resuming

## Support and Questions

This is a complex system with significant risks. Make sure you:
- Understand every parameter
- Test thoroughly before live trading
- Start small
- Use proper risk management

**Remember: 20-30x leverage is extremely aggressive. Most professional traders use 3-10x.**

Good luck and trade safely! 🚀
