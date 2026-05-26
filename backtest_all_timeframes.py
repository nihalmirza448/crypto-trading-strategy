"""
Backtest Professional (+ optional Bear Chento) across multiple timeframes, 1 year ETH.

Data: Binance ETHUSDT (public). Daily can use existing CQ file if present.
Weekly: resampled from daily.

Usage:
  python backtest_all_timeframes.py
  python backtest_all_timeframes.py --skip-fetch
  python backtest_all_timeframes.py --only 1h 4h 1d
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import datetime, timezone

import pandas as pd

DAYS = 365
SYMBOL = "ETHUSDT"
DATA_DIR = "data"
RESULTS_DIR = "results"

# (label, filename suffix, config TIMEFRAME for indicators, binance interval or None)
TIMEFRAME_SPECS = [
    ("1d", "1440m", "1d", "1d"),
    ("1w", "1w", "1d", None),  # built from daily
    ("4h", "240m", "4h", "4h"),
    ("1h", "60m", "1h", "1h"),
    ("5m", "5m", "1h", "5m"),
    ("1m", "1m", "1h", "1m"),
]


def fetch_binance_klines(symbol: str, interval: str, start_ms: int, end_ms: int, limit: int = 1000):
    import requests

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


def candles_to_df(candles) -> pd.DataFrame:
    rows = []
    for c in candles:
        v = float(c[5])
        rows.append(
            {
                "timestamp": datetime.fromtimestamp(c[0] / 1000, tz=timezone.utc).replace(tzinfo=None),
                "open": float(c[1]),
                "high": float(c[2]),
                "low": float(c[3]),
                "close": float(c[4]),
                "volume": v,
                "vwap": float(c[7]) / v if v > 0 else float(c[4]),
                "count": int(c[8]),
            }
        )
    df = pd.DataFrame(rows)
    return df.drop_duplicates(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)


def fetch_binance_history(interval: str, days: int = DAYS) -> pd.DataFrame:
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    start_ms = now_ms - days * 24 * 3600 * 1000
    all_candles = []
    current_ms = start_ms
    print(f"  Binance {SYMBOL} {interval} ({days}d)...", flush=True)
    while current_ms < now_ms:
        batch = fetch_binance_klines(SYMBOL, interval, current_ms, now_ms)
        if not batch:
            break
        all_candles.extend(batch)
        if len(batch) < 1000:
            break
        current_ms = batch[-1][0] + 1
        time.sleep(0.12)
    df = candles_to_df(all_candles)
    print(f"    → {len(df)} bars", flush=True)
    return df


def build_weekly_from_daily(daily_path: str, out_path: str) -> pd.DataFrame:
    df = pd.read_csv(daily_path, parse_dates=["timestamp"])
    x = df.set_index("timestamp")
    w = x.resample("W").agg(
        {
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum",
            "count": "sum",
        }
    )
    w["vwap"] = (w["high"] + w["low"] + w["close"]) / 3.0
    w = w.dropna(subset=["open"]).reset_index()
    w.to_csv(out_path, index=False)
    print(f"    → weekly {len(w)} bars → {out_path}", flush=True)
    return w


def eth_path(suffix: str) -> str:
    return os.path.join(DATA_DIR, f"eth_usd_{suffix}_{DAYS}d.csv")


def ensure_data(skip_fetch: bool, only: list[str] | None) -> dict[str, str]:
    os.makedirs(DATA_DIR, exist_ok=True)
    paths: dict[str, str] = {}
    specs = TIMEFRAME_SPECS
    if only:
        specs = [s for s in specs if s[0] in only]

    daily_path = eth_path("1440m")
    if not skip_fetch:
        for label, suffix, _tf, interval in specs:
            if interval is None:
                continue
            out = eth_path(suffix)
            if label == "1d" and os.path.isfile(out) and os.path.getsize(out) > 1000:
                # keep CQ/Binance daily if already fetched
                print(f"  Using existing {out}", flush=True)
            else:
                df = fetch_binance_history(interval, DAYS)
                df.to_csv(out, index=False)
            paths[label] = out

        if any(s[0] == "1w" for s in specs):
            if not os.path.isfile(daily_path):
                df = fetch_binance_history("1d", DAYS)
                df.to_csv(daily_path, index=False)
            wpath = eth_path("1w")
            build_weekly_from_daily(daily_path, wpath)
            paths["1w"] = wpath
    else:
        for label, suffix, _tf, interval in specs:
            if interval is None and label == "1w":
                paths["1w"] = eth_path("1w")
            else:
                paths[label] = eth_path(suffix)

    for label, suffix, _tf, interval in specs:
        p = paths.get(label) or eth_path(suffix if interval else "1w")
        if not os.path.isfile(p):
            raise FileNotFoundError(f"Missing {p}; run without --skip-fetch")
        paths[label] = p
    return paths


def run_one(
    label: str,
    data_file: str,
    indicator_tf: str,
    *,
    bear: bool = False,
) -> dict | None:
    import config_professional as config
    from backtest_professional import ProfessionalBacktester
    from backtest_bear_chento import BearChentoBacktester

    config.TIMEFRAME = indicator_tf
    cls = BearChentoBacktester if bear else ProfessionalBacktester
    name = f"Bear Chento" if bear else "Professional"

    print(f"\n{'='*70}\n{label} | {name} | {data_file}\n{'='*70}", flush=True)
    t0 = time.time()
    bt = cls(data_file=data_file, leverage=config.LEVERAGE, capital=config.CAPITAL)
    bt.load_data()
    n = len(bt.df)
    if n < 220 and label == "1w":
        print(f"  SKIP: only {n} bars — need ~220+ for EMA200 / order-block validation", flush=True)
        return {"timeframe_label": label, "strategy": name, "skipped": True, "reason": "insufficient_bars", "bars": n}
    try:
        bt.prepare_data()
    except ValueError as e:
        print(f"  SKIP prepare_data: {e}", flush=True)
        return {"timeframe_label": label, "strategy": name, "skipped": True, "reason": str(e), "bars": n}
    bt.run_backtest()
    metrics = bt.calculate_metrics()
    elapsed = time.time() - t0
    if metrics:
        metrics["timeframe_label"] = label
        metrics["strategy"] = name
        metrics["data_file"] = data_file
        metrics["elapsed_sec"] = round(elapsed, 1)
        if bear:
            bt.save_results(metrics, tag=f"multi_{label}_bear_{DAYS}d")
        else:
            bt.save_results(metrics)
        print(
            f"  trades={metrics.get('total_trades')} "
            f"win_rate={metrics.get('win_rate', 0):.1f}% "
            f"return={metrics.get('total_return_pct', 0):.2f}% "
            f"PF={metrics.get('profit_factor', 0)} "
            f"({elapsed:.0f}s)",
            flush=True,
        )
    else:
        print(f"  No trades ({elapsed:.0f}s)", flush=True)
    return metrics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-fetch", action="store_true")
    parser.add_argument("--only", nargs="+", choices=[s[0] for s in TIMEFRAME_SPECS])
    parser.add_argument("--no-bear", action="store_true", help="Skip bear chento runs")
    args = parser.parse_args()

    print("=" * 70)
    print(f"MULTI-TIMEFRAME BACKTEST — ETH, {DAYS} days")
    from hold_exit_rules import exit_rules_description
    import config_professional as config
    print(f"Exits: {exit_rules_description(config.LEVERAGE)}")
    print("=" * 70)

    paths = ensure_data(args.skip_fetch, args.only)
    tf_map = {s[0]: s[2] for s in TIMEFRAME_SPECS}

    rows = []
    bear_labels = {"1d", "4h", "1h"}  # weekly: too few bars for regime stack

    for label in paths:
        indicator_tf = tf_map[label]
        m = run_one(label, paths[label], indicator_tf, bear=False)
        if m:
            rows.append(m)
        if not args.no_bear and label in bear_labels:
            mb = run_one(label, paths[label], indicator_tf, bear=True)
            if mb:
                rows.append(mb)

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"{'TF':<6} {'Strategy':<14} {'Trades':>6} {'Win%':>7} {'Return%':>9} {'MaxDD%':>8} {'PF':>6} {'Sec':>5}")
    print("-" * 70)
    for m in rows:
        if m.get("skipped"):
            print(
                f"{m.get('timeframe_label','?'):<6} "
                f"{m.get('strategy','?'):<14} "
                f"  SKIP ({m.get('reason', '')})"
            )
            continue
        pf = m.get("profit_factor", 0)
        pf_s = f"{pf:.2f}" if isinstance(pf, (int, float)) and pf != float("inf") else str(pf)
        print(
            f"{m.get('timeframe_label','?'):<6} "
            f"{m.get('strategy','?'):<14} "
            f"{m.get('total_trades',0):>6} "
            f"{m.get('win_rate',0):>6.1f}% "
            f"{m.get('total_return_pct',0):>8.2f}% "
            f"{m.get('max_drawdown_pct',0):>7.2f}% "
            f"{pf_s:>6} "
            f"{m.get('elapsed_sec',0):>5}"
        )

    out_csv = os.path.join(RESULTS_DIR, f"multi_timeframe_summary_{DAYS}d.csv")
    os.makedirs(RESULTS_DIR, exist_ok=True)
    if rows:
        pd.DataFrame(rows).to_csv(out_csv, index=False)
        print(f"\nSaved {out_csv}")


if __name__ == "__main__":
    main()
