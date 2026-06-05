"""
Hybrid Strategy — evaluates BOTH confluence models every bar, enters whichever
fires, one position at a time per asset (reversal takes priority).

Per bar:
  1. Compute the reversal (Professional) confluence score.
     -> if it qualifies (>= MIN_CONFLUENCE_SCORE, direction set, filters ok): ENTER reversal.
  2. Else compute the momentum (TrendMomentum) continuation score.
     -> if it qualifies (>= TREND_MIN_CONFLUENCE_SCORE): ENTER momentum.
  3. Else stay flat.

Priority = reversal first (higher historical win rate); momentum only fills the
trend days the reversal model sits out. Reversal behavior is unchanged (strict
superset), so the existing edge is preserved while adding pump/dump capture.

Each entry's trade record carries details['mode'] = 'reversal' | 'momentum'.
Reuses ProfessionalStrategy's sizing, scaled-TP exits, spacing, equity floor.
"""

from __future__ import annotations

from strategy_professional import ProfessionalStrategy
from strategy_trend_momentum import TrendMomentumStrategy

try:
    import config_professional as config
except ImportError:
    import config  # type: ignore


class HybridStrategy(ProfessionalStrategy):
    """Reversal-priority dual-confluence strategy (reversal + momentum)."""

    def __init__(self, leverage=5, capital=1000, risk_pct=1.5):
        super().__init__(leverage=leverage, capital=capital, risk_pct=risk_pct)
        # Stateless scorer used only for momentum confluence reads (df/idx/config).
        self._mom = TrendMomentumStrategy(leverage=leverage, capital=capital, risk_pct=risk_pct)

    def _reversal_score(self, df, idx):
        # Call the BASE implementation explicitly to avoid recursing into this override.
        return ProfessionalStrategy.calculate_confluence_score(self, df, idx)

    def _reversal_filters_block(self, df, idx, direction) -> bool:
        row = df.iloc[idx]
        if getattr(config, "BLOCK_CVD_EXHAUSTION", False):
            if direction == 1 and row.get("cvd_bullish_exhaustion", False):
                return True
            if direction == -1 and row.get("cvd_bearish_exhaustion", False):
                return True
        if getattr(config, "BLOCK_LIQUIDITY_VOID", False) and row.get("liquidity_void", False):
            return True
        return False

    def calculate_confluence_score(self, df, idx):
        """Return the ACTIVE playbook's (score, direction, details) under reversal-priority."""
        rs, rd, rdet = self._reversal_score(df, idx)
        if rs >= int(getattr(config, "MIN_CONFLUENCE_SCORE", 3)) and rd != 0:
            return rs, rd, {**rdet, "mode": "reversal"}
        ms, md, mdet = self._mom.calculate_confluence_score(df, idx)
        if ms >= int(getattr(config, "TREND_MIN_CONFLUENCE_SCORE", 7)) and md != 0:
            return ms, md, {**mdet, "mode": "momentum"}
        # Neither qualifies — surface the reversal read (keeps min_score semantics clean).
        return rs, rd, rdet

    def check_entry_conditions(self, df, idx):
        if idx < 100:
            return False, 0, 0, {}

        # --- Reversal leg (priority) ---
        rs, rd, rdet = self._reversal_score(df, idx)
        if rs >= int(getattr(config, "MIN_CONFLUENCE_SCORE", 3)) and rd != 0:
            if not self._reversal_filters_block(df, idx, rd):
                return True, rd, rs, {**rdet, "mode": "reversal"}

        # --- Momentum leg (only if reversal didn't fire) ---
        should, md, ms, mdet = self._mom.check_entry_conditions(df, idx)
        if should and md != 0:
            return True, md, ms, {**mdet, "mode": "momentum"}

        return False, 0, rs, rdet


if __name__ == "__main__":
    print("Hybrid Strategy — reversal-priority dual confluence (reversal>=3, else momentum>=7)")
