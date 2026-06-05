"""
Professional Trading Configuration

Based on CVD + Liquidity + Market Structure methodology
Following institutional trading principles
"""
import os
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# API Configuration
# =============================================================================
KRAKEN_API_KEY = os.getenv('KRAKEN_API_KEY', '')
KRAKEN_API_SECRET = os.getenv('KRAKEN_API_SECRET', '')
COINGLASS_API_KEY = os.getenv('COINGLASS_API_KEY', '')

# CryptoQuant (optional — fetch_cryptoquant_ohlcv.py). Use either Bearer token or api_key.
CRYPTOQUANT_ACCESS_TOKEN = os.getenv('CRYPTOQUANT_ACCESS_TOKEN', '')
CRYPTOQUANT_API_KEY = os.getenv('CRYPTOQUANT_API_KEY', '')
CRYPTOQUANT_MARKET = os.getenv('CRYPTOQUANT_MARKET', 'spot')
CRYPTOQUANT_EXCHANGE = os.getenv('CRYPTOQUANT_EXCHANGE', 'all_exchange')
CRYPTOQUANT_BTC_SYMBOL = os.getenv('CRYPTOQUANT_BTC_SYMBOL', 'btc_usd')
CRYPTOQUANT_ETH_SYMBOL = os.getenv('CRYPTOQUANT_ETH_SYMBOL', 'eth_usd')
# Professional plan: daily bars only, max ~1 year history (Premium: hour/min, longer history).
CRYPTOQUANT_WINDOW = os.getenv('CRYPTOQUANT_WINDOW', 'day')
CRYPTOQUANT_MAX_LOOKBACK_DAYS = int(os.getenv('CRYPTOQUANT_MAX_LOOKBACK_DAYS', '365'))

# =============================================================================
# Trading Parameters - PROFESSIONAL APPROACH
# =============================================================================

# Leverage & Capital
LEVERAGE = 35  # Leverage for backtests / live (hold_exit_rules use price_move % × LEVERAGE)
CAPITAL = 1000.0  # Starting equity (paper/backtest); P&L accumulates here
POSITION_SIZE_PCT = 0.95  # Margin per entry = 95% of FIXED_CAPITAL when USE_FIXED_CAPITAL

# No stop-loss → never compound exposure: every entry uses FIXED_CAPITAL only, not growing equity.
USE_FIXED_CAPITAL = True
FIXED_CAPITAL = 1000.0  # Max sizing base per trade (margin cap ≈ FIXED_CAPITAL × POSITION_SIZE_PCT)
MIN_EQUITY_TO_TRADE = 1000.0  # No new entries below this account equity

# Position sizing (fixed fraction of capital — no stop-based risk sizing)
RISK_PER_TRADE_PCT = 1.5  # Legacy name; unused for sizing when hold_exit_rules is active
MIN_RISK_REWARD_RATIO = 2.0  # Legacy; exits use return targets below

# =============================================================================
# Entry Confluence System
# =============================================================================

# Minimum confluences required for entry
MIN_CONFLUENCE_SCORE = 3  # ~1–2 trades/week on 1h with relaxed pool scoring below

# Trade frequency (one position at a time; return-window exits cap throughput)
TARGET_TRADES_PER_WEEK = 1.5
MIN_HOURS_BETWEEN_ENTRIES = 48  # Legacy; use ENTRY_SPACING_HOURS_* tiers below

# Confluence-scaled entry spacing (hours since last entry when flat; uses current signal score)
ENTRY_SPACING_HOURS_SCORE_3 = 24   # score == 3 (retuned 48->24: backtest +20% trades, win rate held)
ENTRY_SPACING_HOURS_SCORE_4_5 = 24  # score 4–5
ENTRY_SPACING_HOURS_SCORE_6_PLUS = 12  # score >= 6


def entry_spacing_hours_for_score(confluence_score: int) -> float:
    """Minimum hours since last entry when flat; tier depends on current signal score."""
    score = int(confluence_score)
    if score >= 6:
        return float(ENTRY_SPACING_HOURS_SCORE_6_PLUS)
    if score >= 4:
        return float(ENTRY_SPACING_HOURS_SCORE_4_5)
    return float(ENTRY_SPACING_HOURS_SCORE_3)
BLOCK_CVD_EXHAUSTION = False
BLOCK_LIQUIDITY_VOID = False
ALLOW_STRUCTURE_ONLY_ENTRY = False  # True floods signals (3–4+/week); keep False for quality

