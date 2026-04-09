# Ethereum High-Leverage Swing Trading System

## Overview
This system is designed to capture rapid Ethereum price movements using 20-30x leverage, targeting 100% returns per trade by entering during strong momentum and exiting when volatility stabilizes.

## Project Structure
- `data_collector.py` - Fetches historical data from Kraken API
- `backtester.py` - Backtesting engine for strategy validation
- `strategy.py` - Momentum-based swing trading strategy
- `indicators.py` - Technical indicators for volatility and momentum
- `risk_manager.py` - Position sizing and risk controls
- `live_trader.py` - Live trading implementation (use with caution)
- `config.py` - Configuration settings

## UK Exchanges Supporting High-Leverage ETH Trading

### Recommended Exchanges:
1. **Bybit** (supports up to 100x leverage)
   - Fast execution
   - WebSocket API for real-time data
   - Good for UK traders
   
2. **OKX** (supports up to 125x leverage)
   - Advanced order types
   - Low latency
   - UK accessible

3. **Kraken** (up to 5x leverage - lower but regulated)
   - FCA regulated
   - More conservative but safer
   - Good for backtesting data

4. **dYdX** (decentralized, up to 20x)
   - No KYC
   - On-chain settlement

**Note:** High leverage (20-30x) significantly increases liquidation risk. With 30x leverage, a 3.33% adverse move liquidates your position.

## Strategy Overview

### Entry Signals:
- Rapid price movement (> 2% in 5 minutes)
- High volume surge (> 3x average)
- RSI breaking key levels
- MACD momentum confirmation

### Exit Signals:
- Volatility contraction (Bollinger Bands squeeze)
- Volume drying up
- Price stabilization
- Stop-loss (2-3% from entry)
- Take-profit (3-5% target for 100% return on 30x leverage)

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure API Keys
Create a `.env` file:
```
KRAKEN_API_KEY=your_key
KRAKEN_API_SECRET=your_secret
EXCHANGE_API_KEY=your_trading_exchange_key
EXCHANGE_API_SECRET=your_trading_exchange_secret
```

### 3. Collect Historical Data
```bash
python data_collector.py --days 120
```

### 4. Run Backtest
```bash
python backtester.py --leverage 30 --capital 1000
```

### 5. Analyze Results
Results will be saved in `results/` directory with performance metrics.

## Risk Warnings

⚠️ **CRITICAL RISKS:**
- 30x leverage means 3.33% adverse move = liquidation
- Ethereum can move 5-10% in minutes
- Funding rates can eat profits
- Slippage on volatile moves
- Exchange outages during volatility

## Recommended Monitoring Tools

1. **TradingView** - Real-time charts and alerts
2. **CryptoWatch** - Multi-exchange monitoring
3. **3Commas** - Trading bot integration
4. **Discord/Telegram Bots** - Custom alerts
5. **Prometheus + Grafana** - System monitoring

## Performance Metrics Tracked
- Win rate
- Average return per trade
- Maximum drawdown
- Sharpe ratio
- Profit factor
- Average hold time
- Liquidation events (simulated)
