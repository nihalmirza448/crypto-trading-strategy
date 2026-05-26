"""
Professional Trading Strategy - CVD + Liquidity + Market Structure

Based on institutional trading methodology:
- CVD analysis for order flow
- Liquidity cluster hunting
- Market structure confirmation
- Confluence-based entries (minimum 3 confirmations)
- Time-based exits: 50% return by 48h, else 15%+ (no stop-loss; no minimum hold)
"""

import pandas as pd
import numpy as np
from hold_exit_rules import fixed_position_size, min_equity_to_trade, should_exit

try:
    import config_professional as config
except ImportError:
    import config


class ProfessionalStrategy:
    """
    Professional trading strategy using CVD, liquidity, and market structure

    Entry Requirements (Need 5+ for A+ setup):
    ☐ Liquidity sweep occurred (BSL/SSL)
    ☐ CVD showing divergence or surge
    ☐ Order block holding/breaking
    ☐ Structure break in trade direction (BOS/CHOCH)
    ☐ Key S/R level alignment
    ☐ Higher timeframe confirmation
    ☐ Clean price action

    Exits (hold_exit_rules):
    - No stop-loss; fixed position size (POSITION_SIZE_PCT of capital)
    - No minimum hold; target 50% leveraged return within 48h; else exit at 15%+ or at 48h
    """

    def __init__(self, leverage=5, capital=7500, risk_pct=1.5):
        self.leverage = leverage
        self.use_fixed_capital = bool(getattr(config, "USE_FIXED_CAPITAL", False))
        self.sizing_base = float(getattr(config, "FIXED_CAPITAL", 1000.0)) if self.use_fixed_capital else float(capital)
        self.equity = float(capital)
        self.capital = float(capital)
        self.risk_pct = risk_pct
        self.position = None
        self.entry_price = 0
        self.entry_time = None
        self.position_size = 0
        self.stop_loss_price = 0
        self.tp1_price = 0
        self.tp2_price = 0
        self.tp3_price = 0
        self.tp1_hit = False
        self.tp2_hit = False
        self.entry_confluence_score = 0
        self.last_entry_time = None

    def calculate_confluence_score(self, df, idx):
        """
        Calculate confluence score for entry

        Returns:
            tuple: (score, direction, details_dict)

        Score interpretation:
            0-2: Skip the trade
            3-4: Consider with reduced size
            5-6: Standard size trade
            7+: Maximum confidence (rare)
        """
        row = df.iloc[idx]
        score = 0
        direction = 0  # 1 = long, -1 = short
        details = {}

        # CONFLUENCE 1: Liquidity Sweep (+1)
        if row.get('ssl_sweep', False):  # SSL swept = bullish
            score += 1
            direction = 1
            details['liquidity_sweep'] = 'SSL'
        elif row.get('bsl_sweep', False):  # BSL swept = bearish
            score += 1
            direction = -1
            details['liquidity_sweep'] = 'BSL'

        # Equal highs/lows at liquidity pool (+1, sets direction if missing)
        if row.get('equal_lows', False):
            if direction == 0:
                direction = 1
            score += 1
            details['at_liquidity_pool'] = 'equal_lows'
        elif row.get('equal_highs', False):
            if direction == 0:
                direction = -1
            score += 1
            details['at_liquidity_pool'] = 'equal_highs'

        # Structure-only bias when sweeps are absent
        if direction == 0 and getattr(config, "ALLOW_STRUCTURE_ONLY_ENTRY", True):
            if row.get('bullish_bos', False) or row.get('bullish_choch', False):
                direction = 1
                details['structure_only'] = 'bullish'
            elif row.get('bearish_bos', False) or row.get('bearish_choch', False):
                direction = -1
                details['structure_only'] = 'bearish'
            elif row.get('market_trend', 0) == 1:
                direction = 1
                details['structure_only'] = 'trend_up'
            elif row.get('market_trend', 0) == -1:
                direction = -1
                details['structure_only'] = 'trend_down'

        if direction == 0:
            return 0, 0, details

        # CONFLUENCE 2: CVD Confirmation (+1)
        if direction == 1:  # Looking for long
            if row.get('cvd_bullish_divergence', False):
                score += 1
                details['cvd'] = 'bullish_divergence'
            elif row.get('cvd_bullish_surge', False):
                score += 1
                details['cvd'] = 'bullish_surge'
        elif direction == -1:  # Looking for short
            if row.get('cvd_bearish_divergence', False):
                score += 1
                details['cvd'] = 'bearish_divergence'
            elif row.get('cvd_bearish_surge', False):
                score += 1
                details['cvd'] = 'bearish_surge'

        # CONFLUENCE 3: Order Block Alignment (+1)
        if direction == 1:
            if row.get('bullish_ob_hold', False):
                score += 1
                details['order_block'] = 'bullish_hold'
        elif direction == -1:
            if row.get('bearish_ob_hold', False):
                score += 1
                details['order_block'] = 'bearish_hold'

        # CONFLUENCE 4: Market Structure (+1)
        if direction == 1:
            if row.get('bullish_bos', False):
                score += 1
                details['structure'] = 'bullish_bos'
            elif row.get('bullish_choch', False):
                score += 1
                details['structure'] = 'bullish_choch'
        elif direction == -1:
            if row.get('bearish_bos', False):
                score += 1
                details['structure'] = 'bearish_bos'
            elif row.get('bearish_choch', False):
                score += 1
                details['structure'] = 'bearish_choch'

        # CONFLUENCE 5: Trend Alignment (+1)
        market_trend = row.get('market_trend', 0)
        if (direction == 1 and market_trend == 1) or (direction == -1 and market_trend == -1):
            score += 1
            details['trend_aligned'] = True

        # CONFLUENCE 6: Structure Strength (+1)
        structure_strength = row.get('structure_strength', 0)
        if structure_strength >= 60:  # Strong structure
            score += 1
            details['structure_strength'] = structure_strength

        # CONFLUENCE 7: Volume Confirmation (+1)
        volume_spike = row.get('volume_spike', 1.0)
        if volume_spike >= config.VOLUME_SPIKE_MULTIPLIER:
            score += 1
            details['volume_spike'] = volume_spike

        return score, direction, details

    def _entry_spacing_ok(self, df, idx) -> bool:
        """Enforce minimum time between new entries (targets ~1–2 trades/week)."""
        min_h = float(getattr(config, "MIN_HOURS_BETWEEN_ENTRIES", 0))
        if min_h <= 0 or self.last_entry_time is None:
            return True
        ts = df.iloc[idx]['timestamp']
        gap = (ts - self.last_entry_time).total_seconds() / 3600
        return gap >= min_h

    def check_entry_conditions(self, df, idx):
        """
        Check if entry conditions are met

        Returns:
            tuple: (should_enter, direction, confluence_score, details)
        """
        if idx < 100:  # Need enough data
            return False, 0, 0, {}

        # Calculate confluence score
        score, direction, details = self.calculate_confluence_score(df, idx)

        # Minimum confluence requirement
        if score < config.MIN_CONFLUENCE_SCORE:
            return False, 0, score, details

        # Additional filters
        row = df.iloc[idx]

        if getattr(config, "BLOCK_CVD_EXHAUSTION", False):
            if direction == 1 and row.get('cvd_bullish_exhaustion', False):
                return False, 0, score, details
            if direction == -1 and row.get('cvd_bearish_exhaustion', False):
                return False, 0, score, details

        if getattr(config, "BLOCK_LIQUIDITY_VOID", False) and row.get('liquidity_void', False):
            return False, 0, score, details

        return True, direction, score, details

    def enter_position(self, df, idx, direction, confluence_score, details):
        """Enter a position (fixed size, no stop-loss)."""
        row = df.iloc[idx]
        entry_price = row['close']
        position_size = fixed_position_size(self.equity)

        self.position = direction
        self.entry_price = entry_price
        self.entry_time = row['timestamp']
        self.position_size = position_size
        self.entry_confluence_score = confluence_score
        self.last_entry_time = row['timestamp']

        return {
            'timestamp': row['timestamp'],
            'action': 'ENTER',
            'direction': 'LONG' if direction == 1 else 'SHORT',
            'price': entry_price,
            'position_size': position_size,
            'confluence_score': confluence_score,
            'confluence_details': details,
            'leverage': self.leverage
        }

    def check_exit_conditions(self, df, idx):
        """Exit via hold_exit_rules (50% by 48h, else 15%+ / window end; no min hold)."""
        if self.position is None:
            return False, None, 1.0

        row = df.iloc[idx]
        ok, reason = should_exit(
            self.entry_time,
            row['timestamp'],
            self.entry_price,
            row['close'],
            self.position,
            self.leverage,
        )
        if ok:
            return True, reason, 1.0
        return False, None, 1.0

    def exit_position(self, df, idx, reason, exit_portion=1.0):
        """Exit position (full or partial)"""
        row = df.iloc[idx]
        exit_price = row['close']

        # Calculate P&L for this portion
        if self.position == 1:  # Long
            pnl_pct = (exit_price - self.entry_price) / self.entry_price * 100
        else:  # Short
            pnl_pct = (self.entry_price - exit_price) / self.entry_price * 100

        # Apply leverage
        pnl_pct_leveraged = pnl_pct * self.leverage

        # Dollar P&L on posted margin (capped at -100% of margin = full loss)
        portion_size = self.position_size * exit_portion
        pnl_dollar = portion_size * (pnl_pct_leveraged / 100)
        pnl_dollar = max(pnl_dollar, -portion_size)

        # Apply fees and slippage
        fees = portion_size * self.leverage * (config.TRADING_FEE_TAKER_PCT / 100) * 2
        slippage = portion_size * self.leverage * (config.SLIPPAGE_PCT / 100) * 2

        # Calculate funding costs
        hold_time_hours = (row['timestamp'] - self.entry_time).total_seconds() / 3600
        funding_cost = portion_size * self.leverage * (config.FUNDING_RATE_HOURLY / 100) * hold_time_hours

        net_pnl = pnl_dollar - fees - slippage - funding_cost

        if self.use_fixed_capital:
            self.equity += net_pnl
        else:
            self.capital += net_pnl
            self.equity = self.capital

        trade_result = {
            'timestamp': row['timestamp'],
            'action': 'EXIT',
            'direction': 'LONG' if self.position == 1 else 'SHORT',
            'entry_price': self.entry_price,
            'exit_price': exit_price,
            'exit_portion': exit_portion,
            'pnl_pct': pnl_pct,
            'pnl_pct_leveraged': pnl_pct_leveraged,
            'pnl_dollar': pnl_dollar,
            'fees': fees,
            'slippage': slippage,
            'funding_cost': funding_cost,
            'net_pnl': net_pnl,
            'hold_time_hours': hold_time_hours,
            'exit_reason': reason,
            'confluence_score': self.entry_confluence_score
        }

        if exit_portion >= 1.0:
            self.position = None
            self.entry_price = 0
            self.entry_time = None
            self.position_size = 0
        else:
            self.position_size *= (1 - exit_portion)

        return trade_result

    def run(self, df, start_idx=0):
        """
        Run strategy on historical data

        Args:
            df: DataFrame with all indicators calculated
            start_idx: First bar index to evaluate (for out-of-sample / forward
                segments). Indicators on row i must already be causal; start
                flat with no open position.

        Returns:
            list: List of all trades executed
        """
        trades = []
        start_idx = max(0, int(start_idx))

        for idx in range(start_idx, len(df)):
            if self.position is None:
                # Look for entry
                should_enter, direction, score, details = self.check_entry_conditions(df, idx)
                if should_enter and self.equity >= min_equity_to_trade() and self._entry_spacing_ok(df, idx):
                    entry = self.enter_position(df, idx, direction, score, details)
                    trades.append(entry)
            else:
                # Look for exit
                should_exit, reason, portion = self.check_exit_conditions(df, idx)
                if should_exit:
                    exit_trade = self.exit_position(df, idx, reason, portion)
                    trades.append(exit_trade)

        return trades


if __name__ == "__main__":
    print("Professional Strategy Module")
    print("=" * 60)
    print("Use with backtester.py to test this strategy")
    print("\nEntry requirements: Minimum 3 confluences")
    print("Recommended: 5+ confluences for A+ setups")