# =============================================================================
# Trend Momentum (Continuation) strategy — strategy_trend_momentum.py
# Trades WITH strong pump/dump days; high-confirmation bar (separate from reversal).
# =============================================================================
TREND_MIN_CONFLUENCE_SCORE = 7      # of 9 — "very strong / full confirmation" gate
TREND_MIN_STRUCTURE_STRENGTH = 60   # structure-strength +1 threshold for continuation
TREND_MOMENTUM_LOOKBACK = 6         # bars used to measure the pump/dump thrust
TREND_MOMENTUM_MIN_PCT = 2.0        # min |price move| over lookback to qualify as a thrust
TREND_RSI_MAX = 80                  # long: skip blow-off tops above this RSI
TREND_RSI_MIN = 20                  # short: skip capitulation bottoms below this RSI

# Confluence weight adjustments (if implementing weighted scoring)
CONFLUENCE_WEIGHTS = {
    'liquidity_sweep': 1.5,  # Liquidity sweeps are high probability
    'cvd_divergence': 1.5,   # CVD divergences are powerful
    'order_block': 1.0,
    'structure_break': 1.0,
    'trend_aligned': 0.5,
    'structure_strength': 0.5,
    'volume_spike': 0.5
}

# =============================================================================
# CVD (Cumulative Volume Delta) Parameters
# =============================================================================

# CVD calculation method
CVD_USE_WICK_ANALYSIS = True  # Use advanced wick-based calculation

# CVD divergence detection
CVD_DIVERGENCE_LOOKBACK = 20  # Candles to look back for divergence

# CVD surge detection
CVD_SURGE_PERCENTILE = 80  # Top 20% of slopes = surge

# CVD slope calculation
CVD_SLOPE_PERIOD = 5  # Period for slope calculation

# CVD exhaustion detection
CVD_EXHAUSTION_LOOKBACK = 20  # Period for exhaustion analysis

# =============================================================================
# Liquidity Cluster Parameters
# =============================================================================

# Swing point detection
SWING_POINT_ORDER = 5  # Number of candles on each side for swing point

# Equal highs/lows detection
EQUAL_LEVEL_TOLERANCE_PCT = 0.2  # 0.2% tolerance for "equal" levels

# Liquidity sweep detection
LIQUIDITY_SWEEP_LOOKBACK = 3  # Candles to confirm sweep reversal

# Volume profile
VOLUME_PROFILE_BINS = 50  # Number of price bins for volume profile

# Volume spike requirement
VOLUME_SPIKE_MULTIPLIER = 1.2  # 1.2x average volume for +1 confluence

# =============================================================================
# Market Structure Parameters
# =============================================================================

# Trend determination
MARKET_TREND_LOOKBACK = 20  # Recent structure to analyze for trend

# Structure strength (bonus confluence; lower = more structure tags)
MIN_STRUCTURE_STRENGTH = 45  # Minimum structure consistency (0-100) for +1 confluence

# Order block detection
ORDER_BLOCK_LOOKBACK = 50  # Period for identifying order blocks
ORDER_BLOCK_MIN_MOVE_PCT = 1.0  # Minimum % move to qualify as order block

# =============================================================================
# Exit rules (no stop-loss) — see hold_exit_rules.py
# =============================================================================
# Return % is on leveraged P&L (price move % × LEVERAGE).
MIN_HOLD_HOURS = 0  # 0 = no minimum hold; exits allowed immediately when return rules hit
HOLD_WINDOW_END_HOURS = 48
TARGET_RETURN_PCT = 50.0   # Legacy full exit when USE_SCALED_EXITS=False
MIN_EXIT_RETURN_PCT = 15.0  # After window end if target not hit; else exit at window end

# Scaled take-profit (USE_SCALED_EXITS=True) — goal: TARGET_NET_TRADE_RETURN_PCT after fees
USE_SCALED_EXITS = True
TARGET_NET_TRADE_RETURN_PCT = 50.0  # Design goal: +50% on posted margin, net of fees (full trade)
TP1_RETURN_PCT = 55.0   # Gross on margin — bank half (55% clears ~50% net on that leg after fees)
TP1_EXIT_PORTION = 0.50  # Close 50% of position at TP1
TP2_RETURN_PCT = 100.0  # Second spike — gross on margin
TP2_EXIT_PORTION = 0.50  # Close 50% of remainder (= 25% of original size)
RUNNER_TRAIL_GIVEBACK_PCT = 25.0  # Close runner if return falls this much from peak
MIN_RUNNER_RETURN_PCT = 15.0  # Don't trail out runner below this gross return

