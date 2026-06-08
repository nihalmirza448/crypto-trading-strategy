"""
Shared hold / return exit rules (no stop-loss).

Legacy mode (USE_SCALED_EXITS=False):
- By HOLD_WINDOW_END_HOURS: exit if leveraged return >= TARGET_RETURN_PCT (50%)
- At/after window end: exit if return >= MIN_EXIT_RETURN_PCT (15%), else force exit

Scaled mode (USE_SCALED_EXITS=True):
- TP1: take TP1_EXIT_PORTION (50%) at TP1_RETURN_PCT gross on margin
- TP2: take TP2_EXIT_PORTION of remainder (25% orig) at TP2_RETURN_PCT
- Runner: trail peak − RUNNER_TRAIL_GIVEBACK_PCT; optional HOLD_WINDOW_END_HOURS cap
- Design goal: TARGET_NET_TRADE_RETURN_PCT (+50% on margin net of fees, full trade)
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional, Tuple, Union

try:
    import config_professional as config
except ImportError:
    import config  # type: ignore


def _cfg(name: str, default):
    return getattr(config, name, default)


def price_pnl_pct(
    entry_price: float,
    current_price: float,
    direction: Union[int, str],
) -> float:
    if direction in (1, "LONG", "long"):
        return (current_price - entry_price) / entry_price * 100
    return (entry_price - current_price) / entry_price * 100


def leveraged_return_pct(price_pnl: float, leverage: float = 1.0) -> float:
    return price_pnl * leverage


def hold_hours(entry_time: datetime, current_time: datetime) -> float:
    return (current_time - entry_time).total_seconds() / 3600


def should_exit(
    entry_time: datetime,
    current_time: datetime,
    entry_price: float,
    current_price: float,
    direction: Union[int, str],
    leverage: float = 1.0,
    position_state: Optional[dict[str, Any]] = None,
) -> Tuple[bool, Optional[str], float]:
    """
    Returns (should_exit, reason, exit_portion).
    exit_portion is a fraction of the *current* open position (0–1).
    """
    min_hold = float(_cfg("MIN_HOLD_HOURS", 0))
    window_end = float(_cfg("HOLD_WINDOW_END_HOURS", 48))
    target = float(_cfg("TARGET_RETURN_PCT", 50))
    min_exit = float(_cfg("MIN_EXIT_RETURN_PCT", 15))
    use_scaled = bool(_cfg("USE_SCALED_EXITS", False))

    hrs = hold_hours(entry_time, current_time)
    if min_hold > 0 and hrs < min_hold:
        return False, None, 0.0

    ret = leveraged_return_pct(price_pnl_pct(entry_price, current_price, direction), leverage)
    ret = round(ret, 6)
    state = position_state or {}
    tp1_done = bool(state.get("tp1_done", False))
    tp2_done = bool(state.get("tp2_done", False))
    peak = max(float(state.get("peak_return_pct", ret)), ret)

    if use_scaled:
        tp1_ret = float(_cfg("TP1_RETURN_PCT", 55))
        tp1_portion = float(_cfg("TP1_EXIT_PORTION", 0.50))
        tp2_ret = float(_cfg("TP2_RETURN_PCT", 100))
        tp2_portion = float(_cfg("TP2_EXIT_PORTION", 0.50))
        trail_giveback = float(_cfg("RUNNER_TRAIL_GIVEBACK_PCT", 25))

        if not tp1_done and ret >= tp1_ret:
            return True, "tp1_partial", tp1_portion

        if tp1_done and not tp2_done and ret >= tp2_ret:
            return True, "tp2_partial", tp2_portion

        if tp1_done and peak > 0 and (peak - ret) >= trail_giveback and ret > float(_cfg("MIN_RUNNER_RETURN_PCT", 15)):
            return True, "trail_runner", 1.0

        if window_end > 0 and hrs >= window_end:
            if ret >= min_exit:
                return True, "min_15pct", 1.0
            return True, "window_end", 1.0

        return False, None, 0.0

    if (window_end <= 0 or hrs < window_end) and ret >= target:
        return True, "target_50pct", 1.0

    if window_end > 0 and hrs >= window_end:
        if ret >= min_exit:
            return True, "min_15pct", 1.0
        return True, "window_end", 1.0

    return False, None, 0.0


def sizing_capital(account_equity: float) -> float:
    """Notional base for position sizing (fixed $1k mode vs compounding equity)."""
    if bool(_cfg("USE_FIXED_CAPITAL", True)):
        return float(_cfg("FIXED_CAPITAL", 1000.0))
    return account_equity


def max_entry_margin() -> float:
    """Hard cap on margin per entry when USE_FIXED_CAPITAL (wins do not increase exposure)."""
    return float(_cfg("FIXED_CAPITAL", 1000.0)) * float(_cfg("POSITION_SIZE_PCT", 0.95))


def fixed_position_size(account_equity: float) -> float:
    pct = float(_cfg("POSITION_SIZE_PCT", 0.95))
    equity = max(0.0, float(account_equity))
    if bool(_cfg("USE_FIXED_CAPITAL", True)):
        # Always size from FIXED_CAPITAL, never from equity above that base (no compounding).
        cap = max_entry_margin()
        deployable = equity * pct
        return min(cap, deployable)
    return equity * pct


def min_equity_to_trade() -> float:
    """Minimum account equity required to open the next position."""
    explicit = _cfg("MIN_EQUITY_TO_TRADE", None)
    if explicit is not None:
        return float(explicit)
    if bool(_cfg("USE_FIXED_CAPITAL", True)):
        return float(_cfg("FIXED_CAPITAL", 1000.0))
    return float(_cfg("CAPITAL", 1000.0))


def exit_rule_snapshot(leverage: float = 1.0) -> dict:
    """Config snapshot for backtests / recommendations (no stop-loss)."""
    fixed = bool(_cfg("USE_FIXED_CAPITAL", True))
    scaled = bool(_cfg("USE_SCALED_EXITS", False))
    snap = {
        "min_hold_hours": float(_cfg("MIN_HOLD_HOURS", 0)),
        "hold_window_end_hours": float(_cfg("HOLD_WINDOW_END_HOURS", 48)),
        "target_return_pct": float(_cfg("TARGET_RETURN_PCT", 50)),
        "min_exit_return_pct": float(_cfg("MIN_EXIT_RETURN_PCT", 15)),
        "position_size_pct": float(_cfg("POSITION_SIZE_PCT", 0.95)),
        "leverage": leverage,
        "no_stop_loss": True,
        "use_fixed_capital": fixed,
        "fixed_capital": float(_cfg("FIXED_CAPITAL", 1000.0)) if fixed else None,
        "max_entry_margin": max_entry_margin() if fixed else None,
        "use_scaled_exits": scaled,
        "target_net_trade_return_pct": float(_cfg("TARGET_NET_TRADE_RETURN_PCT", 50)),
    }
    if scaled:
        snap.update(
            {
                "tp1_return_pct": float(_cfg("TP1_RETURN_PCT", 55)),
                "tp1_exit_portion": float(_cfg("TP1_EXIT_PORTION", 0.50)),
                "tp2_return_pct": float(_cfg("TP2_RETURN_PCT", 100)),
                "tp2_exit_portion": float(_cfg("TP2_EXIT_PORTION", 0.50)),
                "runner_trail_giveback_pct": float(_cfg("RUNNER_TRAIL_GIVEBACK_PCT", 25)),
            }
        )
    return snap


def target_prices(
    entry_price: float,
    direction: Union[int, str],
    leverage: float = 1.0,
) -> dict:
    """Reference prices for 50% and 15% leveraged return targets."""
    t50 = float(_cfg("TARGET_RETURN_PCT", 50)) / leverage / 100
    t15 = float(_cfg("MIN_EXIT_RETURN_PCT", 15)) / leverage / 100
    if direction in (1, "LONG", "long"):
        return {
            "target_50pct_price": entry_price * (1 + t50),
            "min_15pct_price": entry_price * (1 + t15),
        }
    return {
        "target_50pct_price": entry_price * (1 - t50),
        "min_15pct_price": entry_price * (1 - t15),
    }


def exit_rules_description(leverage: float = 1.0) -> str:
    s = exit_rule_snapshot(leverage)
    min_part = (
        "No min hold"
        if s["min_hold_hours"] <= 0
        else f"Min hold {s['min_hold_hours']:.0f}h"
    )
    if s.get("use_scaled_exits"):
        window_part = (
            f"{s['hold_window_end_hours']:.0f}h window | "
            if s["hold_window_end_hours"] > 0
            else "no time cap | "
        )
        return (
            f"{min_part} | scaled: "
            f"{s['tp1_exit_portion']*100:.0f}% off @ {s['tp1_return_pct']:.0f}%+ | "
            f"{s['tp2_exit_portion']*100:.0f}% of rest @ {s['tp2_return_pct']:.0f}%+ | "
            f"trail −{s['runner_trail_giveback_pct']:.0f}% from peak | "
            f"{window_part}"
            f"goal ≥{s['target_net_trade_return_pct']:.0f}% net on margin | no stop-loss"
        )
    if s["hold_window_end_hours"] <= 0:
        return (
            f"{min_part} | "
            f"{s['target_return_pct']:.0f}% return anytime | no time cap | no stop-loss"
        )
    return (
        f"{min_part} | "
        f"{s['target_return_pct']:.0f}% return by {s['hold_window_end_hours']:.0f}h | "
        f"else exit at {s['min_exit_return_pct']:.0f}%+ | no stop-loss"
    )
