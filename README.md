# Professional Crypto Trading Strategy: Confluence-Based Edge

## Overview
This repository contains a professional-grade crypto trading strategy focused on identifying high-probability entry points using a confluence of institutional order flow concepts: Cumulative Volume Delta (CVD) analysis, liquidity cluster detection, and market structure identification. The strategy is designed for backtesting and provides a clear, rule-based approach to market engagement.

## Strategy Core Concepts

### Confluence-Based Entries
The strategy enters trades only when multiple independent signals align, forming a "confluence score." A high confluence score indicates a strong probability setup, minimizing noise and false signals. Key confluence factors include:
-   **Liquidity Sweeps (BSL/SSL):** Identifying when price takes out buy-side or sell-side liquidity, often signaling a reversal or continuation.
-   **CVD Divergences/Surges:** Analyzing cumulative volume delta for shifts in buying/selling pressure that diverge from price action or indicate strong directional momentum.
-   **Order Block Confirmation:** Recognizing institutional supply/demand zones (order blocks) and confirming price interaction with these levels.
-   **Market Structure (BOS/CHOCH):** Detecting continuation patterns (Break of Structure - BOS) or potential reversals (Change of Character - CHOCH) to align with the prevailing trend or anticipate shifts.

### Time-Based Exits
Trades are managed with predefined time-based exit rules, focusing on capturing profit targets within a specified window. The strategy employs a fixed position size and does not use traditional stop-losses, instead relying on the robust entry confluence and time-based profit taking.

## Backtested Performance

Based on extensive backtesting on 1-hour candles, the Professional Trading Strategy has demonstrated strong results under various conditions. The initial figures (74% Win Rate and ~1100% Annualized Return) generally align with high-leverage 1h runs.

Below are detailed results from a leverage sweep run on ETH and BTC 1h data (approximately 1 year of data, fixed $1,000 capital, no compounding per trade):

| Run                  | Win Rate | Total Return (≈1 year) |
| :------------------- | :------- | :--------------------- |
| ETH 1h @ 25x         | 56.7%    | 991%                   |
| ETH 1h @ 100x        | 72.1%    | 5,619%                 |
| BTC 1h @ 100x        | 75.0%    | 2,894%                 |

**Important Caveats:**
*   **"Annual Return" Interpretation:** The "Total Return" figures above represent the cumulative percentage return over the entire backtest period (~1 year), not necessarily a strict annualization formula.
*   **Fixed Capital Sizing:** High returns (e.g., 5,000%+ at 100x leverage) are based on a fixed $1,000 notional capital per trade, which does not account for realistic live compounding of profits and losses. These figures are for illustrative purposes to compare strategy performance across different leverage levels.
*   **Reproducibility:** These results were generated using `optimize_leverage_fixed.py`. The output is saved to `results/leverage_sweep_fixed_1k.csv`.

**Note:** These are backtested results and do not guarantee future performance.

## Project Structure
-   `strategy_professional.py`: The core trading strategy logic, including entry and exit conditions based on confluence.
-   `config_professional.py`: Configuration settings for the strategy (e.g., leverage, fees, minimum confluence score).
-   `hold_exit_rules.py`: Defines the time-based position management and exit criteria.
-   `cvd_analyzer.py`: Module for calculating and interpreting Cumulative Volume Delta (CVD) indicators.
-   `liquidity_analyzer.py`: Module for identifying and analyzing liquidity zones (BSL, SSL, equal highs/lows, sweeps).
-   `market_structure.py`: Module for detecting market structure elements (BOS, CHOCH, order blocks, trend).
-   `indicators_professional.py`: Orchestrates the calculation of all necessary CVD, liquidity, and market structure indicators.
-   `backtester.py`: The engine for running historical simulations of the strategy and evaluating its performance.
-   `requirements.txt`: Python dependencies required to run the strategy and backtester.

## Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/nihalmirza448/crypto-trading-strategy.git
cd crypto-trading-strategy
```

### 2. Install Dependencies
Ensure you have Python 3.8+ installed.
```bash
pip install -r requirements.txt
```

### 3. Configure Strategy Parameters
Edit `config_professional.py` to adjust parameters such as leverage, capital, trading fees, and minimum confluence score according to your preferences.

### 4. Prepare Data
The backtester expects historical OHLCV data in CSV format, specifically `data/eth_usd_60m_1825d.csv` for the default configuration. You will need to collect your own historical data and place it in the `data/` directory.

**To collect historical data:**
You can use various cryptocurrency exchange APIs (e.g., Binance, Coinbase, Kraken) or data providers to download OHLCV data. Ensure your data includes at least the following columns: `timestamp`, `open`, `high`, `low`, `close`, `volume`. For advanced CVD calculations, including `taker_buy_volume` can enhance accuracy.

Example data collection libraries:
-   `ccxt` (Unified API for many exchanges)
-   `python-krakenex` (for Kraken-specific data)

Ensure your data files are named according to the `TIMEFRAME` and `LOOKBACK_DAYS` specified in `config_professional.py` (e.g., `eth_usd_60m_1825d.csv`).

### 5. Run Backtest
To run a backtest:
```bash
python backtester.py --strategy professional --leverage 20 --capital 10000
```
This will run the `ProfessionalStrategy` with specified parameters. Results will be printed to the console and can be extended to save to a file for detailed analysis.

## Metrics Used in Strategy
The strategy relies on a range of metrics generated by `cvd_analyzer.py`, `liquidity_analyzer.py`, and `market_structure.py`. These metrics form the basis of the confluence score:

### Cumulative Volume Delta (CVD) Metrics
-   `cvd`: Raw Cumulative Volume Delta, indicating net buying/selling pressure.
-   `cvd_slope`: Rate of change of CVD, showing momentum intensity.
-   `cvd_bullish_divergence`: Price makes a lower low while CVD makes a higher low.
-   `cvd_bearish_divergence`: Price makes a higher high while CVD makes a lower high.
-   `cvd_bullish_surge`: Strong increase in buying pressure.
-   `cvd_bearish_surge`: Strong increase in selling pressure.
-   `cvd_bullish_exhaustion`: Buying pressure waning after a strong rally.
-   `cvd_bearish_exhaustion`: Selling pressure waning after a strong decline.
-   `cvd_reset`: CVD returning to neutral, indicating market balance.

### Liquidity Metrics
-   `swing_high`, `swing_low`: Identified price swing points.
-   `bsl_level`: Buy-Side Liquidity levels (above swing highs).
-   `ssl_level`: Sell-Side Liquidity levels (below swing lows).
-   `equal_highs`, `equal_lows`: Multiple swing points at similar price levels, indicating major liquidity pools.
-   `bsl_sweep`: Price momentarily exceeds BSL and then reverses below it.
-   `ssl_sweep`: Price momentarily drops below SSL and then reverses above it.
-   `bsl_strength`, `ssl_strength`: Strength of liquidity zones based on touches and volume.
-   `liquidity_void`: Areas of low trading volume where price tends to move quickly.

### Market Structure Metrics
-   `structure_type`: Categorizes swing points as Higher High (HH), Higher Low (HL), Lower High (LH), Lower Low (LL).
-   `bullish_bos`: Bullish Break of Structure, indicating trend continuation.
-   `bearish_bos`: Bearish Break of Structure, indicating trend continuation.
-   `bullish_choch`: Bullish Change of Character, an early sign of a bearish-to-bullish trend reversal.
-   `bearish_choch`: Bearish Change of Character, an early sign of a bullish-to-bearish trend reversal.
-   `market_trend`: Overall trend direction (uptrend, downtrend, neutral) based on structure.
-   `structure_strength`: Consistency and reliability of the current market structure.
-   `bullish_ob_high`, `bullish_ob_low`: Price range of bullish order blocks.
-   `bearish_ob_high`, `bearish_ob_low`: Price range of bearish order blocks.
-   `bullish_ob_hold`: Price interacts with and holds a bullish order block.
-   `bearish_ob_hold`: Price interacts with and holds a bearish order block.

### Traditional Indicators (for context)
-   `ema_50`, `ema_100`, `ema_200`: Exponential Moving Averages for trend context.
-   `rsi`: Relative Strength Index, for identifying overbought/oversold conditions.
-   `atr`: Average True Range, for measuring volatility.
-   `bb_upper`, `bb_middle`, `bb_lower`, `bb_bandwidth`: Bollinger Bands for volatility context.

## Backtesting Agent
The `backtester.py` script serves as your backtesting agent. It allows you to simulate the Professional Trading Strategy on historical data with customizable parameters. 

**Usage:**
1.  **Prepare Data:** Ensure you have your historical OHLCV data (e.g., `eth_usd_60m_1825d.csv`) in the `data/` directory.
2.  **Configure Strategy:** Adjust parameters in `config_professional.py` as needed.
3.  **Run from command line:**
    ```bash
    python backtester.py --leverage <your_leverage> --capital <your_capital>
    ```
    Replace `<your_leverage>` and `<your_capital>` with your desired values. The script will output the backtest results directly to the console and save detailed metrics, trades, and equity curve to files in the `results/` directory.

## Disclaimer
Trading cryptocurrencies involves substantial risk and is not suitable for all investors. Past performance is not indicative of future results. Only risk capital you can afford to lose.