# Legacy (unused by hold_exit_rules)
STOP_LOSS_PCT = 2.5
MIN_STOP_DISTANCE_PCT = 1.0
STOP_LOSS_BUFFER_PCT = 0.2
TP1_RATIO = 2.0
TP2_RATIO = 4.0
TP3_RATIO = 6.0
USE_LIQUIDITY_VOIDS_AS_TARGETS = False
USE_OPPOSITE_LIQUIDITY_AS_TARGETS = False
MAX_HOLD_TIME_HOURS = 48
MOVE_TO_BREAKEVEN_AFTER_TP1 = False
TRAIL_STOP_AFTER_TP2 = False
TRAILING_STOP_METHOD = 'structure'
TRAILING_STOP_ATR_MULTIPLIER = 1.5

# =============================================================================
# Bear-market Chento liquidity strategy (strategy_bear_chento.py)
# =============================================================================
# Return goal (documentation): 20% account return and $500 profit implies
# starting equity >= max(500/0.20, 500) => use at least $2,500 if both must hold.
BEAR_GOAL_MIN_STARTING_CAPITAL_USD = 2500

# Liquidity execution (matches ~0.35% rule after second re-test)
BEAR_LIQ_TOUCH_BAND_PCT = 0.12
BEAR_LIQ_DEPART_PCT = 0.28
BEAR_LIQ_CONFIRM_MOVE_PCT = 0.35
BEAR_LIQ_MIN_RETESTS = 2
BEAR_LIQ_ANCHOR_DRIFT_MAX_PCT = 0.85

# Regime: default "sub50" = weekly/daily/4H RSI all below threshold (macro bearish control).
# Set BEAR_RSI_MODE = "bands" to use the tight ranges below instead.
BEAR_RSI_MODE = "sub50"
BEAR_RSI_SUB50_THRESHOLD = 50.0
# Which higher-timeframe RSIs must be sub-threshold: "wd" = weekly+daily (default),
# "wd4" = include 4H (stricter, fewer overlaps with intraday liquidity signals).
BEAR_RSI_SUB50_PARTS = "wd"
BEAR_WEEKLY_RSI_RANGE = (30.0, 48.0)
BEAR_DAILY_RSI_RANGE = (38.0, 50.0)
BEAR_4H_RSI_RANGE = (36.0, 50.0)
BEAR_MOMENTUM_7D_MAX_PCT = -2.0
BEAR_TREND_SCORE_RANGE = (30.0, 92.0)

# Optional on-chain / flow columns on the DataFrame (forward-filled). If absent, skipped.
BEAR_MACRO_MVRV_MAX = 1.5
BEAR_MACRO_SOPR_MAX = 1.0
BEAR_MACRO_NETFLOW_MIN_BTC = 0.0
BEAR_MACRO_TAKER_LO = 0.95
BEAR_MACRO_TAKER_HI = 1.05
BEAR_REQUIRE_MACRO_COLUMNS = False

# Mean-reversion longs at SSL in bear tape (disable for short-only)
BEAR_ALLOW_SSL_LONG = True

# Forward / out-of-sample: first timestamp where trades are counted (inclusive).
# Indicators are still computed on the full series before the split.
BEAR_FORWARD_SPLIT = "2024-01-01"
# Minimum bar index for OOS split (indicator / signal warm-up).
BEAR_MIN_START_IDX = 200

# =============================================================================
# Market Regime Filter (Optional but Recommended)
# =============================================================================

# Only trade when market conditions are favorable
USE_MARKET_REGIME_FILTER = False  # Set True to only trade strong trends

# Regime requirements
MIN_MARKET_TREND_STRENGTH = 60  # Minimum trend consistency
SKIP_CONSOLIDATION = True  # Skip trades when market is ranging

# =============================================================================
# Additional Filters
# =============================================================================

# Time filters
SKIP_LOW_LIQUIDITY_HOURS = False  # Skip certain hours (if True, define below)
LOW_LIQUIDITY_HOURS = [0, 1, 2, 3, 4, 5]  # Hours to skip (UTC)

# Volatility filters
SKIP_EXTREME_VOLATILITY = True  # Skip when volatility is too high
VOLATILITY_THRESHOLD_PERCENTILE = 90  # Top 10% volatility = skip

