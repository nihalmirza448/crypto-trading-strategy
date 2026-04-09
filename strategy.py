"""
Precision trend-following strategy for Ethereum
High-quality setups only - targeting 8-10 trades per month
"""
import pandas as pd
import numpy as np
import config
from indicators import TechnicalIndicators

class MomentumSwingStrategy:
    """
    DUAL DIRECTION STRATEGY (5x Leverage)
    
    TARGET: 1-2 trades per week
    FOCUS: Quality over Quantity - LONGS and SHORTS
    
    TRADING RULES:
    ========================================
    ✅ Trade LONG when price > 100 SMA (bull market)
    ✅ Trade SHORT when price < 100 SMA (bear market)
    🔄 Both directions enabled
    
    ENTRY REQUIREMENTS:
    ========================================
    - RSI(14) > 50
    - RSI(30) > 41 AND < 72
    - Volume spike > 1.5x
    - All SMAs aligned (60, 90, 180)
    - No volatility filter
    
    ENTRY TYPES (Both Directions):
    ========================================
    
    1️⃣ HIGH-QUALITY PULLBACK:
    - Price pulls back to SMA60 (within 2.5%)
    - Strong bounce confirmation (0.4%+)
    - All SMAs aligned
    - High volume (>1.5x average)
    - Momentum > 1.0%
    
    2️⃣ STRONG BREAKOUT:
    - Momentum > 1.0%
    - Volume spike > 1.5x
    - RSI conditions met
    
    3️⃣ EXTREME REVERSAL:
    - RSI < 28 (deeply oversold)
    - Strong momentum reversal
    - High volume confirmation
    
    Exit Conditions:
    - Take profit: 7% (35% gain at 5x leverage)
    - Stop loss: 3.5% (17.5% loss at 5x leverage)
    - Risk/Reward: 2:1
    - Maximum hold: 6 hours
    - Exit if consolidation detected
    - Exit if price crosses 100 SMA (regime change)
    
    📊 Leverage: 5x
    🎯 Target Win Rate: 40-50%
    🎯 Target Frequency: 1-2 trades/week
    💰 Strategy: Long and Short based on 100 SMA
    """
    
    def __init__(self, leverage=5, capital=7500):
        self.leverage = leverage
        self.capital = capital
        self.position = None
        self.entry_price = 0
        self.entry_time = None
        self.entry_volume = 0
        self.entry_volatility = 0
        self.entry_momentum = 0
        self.entry_sma_ref = 0
        self.entry_regime = None  # Track market regime at entry
        
    def check_entry_conditions(self, df, idx):
        """
        DUAL DIRECTION ENTRY STRATEGY - Longs and Shorts
        
        Focus: High probability setups in both directions
        Based on 100 SMA regime
        
        Returns:
            tuple: (should_enter, direction) where direction is 1 (long) or -1 (short)
        """
        if idx < 100:  # Need enough data for 100-period SMA
            return False, 0
        
        row = df.iloc[idx]
        
        # Get current market state
        current_price = row['close']
        price_change_1h = row['momentum_1h']
        sma_100 = row.get('sma_100', None)
        sma_60 = row['sma_60']
        sma_90 = row['sma_90']
        sma_180 = row['sma_180']
        
        # Check data availability
        if pd.isna(sma_100) or pd.isna(sma_60) or pd.isna(sma_90) or pd.isna(sma_180):
            return False, 0
        
        # RSI FILTERS - MUST PASS BOTH
        rsi_14 = row.get('rsi_14', row['rsi'])
        rsi_30 = row.get('rsi_30', None)
        
        if pd.isna(rsi_14) or pd.isna(rsi_30):
            return False, 0
        
        # Check RSI conditions
        if rsi_14 <= config.RSI_14_MIN:
            return False, 0  # RSI(14) must be > 50
        
        if rsi_30 <= config.RSI_30_MIN or rsi_30 >= config.RSI_30_MAX:
            return False, 0  # RSI(30) must be 41 < RSI < 72
        
        # MARKET REGIME FILTER - 100 SMA
        if config.USE_MARKET_REGIME_FILTER:
            regime_buffer = config.REGIME_BUFFER_PCT / 100
            
            is_bull_market = current_price > sma_100 * (1 + regime_buffer)
            is_bear_market = current_price < sma_100 * (1 - regime_buffer)
            
            if not is_bull_market and not is_bear_market:
                return False, 0  # Neutral zone
        else:
            is_bull_market = current_price > sma_100
            is_bear_market = current_price < sma_100
        
        # VOLATILITY FILTER - REMOVED (not checking)
        # No volatility filter per user request
        
        # VOLUME FILTER - Require strong volume
        if row['volume_spike'] < config.VOLUME_SPIKE_MULTIPLIER:
            return False, 0
        
        # Determine direction based on regime
        if is_bull_market:
            direction = 1  # LONG
        elif is_bear_market:
            direction = -1  # SHORT
        else:
            return False, 0
        
        # ========================================================================
        # ENTRY LOGIC (Same for both directions, just inverted)
        # ========================================================================
        
        # STRICT SMA ALIGNMENT - All SMAs must be aligned
        if config.USE_SMA_TREND and config.REQUIRE_ALL_SMAS:
            buffer_divider = 1 - (config.SMA_BUFFER_PCT / 100)
            buffer_multiplier = 1 + (config.SMA_BUFFER_PCT / 100)
            
            if direction == 1:  # Long - price above SMAs
                if not (current_price > sma_60 * buffer_divider and
                        current_price > sma_90 * buffer_divider and
                        current_price > sma_180 * buffer_divider):
                    return False, 0
            else:  # Short - price below SMAs
                if not (current_price < sma_60 * buffer_multiplier and
                        current_price < sma_90 * buffer_multiplier and
                        current_price < sma_180 * buffer_multiplier):
                    return False, 0
        
        entry_signals = 0  # Count confirmation signals
        
        # ENTRY TYPE 1: HIGH-QUALITY PULLBACK
        if config.REQUIRE_PULLBACK:
            dist_from_sma60 = abs((current_price - sma_60) / sma_60 * 100)
            bounce_pct = row.get('bounce_from_low_pct', 0)
            
            if direction == 1:  # Long pullback
                is_pullback = (
                    dist_from_sma60 < config.PULLBACK_TOLERANCE_PCT and
                    bounce_pct > config.MIN_BOUNCE_PCT and
                    price_change_1h > config.MOMENTUM_THRESHOLD_1H * 0.5 and
                    row['rsi'] > 40  # Not too low
                )
            else:  # Short pullback (rally into resistance)
                is_pullback = (
                    dist_from_sma60 < config.PULLBACK_TOLERANCE_PCT and
                    price_change_1h < -config.MOMENTUM_THRESHOLD_1H * 0.5  # Negative momentum
                )
            
            if is_pullback:
                entry_signals += 1
        
        # ENTRY TYPE 2: STRONG BREAKOUT
        if config.ENABLE_BREAKOUT_ENTRIES:
            if direction == 1:  # Long breakout
                is_breakout = (
                    price_change_1h > config.MOMENTUM_THRESHOLD_1H and
                    row['rsi'] > 50 and
                    row['volume_spike'] > config.VOLUME_SPIKE_MULTIPLIER * 1.2
                )
            else:  # Short breakout (breakdown)
                is_breakout = (
                    price_change_1h < -config.MOMENTUM_THRESHOLD_1H and
                    row['volume_spike'] > config.VOLUME_SPIKE_MULTIPLIER * 1.2
                )
            
            if is_breakout:
                entry_signals += 1
        
        # ENTRY TYPE 3: EXTREME REVERSAL
        if config.ENABLE_REVERSAL_ENTRIES:
            if direction == 1:  # Long reversal
                is_reversal = (
                    row['rsi'] < config.RSI_OVERSOLD and
                    price_change_1h > config.MOMENTUM_THRESHOLD_1H * 0.8 and
                    row['volume_spike'] > config.VOLUME_SPIKE_MULTIPLIER * 1.3
                )
            else:  # Short reversal
                is_reversal = (
                    row['rsi'] > 72 and  # Overbought
                    price_change_1h < -config.MOMENTUM_THRESHOLD_1H * 0.8 and
                    row['volume_spike'] > config.VOLUME_SPIKE_MULTIPLIER * 1.3
                )
            
            if is_reversal:
                entry_signals += 2  # Weight extreme reversals higher
        
        # REQUIRE SIGNALS for quality
        if config.REQUIRE_MULTIPLE_CONFIRMATIONS:
            if entry_signals >= 2:
                return True, direction
        else:
            if entry_signals >= 1:
                return True, direction
        
        return False, 0
    
    def check_exit_conditions(self, df, idx):
        """
        Check exit conditions for LONG and SHORT positions
        
        Returns:
            tuple: (should_exit, reason)
        """
        if self.position is None:
            return False, None
        
        row = df.iloc[idx]
        current_price = row['close']
        sma_100 = row.get('sma_100', None)
        
        # Calculate P&L based on position direction
        if self.position == 1:  # Long
            pnl_pct = ((current_price - self.entry_price) / self.entry_price) * 100
        else:  # Short
            pnl_pct = ((self.entry_price - current_price) / self.entry_price) * 100
        
        # Use regime-specific exit parameters
        if self.entry_regime == 'bull':
            stop_loss = config.STOP_LOSS_PCT
            take_profit = config.TAKE_PROFIT_PCT
            max_hold_time = config.MAX_HOLD_TIME_HOURS
        elif self.entry_regime == 'bear':
            stop_loss = config.BEAR_STOP_LOSS_PCT
            take_profit = config.BEAR_TAKE_PROFIT_PCT
            max_hold_time = config.BEAR_MAX_HOLD_TIME_HOURS
        else:
            # Default
            stop_loss = config.STOP_LOSS_PCT
            take_profit = config.TAKE_PROFIT_PCT
            max_hold_time = config.MAX_HOLD_TIME_HOURS
        
        # 0. REGIME CHANGE - Exit if crosses 100 SMA
        if config.USE_MARKET_REGIME_FILTER and pd.notna(sma_100):
            if self.position == 1:  # Long position
                if current_price < sma_100:
                    return True, 'regime_change_bearish'
            elif self.position == -1:  # Short position
                if current_price > sma_100:
                    return True, 'regime_change_bullish'
        
        # 1. Stop Loss
        if pnl_pct <= -stop_loss:
            return True, 'stop_loss'
        
        # 2. Take Profit
        if pnl_pct >= take_profit:
            return True, 'take_profit'
        
        # 3. Maximum hold time
        time_held_hours = (row['timestamp'] - self.entry_time).total_seconds() / 3600
        if time_held_hours >= max_hold_time:
            return True, 'max_hold_time'
        
        # 4. Consolidation detected - EXIT if enabled
        if config.CONSOLIDATION_EXIT:
            if pd.notna(row['is_consolidating']) and row['is_consolidating']:
                return True, 'consolidation_detected'
        
        # 5. SMA Crossover - price crosses back through SMA60
        if config.USE_SMA_TREND and self.entry_sma_ref > 0:
            sma_60 = row['sma_60']
            
            if self.position == 1:  # Long position
                if current_price < sma_60 * 0.998:
                    return True, 'sma_crossover'
            elif self.position == -1:  # Short position
                if current_price > sma_60 * 1.002:
                    return True, 'sma_crossover'
        
        # 6. Momentum reversal
        current_momentum = row['momentum_1h']
        if self.position == 1:
            if current_momentum < -config.MOMENTUM_REVERSAL_THRESHOLD:
                return True, 'momentum_reversal'
        elif self.position == -1:
            if current_momentum > config.MOMENTUM_REVERSAL_THRESHOLD:
                return True, 'momentum_reversal'
        
        # 7. Volatility contraction
        if pd.notna(row['bb_bandwidth']) and pd.notna(self.entry_volatility):
            if self.entry_volatility > 0:
                volatility_change = (row['bb_bandwidth'] - self.entry_volatility) / self.entry_volatility
                if volatility_change < -config.VOLATILITY_CONTRACTION_THRESHOLD:
                    return True, 'volatility_contraction'
        
        return False, None
    
    def enter_position(self, df, idx, direction):
        """Enter a precision position"""
        row = df.iloc[idx]
        self.position = direction
        self.entry_price = row['close']
        self.entry_time = row['timestamp']
        self.entry_volume = row['volume']
        self.entry_volatility = row['bb_bandwidth'] if pd.notna(row['bb_bandwidth']) else 0
        self.entry_momentum = row['momentum_1h']
        self.entry_sma_ref = row['sma_60']  # Store SMA60 as reference
        self.entry_regime = row.get('market_regime', 'neutral')  # Store regime
        
        return {
            'timestamp': row['timestamp'],
            'action': 'ENTER',
            'direction': 'LONG' if direction == 1 else 'SHORT',
            'price': self.entry_price,
            'leverage': self.leverage,
            'position_size': self.capital * self.leverage,
            'volume_spike': row['volume_spike'],
            'momentum_1h': row['momentum_1h'],
            'rsi': row['rsi'],
            'volatility': self.entry_volatility,
            'sma_60': row['sma_60'],
            'sma_180': row['sma_180'],
            'sma_200': row.get('sma_200', None),
            'market_regime': self.entry_regime,
            'is_trending': row.get('is_trending', False)
        }
    
    def exit_position(self, df, idx, reason):
        """Exit current position (long or short)"""
        row = df.iloc[idx]
        exit_price = row['close']
        
        # Calculate P&L based on direction
        if self.position == 1:  # Long
            pnl_pct = ((exit_price - self.entry_price) / self.entry_price) * 100
        else:  # Short
            pnl_pct = ((self.entry_price - exit_price) / self.entry_price) * 100
        
        # Apply leverage
        pnl_pct_leveraged = pnl_pct * self.leverage
        pnl_dollar = self.capital * (pnl_pct_leveraged / 100)
        
        # Apply fees and slippage (CoinDCX India rates)
        # Assume taker fees (market orders)
        fees = self.capital * self.leverage * (config.TRADING_FEE_TAKER_PCT / 100) * 2  # Entry + exit
        slippage = self.capital * self.leverage * (config.SLIPPAGE_PCT / 100) * 2
        
        # Calculate funding costs
        hold_time_hours = (row['timestamp'] - self.entry_time).total_seconds() / 3600
        funding_cost = self.capital * self.leverage * config.FUNDING_RATE_HOURLY * hold_time_hours
        
        net_pnl = pnl_dollar - fees - slippage - funding_cost
        
        trade_result = {
            'timestamp': row['timestamp'],
            'action': 'EXIT',
            'direction': 'LONG' if self.position == 1 else 'SHORT',
            'entry_price': self.entry_price,
            'exit_price': exit_price,
            'pnl_pct': pnl_pct,
            'pnl_pct_leveraged': pnl_pct_leveraged,
            'pnl_dollar': pnl_dollar,
            'fees': fees,
            'slippage': slippage,
            'funding_cost': funding_cost,
            'net_pnl': net_pnl,
            'hold_time_hours': hold_time_hours,
            'exit_reason': reason
        }
        
        # Update capital
        self.capital += net_pnl
        
        # Reset position
        self.position = None
        self.entry_price = 0
        self.entry_time = None
        
        return trade_result
    
    def run(self, df):
        """
        Run strategy on historical data
        
        Args:
            df: DataFrame with OHLCV data and indicators
            
        Returns:
            list: List of all trades executed
        """
        trades = []
        
        for idx in range(len(df)):
            if self.position is None:
                # Look for entry
                should_enter, direction = self.check_entry_conditions(df, idx)
                if should_enter:
                    entry = self.enter_position(df, idx, direction)
                    trades.append(entry)
            else:
                # Look for exit
                should_exit, reason = self.check_exit_conditions(df, idx)
                if should_exit:
                    exit_trade = self.exit_position(df, idx, reason)
                    trades.append(exit_trade)
        
        return trades

def test_strategy():
    """Test the strategy with sample data"""
    print("Strategy test - use backtester.py for full backtesting")

if __name__ == "__main__":
    test_strategy()
