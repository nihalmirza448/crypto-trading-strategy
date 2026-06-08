#!/usr/bin/env python3
"""
Fetch / refresh local OHLCV CSVs from Binance public API.

Writes:
  data/{btc,eth}_usd_60m_1825d.csv   — ~5 years of 1h candles
  data/{btc,eth}_usd_60m_365d.csv    — last 365 days (sliced from 5y fetch)
  data/{btc,eth}_usd_240m_365d.csv   — 4h resample of 365d 1h

Used by scripts/weekly_backtest_refresh.sh (launchd weekly timer).
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import datetime, timedelta, timezone

import pandas as pd
import requests

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO_ROOT, "data")
ASSETS = ("BTC", "ETH")
DAYS_5Y = 1825
DAYS_1Y = 365


def fetch_binance_klines(symbol: str, interval: str, start_ms: int, end_ms: int, limit: int = 1000):
    url = "https://api.binance.com/api/v3/klines"
    resp = requests.get(
        url,
        params={
            "symbol": symbol,
            "interval": interval,
            "startTime": start_ms,
            "endTime": end_ms,
            "limit": limit,
        },
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()


def fetch_history(asset: str, interval: str = "1h", days: int = DAYS_5Y) -> pd.DataFrame:
    symbol = f"{asset.upper()}USDT"
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    start_ms = now_ms - days * 24 * 3600 * 1000
    rows = []
    current_ms = start_ms
    batch = 0

    print(f"  Binance {symbol} {interval} ({days}d)...", flush=True)
    while current_ms < now_ms:
        batch += 1
        batch_rows = fetch_binance_klines(symbol, interval, current_ms, now_ms)
        if not batch_rows:
            break
        for c in batch_rows:
            vol = float(c[5])
            rows.append(
                {
                    "timestamp": datetime.fromtimestamp(c[0] / 1000, tz=timezone.utc).replace(tzinfo=None),
                    "open": float(c[1]),
                    "high": float(c[2]),
                    "low": float(c[3]),
                    "close": float(c[4]),
                    "volume": vol,
                    "vwap": float(c[7]) / vol if vol > 0 else float(c[4]),
                    "count": int(c[8]),
                }
            )
        if len(batch_rows) < 1000:
            break
        current_ms = batch_rows[-1][0] + 1
        if batch % 10 == 0:
            last = datetime.fromtimestamp(batch_rows[-1][0] / 1000, tz=timezone.utc)
            print(f"    batch {batch}, up to {last:%Y-%m-%d %H:%M}", flush=True)
        time.sleep(0.12)

    df = pd.DataFrame(rows).drop_duplicates(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
    print(f"    {len(df)} bars: {df.timestamp.iloc[0]} → {df.timestamp.iloc[-1]}", flush=True)
    return df


def slice_last_days(df: pd.DataFrame, days: int = DAYS_1Y) -> pd.DataFrame:
    cutoff = df["timestamp"].max() - timedelta(days=days)
    return df[df["timestamp"] >= cutoff].reset_index(drop=True)


def resample_4h(df: pd.DataFrame) -> pd.DataFrame:
    x = df.set_index("timestamp")
    out = x.resample("4h").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
    )
    if "count" in x.columns:
        out["count"] = x["count"].resample("4h").sum()
    out["vwap"] = (out["high"] + out["low"] + out["close"]) / 3.0
    return out.dropna(subset=["open"]).reset_index()


def write_csv(df: pd.DataFrame, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)
    print(f"  wrote {path} ({len(df)} rows)", flush=True)


def refresh_asset(asset: str, days_5y: int = DAYS_5Y) -> dict:
    sym = asset.lower()
    h1_5y_path = os.path.join(DATA_DIR, f"{sym}_usd_60m_{days_5y}d.csv")
    h1_1y_path = os.path.join(DATA_DIR, f"{sym}_usd_60m_{DAYS_1Y}d.csv")
    h4_1y_path = os.path.join(DATA_DIR, f"{sym}_usd_240m_{DAYS_1Y}d.csv")

    df_5y = fetch_history(asset, "1h", days_5y)
    write_csv(df_5y, h1_5y_path)

    df_1y = slice_last_days(df_5y, DAYS_1Y)
    write_csv(df_1y, h1_1y_path)

    df_4h = resample_4h(df_1y)
    write_csv(df_4h, h4_1y_path)

    return {
        "asset": asset.upper(),
        "bars_5y": len(df_5y),
        "bars_1y": len(df_1y),
        "bars_4h": len(df_4h),
        "first": str(df_5y.timestamp.iloc[0]),
        "last": str(df_5y.timestamp.iloc[-1]),
    }


def refresh_all(assets: tuple[str, ...] = ASSETS) -> list[dict]:
    os.makedirs(DATA_DIR, exist_ok=True)
    print(f"Refreshing market data → {DATA_DIR}", flush=True)
    meta = []
    for asset in assets:
        print(f"\n{asset}:", flush=True)
        meta.append(refresh_asset(asset))
    return meta


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch latest Binance OHLCV into data/")
    parser.add_argument("--assets", nargs="+", default=list(ASSETS), choices=["BTC", "ETH", "btc", "eth"])
    args = parser.parse_args()
    assets = tuple(a.upper() for a in args.assets)

    try:
        meta = refresh_all(assets)
    except requests.RequestException as exc:
        print(f"Fetch failed: {exc}", file=sys.stderr)
        return 1

    print("\nSummary:")
    for m in meta:
        print(f"  {m['asset']}: {m['bars_5y']} 1h bars ({m['first'][:10]} → {m['last'][:10]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
