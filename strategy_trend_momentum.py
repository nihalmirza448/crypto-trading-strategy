"""
Trend Momentum (Continuation) Strategy — trades WITH strong pump/dump days.

Complements the reversal-based ProfessionalStrategy:
- Professional   -> liquidity sweep + reject (fade the flush / failed move)
- TrendMomentum  -> trade in the direction of a confirmed strong trend (pump or dump)

Design intent:
- ONLY fires on a clean, fully-confirmed trend day (high confluence bar).
- Direction is set by trend + EMA structure; entries require a STRONG stack of
  continuation confirmations (default >= TREND_MIN_CONFLUENCE_SCORE of 9).
- Reuses ProfessionalStrategy's sizing, scaled-TP exits, spacing, and equity floor
  via subclassing (only entry logic changes).

Confluence components (each +1, max 9):
  1. Trend alignment (market_trend matches direction)        [required to set direction]
  2. EMA full stack (50>100>200 for long; reverse for short)
  3. Break of structure in trade direction (BOS)
  4. CVD surge in trade direction (aggressive flow)
  5. Volume spike (conviction)
  6. Structure strength >= TREND_MIN_STRUCTURE_STRENGTH
  7. Momentum thrust: |price move| over TREND_MOMENTUM_LOOKBACK bars >= TREND_MOMENTUM_MIN_PCT
  8. RSI in trend zone (not blow-off / not capitulation)
  9. No CVD exhaustion against the trade
"""

from __future__ import annotations

from strategy_professional import ProfessionalStrategy

try:
    import config_professional as config
except ImportError:
    import config  # type: ignore


class TrendMomentumStrategy(ProfessionalStrategy):
    """Trend-continuation entries (pump/dump) with strong-confirmation confluence."""

    def calculate_confluence_score(self, df, idx):
        """Return (score, direction, details) for a trend-continuation setup."""
        row = df.iloc[idx]
        details: dict = {}
        score = 0
        direction = 0

        close = float(row.get("close", 0.0))
        ema50 = row.get("ema_50")
        ema100 = row.get("ema_100")
        ema200 = row.get("ema_200")
        market_trend = int(row.get("market_trend", 0) or 0)

        # Need EMAs to assess trend structure
        if ema50 is None or ema200 is None or ema50 != ema50 or ema200 != ema200:
            return 0, 0, details

        # --- Direction: requires a clean, aligned trend (no chop) ---
        if market_trend == 1 and close > ema50 and ema50 > ema200:
            direction = 1
        elif market_trend == -1 and close < ema50 and ema50 < ema200:
            direction = -1
        else:
            return 0, 0, details  # momentum strat stays flat unless trend is clean

        # 1. Trend alignment (direction was set by it)
        score += 1
        details["trend"] = "up" if direction == 1 else "down"

        # 2. EMA full stack
        if ema100 is not None and ema100 == ema100:
            if direction == 1 and ema50 > ema100 > ema200:
                score += 1
                details["ema_stack"] = True
            elif direction == -1 and ema50 < ema100 < ema200:
                score += 1
                details["ema_stack"] = True

        # 3. Break of structure in trade direction
        if direction == 1 and row.get("bullish_bos", False):
            score += 1
            details["bos"] = "bullish"
        elif direction == -1 and row.get("bearish_bos", False):
            score += 1
            details["bos"] = "bearish"

        # 4. CVD surge in trade direction
        if direction == 1 and row.get("cvd_bullish_surge", False):
            score += 1
            details["cvd"] = "bullish_surge"
        elif direction == -1 and row.get("cvd_bearish_surge", False):
            score += 1
            details["cvd"] = "bearish_surge"

        # 5. Volume spike (conviction)
        vol_spike = float(row.get("volume_spike", 1.0) or 1.0)
        if vol_spike >= float(getattr(config, "VOLUME_SPIKE_MULTIPLIER", 1.2)):
            score += 1
            details["volume_spike"] = vol_spike

        # 6. Structure strength
        ss = float(row.get("structure_strength", 0) or 0)
        if ss >= float(getattr(config, "TREND_MIN_STRUCTURE_STRENGTH", 60)):
            score += 1
            details["structure_strength"] = ss

        # 7. Momentum thrust — the actual pump/dump
        n = int(getattr(config, "TREND_MOMENTUM_LOOKBACK", 6))
        thr = float(getattr(config, "TREND_MOMENTUM_MIN_PCT", 2.0))
        if idx >= n:
            past = float(df.iloc[idx - n].get("close", close) or close)
            if past:
                chg = (close - past) / past * 100.0
                if (direction == 1 and chg >= thr) or (direction == -1 and chg <= -thr):
                    score += 1
                    details["thrust_pct"] = round(chg, 2)

        # 8. RSI in trend zone (avoid blow-off top / capitulation bottom)
        rsi = row.get("rsi")
        if rsi is not None and rsi == rsi:
            rsi = float(rsi)
            rsi_max = float(getattr(config, "TREND_RSI_MAX", 80))
            rsi_min = float(getattr(config, "TREND_RSI_MIN", 20))
            if direction == 1 and 50.0 <= rsi < rsi_max:
                score += 1
                details["rsi"] = round(rsi, 1)
            elif direction == -1 and rsi_min < rsi <= 50.0:
                score += 1
                details["rsi"] = round(rsi, 1)

        # 9. No CVD exhaustion against the trade
        if direction == 1 and not row.get("cvd_bullish_exhaustion", False):
            score += 1
            details["no_exhaustion"] = True
        elif direction == -1 and not row.get("cvd_bearish_exhaustion", False):
            score += 1
            details["no_exhaustion"] = True

        return score, direction, details

    def check_entry_conditions(self, df, idx):
        """Enter only on a very strong continuation stack (full confirmation)."""
        if idx < 100:
            return False, 0, 0, {}

        score, direction, details = self.calculate_confluence_score(df, idx)

        min_score = int(getattr(config, "TREND_MIN_CONFLUENCE_SCORE", 7))
        if score < min_score or direction == 0:
            return False, 0, score, details

        row = df.iloc[idx]
        if getattr(config, "BLOCK_LIQUIDITY_VOID", False) and row.get("liquidity_void", False):
            return False, 0, score, details

        return True, direction, score, details


if __name__ == "__main__":
    print("Trend Momentum (Continuation) Strategy")
    print("Direction: clean trend + EMA stack | Entry: >= TREND_MIN_CONFLUENCE_SCORE of 9")
