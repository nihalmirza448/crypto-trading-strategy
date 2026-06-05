"""
Download BTC/ETH OHLCV from CryptoQuant into data/ CSV files.

Professional plan limits (per CryptoQuant support):
  - window: ``day`` only (``hour`` / ``min`` require Premium)
  - history: up to ~1 year (CRYPTOQUANT_MAX_LOOKBACK_DAYS, default 365)

Auth: Authorization: Bearer <key> in CRYPTOQUANT_ACCESS_TOKEN or CRYPTOQUANT_API_KEY.

Hourly backtests (``eth_usd_60m_*.csv``) still need exchange data or Premium CQ tier.

Usage:
  python fetch_cryptoquant_ohlcv.py
  python fetch_cryptoquant_ohlcv.py --days 365 --assets btc eth
  python fetch_cryptoquant_ohlcv.py --window day
"""

from __future__ import annotations

import argparse
import os
import sys

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

try:
    import config_professional as config
except ImportError:
    config = None  # type: ignore

# CQ plan guardrails
PRO_WINDOW_ALLOWED = frozenset({"day"})
PREMIUM_WINDOWS = frozenset({"min", "hour", "day"})


def _cfg(name: str, default: str) -> str:
    if config is not None and hasattr(config, name):
        v = getattr(config, name)
        if v is not None and str(v).strip():
            return str(v).strip()
    return os.getenv(name, default)


def _cfg_int(name: str, default: int) -> int:
    if config is not None and hasattr(config, name):
        v = getattr(config, name)
        if v is not None:
            return int(v)
    return int(os.getenv(name, str(default)))


def _output_basename(asset: str, window: str, days: int) -> str:
    """Match repo naming: 60m for hour, 1440m for day."""
    interval = "60m" if window == "hour" else "1440m"
    return f"{asset}_usd_{interval}_{days}d.csv"


def main() -> None:
    default_window = _cfg("CRYPTOQUANT_WINDOW", "day")
    max_days = _cfg_int("CRYPTOQUANT_MAX_LOOKBACK_DAYS", 365)
    default_days = min(
        int(getattr(config, "LOOKBACK_DAYS", 365) if config else 365),
        max_days,
    )

    parser = argparse.ArgumentParser(description="Fetch OHLCV from CryptoQuant")
    parser.add_argument(
        "--days",
        type=int,
        default=default_days,
        help=f"Calendar days of history (capped at {max_days} for Professional)",
    )
    parser.add_argument(
        "--window",
        type=str,
        default=default_window,
        choices=sorted(PREMIUM_WINDOWS),
        help="CQ window: Professional supports day only",
    )
    parser.add_argument(
        "--assets",
        nargs="+",
        default=["btc", "eth"],
        choices=["btc", "eth"],
        help="Which assets to download",
    )
    parser.add_argument("--data-dir", type=str, default=_cfg("DATA_DIR", "data"))
    args = parser.parse_args()

    if args.window not in PRO_WINDOW_ALLOWED:
        print(
            f"⚠️  window={args.window!r} is not available on CryptoQuant Professional "
            f"(use day, or upgrade to Premium for hour/min).",
            file=sys.stderr,
        )
        sys.exit(1)

    days = min(args.days, max_days)
    if days < args.days:
        print(
            f"⚠️  Capping --days {args.days} → {days} (CRYPTOQUANT_MAX_LOOKBACK_DAYS={max_days})"
        )

    market = _cfg("CRYPTOQUANT_MARKET", "spot")
    exchange = _cfg("CRYPTOQUANT_EXCHANGE", "all_exchange")
    sym_btc = _cfg("CRYPTOQUANT_BTC_SYMBOL", "btc_usd")
    sym_eth = _cfg("CRYPTOQUANT_ETH_SYMBOL", "eth_usd")

    from cryptoquant_client import fetch_price_ohlcv_range, rows_to_backtest_csv_rows

    os.makedirs(args.data_dir, exist_ok=True)

    for asset in args.assets:
        symbol = sym_btc if asset == "btc" else sym_eth
        print(
            f"\nFetching {asset.upper()} OHLCV (market={market}, exchange={exchange}, "
            f"symbol={symbol}, window={args.window}, days={days})..."
        )
        raw = fetch_price_ohlcv_range(
            asset,
            days=days,
            window=args.window,
            market=market,
            exchange=exchange,
            symbol=symbol,
        )
        if not raw:
            print(f"❌ No rows returned for {asset}. Check plan, symbol, and API credentials.")
            sys.exit(1)
        rows = rows_to_backtest_csv_rows(raw)
        df = pd.DataFrame(rows)
        df = df.drop_duplicates(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
        out_name = _output_basename(asset, args.window, days)
        out = os.path.join(args.data_dir, out_name)
        df.to_csv(out, index=False)
        print(f"✅ Saved {len(df)} candles → {out}")
        print(f"   Range: {df['timestamp'].iloc[0]} … {df['timestamp'].iloc[-1]}")
        if args.window == "day":
            print(
                "   Note: daily bars. For 1h backtests set TIMEFRAME=1d or use exchange hourly CSVs."
            )


if __name__ == "__main__":
    main()