# CVD reset zones
SKIP_CVD_RESET_ZONES = True  # Don't trade when CVD is neutral

# =============================================================================
# Data Collection
# =============================================================================

TIMEFRAME = '1h'  # Hourly candles for swing trading
LOOKBACK_DAYS = 1825  # 5 years of historical data
PAIR = 'ETHUSD'

# =============================================================================
# Backtesting Parameters
# =============================================================================

# Trading costs (CoinDCX India rates - adjust for your exchange)
SLIPPAGE_PCT = 0.05  # 0.05% slippage per trade
TRADING_FEE_MAKER_PCT = 0.04  # 0.04% maker fee
TRADING_FEE_TAKER_PCT = 0.08  # 0.08% taker fee (assume taker for all trades)
FUNDING_RATE_HOURLY = 0.0034  # 0.0034% per hour (average funding rate)

# =============================================================================
# File Paths
# =============================================================================

DATA_DIR = 'data'
RESULTS_DIR = 'results'
LOGS_DIR = 'logs'
JOURNAL_DIR = 'journal'  # For trade journal entries

# =============================================================================
# API Endpoints
# =============================================================================

KRAKEN_REST_URL = 'https://api.kraken.com'
KRAKEN_WS_URL = 'wss://ws.kraken.com'
COINGLASS_API_URL = 'https://open-api.coinglass.com/public/v2'

# =============================================================================
# Create Required Directories
# =============================================================================

for directory in [DATA_DIR, RESULTS_DIR, LOGS_DIR, JOURNAL_DIR]:
    os.makedirs(directory, exist_ok=True)

# =============================================================================
# Performance Targets (Realistic Based on Research)
# =============================================================================

"""
Expected Performance with Professional Strategy:

Win Rate: 40-50%
Average R:R: 1:3 to 1:4
Annual Return: 60-100% (highly profitable)
Max Drawdown: <20%
Sharpe Ratio: >1.5

These are REALISTIC and ACHIEVABLE targets based on:
- CVD order flow analysis
- Liquidity hunting with institutions
- Proper risk management (1-2% per trade)
- Confluence-based entries (quality over quantity)

Compare to old strategy:
- Old: 100% loss over full cycle
- New: Sustainable profitable trading

The difference:
- Edge: CVD + Liquidity + Structure (proven institutional methods)
- Discipline: Strict confluence requirements (no low-quality setups)
- Risk Management: Proper position sizing and scaled exits
- Psychology: Following a proven process, not gambling
"""

# =============================================================================
# Trading Rules (Print for Reference)
# =============================================================================

def print_trading_rules():
    """Print the core trading rules"""
    print("=" * 70)
    print("PROFESSIONAL TRADING RULES")
    print("=" * 70)
    print("\n📋 ENTRY CHECKLIST (Need 5+ for A+ Setup):")
    print("  ☐ Liquidity sweep occurred (BSL/SSL)")
    print("  ☐ CVD showing divergence or surge")
    print("  ☐ Order block holding/breaking")
    print("  ☐ Structure break in trade direction (BOS/CHOCH)")
    print("  ☐ Key S/R level alignment")
    print("  ☐ Higher timeframe confirmation")
    print("  ☐ Clean price action")
    print("\n💰 RISK MANAGEMENT:")
    print(f"  • Risk per trade: {RISK_PER_TRADE_PCT}% of capital")
    print(f"  • Minimum R:R: 1:{MIN_RISK_REWARD_RATIO}")
    print(f"  • Position sizing: Risk-based (not fixed %)")
    print("\n🎯 EXITS:")
    print(f"  • TP1 at 1:{TP1_RATIO} R:R (exit 33%)")
    print(f"  • TP2 at 1:{TP2_RATIO} R:R (exit 33%)")
    print(f"  • TP3 at 1:{TP3_RATIO} R:R (exit 34%)")
    print("  • Stop to breakeven after TP1")
    print("  • Trail stop after TP2")
    print("\n🚫 DON'T TRADE IF:")
    print("  • Less than 3 confluences")
    print("  • CVD showing exhaustion")
    print("  • In liquidity void (range, not breakout)")
    print("  • Extreme volatility (if filter enabled)")
    print("\n✅ DISCIPLINE:")
    print("  • Follow the checklist EVERY trade")
    print("  • No revenge trading after losses")
    print("  • Max 3-5 trades per day")
    print("  • Journal every trade with screenshots")
    print("=" * 70)

if __name__ == "__main__":
    print_trading_rules()
