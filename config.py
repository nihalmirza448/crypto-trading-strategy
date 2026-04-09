"""
Configuration settings for the Ethereum swing trading system
"""
import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
KRAKEN_API_KEY = os.getenv('KRAKEN_API_KEY', '')
KRAKEN_API_SECRET = os.getenv('KRAKEN_API_SECRET', '')

# Trading Parameters
LEVERAGE = 8  # 8x leverage (conservative for daily candles)
CAPITAL = 7500  # Starting capital in USD
POSITION_SIZE_PCT = 0.95  # Use 95% of capital per trade (aggressive)

# MARKET REGIME FILTER
USE_MARKET_REGIME_FILTER = False  # Disabled for 66% win rate config
MARKET_REGIME_SMA = 100  # 100-period SMA for regime detection
REGIME_BUFFER_PCT = 2.0  # 2% buffer to avoid whipsaws at regime boundary

# Strategy Parameters - VERY HIGH FREQUENCY (100+ Trades/Year Target)
MOMENTUM_THRESHOLD_1H = 0.3  # Very low threshold (was 0.5%)
VOLUME_SPIKE_MULTIPLIER = 1.0  # No volume requirement (was 1.2x)
RSI_OVERBOUGHT = 90  # Very wide range (was 85)
RSI_OVERSOLD = 10  # Very wide range (was 15)

# RSI Filters (Disabled for original config)
RSI_14_MIN = 0  # Disabled
RSI_30_MIN = 0  # Disabled
RSI_30_MAX = 100  # Disabled

# BEAR MARKET STRATEGY (Relaxed for High Frequency)
BEAR_MOMENTUM_THRESHOLD = 0.5  # Lower threshold (was 1.8)
BEAR_VOLUME_SPIKE_MULTIPLIER = 1.0  # No volume requirement (was 2.0)
BEAR_RSI_OVERBOUGHT = 80  # More lenient (was 68)
BEAR_RSI_OVERSOLD = 20  # More lenient (was 32)
BEAR_REQUIRE_LOWER_HIGHS = False  # DISABLED (was True)

# SMA Trend Following (Adjusted for 4-Hour Candles)
USE_SMA_TREND = False  # DISABLED - No SMA crossover exits
SMA_PERIODS = [60, 90, 180]  # Back to original periods for 4h timeframe
REQUIRE_ALL_SMAS = True  # Require all SMAs aligned
SMA_BUFFER_PCT = 0.2  # 0.2% buffer to avoid whipsaws

# ENTRY FILTERS - HIGH FREQUENCY (100+ Trades Target)
REQUIRE_BREAKOUT = False  # DISABLED - too restrictive
REQUIRE_PULLBACK = False  # DISABLED - too restrictive  
PULLBACK_SMA = 60  # Reference SMA for pullback detection
PULLBACK_TOLERANCE_PCT = 2.5  # Within 2.5% of SMA
MIN_BOUNCE_PCT = 0.4  # Require 0.4% bounce confirmation
MIN_VOLATILITY_FILTER = False  # DISABLED - was blocking too many trades
VOLATILITY_PERCENTILE = 0.40  # Lower to top 60% (was 0.60)
VOLATILITY_LOOKBACK = 6  # Hours to calculate volatility

# QUALITY ENTRY TYPES (More Inclusive for High Frequency)
ENABLE_BREAKOUT_ENTRIES = True  # Strong momentum breakouts
ENABLE_REVERSAL_ENTRIES = True  # Extreme reversals
ENABLE_TREND_FOLLOWING = True  # ENABLED for more trades

# ADDITIONAL QUALITY FILTERS (Minimal for High Frequency)
REQUIRE_MULTIPLE_CONFIRMATIONS = False  # Allow single signal
MIN_RISK_REWARD_RATIO = 1.0  # Lowered from 1.5 to 1.0 (any positive RR)

# Consolidation Handling (Original Config)
CONSOLIDATION_THRESHOLD = 0.3  # If moves < 0.3% = consolidating
CONSOLIDATION_EXIT = False  # DISABLED - Let trades run to stop/target

# Risk Management - HIGH FREQUENCY (4-Hour Candles)
STOP_LOSS_PCT = 1.5  # 1.5% stop = 12% loss on 8x leverage
TAKE_PROFIT_PCT = 3.0  # 3.0% target = 24% gain on 8x leverage (2:1 RR)
MAX_HOLD_TIME_HOURS = 72  # Max 3 days hold (72 hours)

# Risk Management - BEAR MARKETS (4-Hour Candles)
BEAR_STOP_LOSS_PCT = 1.5  # Same as bull market
BEAR_TAKE_PROFIT_PCT = 3.0  # Same as bull market (2:1 RR)
BEAR_MAX_HOLD_TIME_HOURS = 72  # Max 3 days hold

# Exit Conditions (Original Config)
VOLATILITY_CONTRACTION_THRESHOLD = 999  # DISABLED - Let trades run
VOLUME_DRYUP_THRESHOLD = 999  # DISABLED - Let trades run
MOMENTUM_REVERSAL_THRESHOLD = 999  # DISABLED - Let trades run to stop/target

# Data Collection
TIMEFRAME = '4h'  # 4-hour candles for more trade frequency
LOOKBACK_DAYS = 1825  # 5 years of historical data
PAIR = 'ETHUSD'

# Backtesting
SLIPPAGE_PCT = 0.05  # 0.05% slippage per trade
TRADING_FEE_MAKER_PCT = 0.04  # CoinDCX India maker fee
TRADING_FEE_TAKER_PCT = 0.08  # CoinDCX India taker fee
FUNDING_RATE_HOURLY = 0.0034  # 0.0034% per hour funding rate

# Files
DATA_DIR = 'data'
RESULTS_DIR = 'results'
LOGS_DIR = 'logs'

# Kraken API Endpoints
KRAKEN_REST_URL = 'https://api.kraken.com'
KRAKEN_WS_URL = 'wss://ws.kraken.com'

# Create directories if they don't exist
for directory in [DATA_DIR, RESULTS_DIR, LOGS_DIR]:
    os.makedirs(directory, exist_ok=True)
