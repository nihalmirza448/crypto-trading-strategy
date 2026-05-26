"""
Shared hold / return exit rules (no stop-loss).

- Optional minimum hold: MIN_HOLD_HOURS (0 = none; legacy default was 24)
- By HOLD_WINDOW_END_HOURS (default 48): exit if leveraged return >= TARGET_RETURN_PCT (50%)
- At/after window end: exit if return >= MIN_EXIT_RETURN_PCT (15%), else force exit
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Tuple, Union

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
) -> Tuple[bool, Optional[str]]:
    """
    Returns (should_exit, reason).
    """
    min_hold = float(_cfg("MIN_HOLD_HOURS", 0))
    window_end = float(_cfg("HOLD_WINDOW_END_HOURS", 48))
    target = float(_cfg("TARGET_RETURN_PCT", 50))
    min_exit = float(_cfg("MIN_EXIT_RETURN_PCT", 15))

    hrs = hold_hours(entry_time, current_time)
    if min_hold > 0 and hrs < min_hold:
        return False, None

    ret = leveraged_return_pct(price_pnl_pct(entry_price, current_price, direction), leverage)

    if hrs < window_end and ret >= target:
        return True, "target_50pct"

    if hrs >= window_end:
        if ret >= min_exit:
            return True, "min_15pct"
        return True, "window_end"

    return False, None


def sizing_capital(account_equity: float) -> float:
    """Notional base for position sizing (fixed $1k mode vs compounding equity)."""
    if bool(_cfg("USE_FIXED_CAPITAL", False)):
        return float(_cfg("FIXED_CAPITAL", 1000.0))
    return account_equity


def fixed_position_size(account_equity: float) -> float:
    pct = float(_cfg("POSITION_SIZE_PCT", 0.95))
    base = sizing_capital(account_equity)
    if bool(_cfg("USE_FIXED_CAPITAL", False)):
        # Cannot deploy more margin than available equity
        deployable = max(0.0, float(account_equity)) * pct
        return min(base * pct, deployable)
    return base * pct


def min_equity_to_trade() -> float:
    """Minimum equity required to open the next position."""
    pct = float(_cfg("POSITION_SIZE_PCT", 0.95))
    base = sizing_capital(1000.0)
    return base * pct * 0.1  # at least 10% of normal margin available


def exit_rule_snapshot(leverage: float = 1.0) -> dict:
    """Config snapshot for backtests / recommendations (no stop-loss)."""
    return {
        "min_hold_hours": float(_cfg("MIN_HOLD_HOURS", 0)),
        "hold_window_end_hours": float(_cfg("HOLD_WINDOW_END_HOURS", 48)),
        "target_return_pct": float(_cfg("TARGET_RETURN_PCT", 50)),
        "min_exit_return_pct": float(_cfg("MIN_EXIT_RETURN_PCT", 15)),
        "position_size_pct": float(_cfg("POSITION_SIZE_PCT", 0.95)),
        "leverage": leverage,
        "no_stop_loss": True,
    }


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
    return (
        f"{min_part} | "
        f"{s['target_return_pct']:.0f}% return by {s['hold_window_end_hours']:.0f}h | "
        f"else exit at {s['min_exit_return_pct']:.0f}%+ | no stop-loss"
    )
