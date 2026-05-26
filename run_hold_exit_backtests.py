#!/usr/bin/env python3
"""Run hold_exit_rules backtests for ETH + BTC across multiple timeframes."""

from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime, timedelta, timezone

import pandas as pd

RESULTS_DIR = "results"
DATA_DIR = "data"
DAYS = 365
os.makedirs(RESULTS_DIR, exist_ok=True)

# (tf label, file suffix, indicator_tf for ProfessionalIndicators)
TIMEFRAMES = [
    ("1m", "1m", "1h"),
    ("5m", "5m", "1h"),
    ("1h", "60m", "1h"),
    ("4h", "240m", "4h"),
    ("1d", "1440m", "1d"),
    ("1w", "1w", "1d"),
]


def row(label: str, strategy: str, metrics: dict | None, skipped: str | None = None) -> dict:
    if skipped:
        return {"label": label, "strategy": strategy, "skipped": True, "reason": skipped}
    if not metrics:
        return {"label": label, "strategy": strategy, "skipped": True, "reason": "no_trades"}
    pf = metrics.get("profit_factor", 0)
    return {
        "label": label,
        "strategy": strategy,
        "skipped": False,
        "total_trades": metrics.get("total_trades", 0),
        "win_rate": round(metrics.get("win_rate", 0), 2),
        "total_return_pct": round(metrics.get("total_return_pct", 0), 2),
        "max_drawdown": round(metrics.get("max_drawdown", metrics.get("max_drawdown_pct", 0)), 2),
        "profit_factor": pf if pf != float("inf") else "inf",
        "total_pnl": round(metrics.get("total_pnl", 0), 2),
        "exit_reasons": metrics.get("exit_reasons", {}),
        "avg_hold_time_hours": round(metrics.get("avg_hold_time_hours", 0), 1),
        "elapsed_sec": metrics.get("elapsed_sec", 0),
    }


def _asset_path(asset: str, suffix: str) -> str:
    return os.path.join(DATA_DIR, f"{asset.lower()}_usd_{suffix}_{DAYS}d.csv")


def _resample_ohlcv(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    x = df.set_index("timestamp")
    out = x.resample(rule).agg(
        {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
    )
    if "count" in x.columns:
        out["count"] = x["count"].resample(rule).sum()
    if "vwap" in x.columns:
        out["vwap"] = (out["high"] + out["low"] + out["close"]) / 3.0
    return out.dropna(subset=["open"]).reset_index()


def _slice_last_days(df: pd.DataFrame, days: int = DAYS) -> pd.DataFrame:
    cutoff = df["timestamp"].max() - timedelta(days=days)
    return df[df["timestamp"] >= cutoff].reset_index(drop=True)


def _write_csv(df: pd.DataFrame, path: str) -> None:
    df.to_csv(path, index=False)
    print(f"    wrote {path} ({len(df)} bars)", flush=True)


def ensure_local_derived(asset: str) -> None:
    """Build 1h/4h/1w 365d files from what we already have on disk."""
    h1_365 = _asset_path(asset, "60m")
    h4_365 = _asset_path(asset, "240m")
    d1_365 = _asset_path(asset, "1440m")
    w1_365 = _asset_path(asset, "1w")
    h1_long = os.path.join(DATA_DIR, f"{asset.lower()}_usd_60m_1825d.csv")

    if not os.path.isfile(h1_365):
        if os.path.isfile(h1_long):
            df = pd.read_csv(h1_long, parse_dates=["timestamp"])
            _write_csv(_slice_last_days(df), h1_365)
        elif os.path.isfile(d1_365):
            pass  # 1h may arrive via fetch
        else:
            return

    if not os.path.isfile(h4_365) and os.path.isfile(h1_365):
        df = pd.read_csv(h1_365, parse_dates=["timestamp"])
        _write_csv(_resample_ohlcv(df, "4h"), h4_365)

    if not os.path.isfile(w1_365) and os.path.isfile(d1_365):
        df = pd.read_csv(d1_365, parse_dates=["timestamp"])
        _write_csv(_resample_ohlcv(df, "W"), w1_365)


def fetch_binance(asset: str, interval: str, days: int = DAYS) -> pd.DataFrame:
    import requests

    symbol = f"{asset.upper()}USDT"
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    start_ms = now_ms - days * 24 * 3600 * 1000
    url = "https://api.binance.com/api/v3/klines"
    all_candles = []
    current_ms = start_ms
    print(f"    Binance {symbol} {interval} ({days}d)...", flush=True)
    while current_ms < now_ms:
        resp = requests.get(
            url,
            params={"symbol": symbol, "interval": interval, "startTime": current_ms, "endTime": now_ms, "limit": 1000},
            timeout=60,
        )
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        all_candles.extend(batch)
        if len(batch) < 1000:
            break
        current_ms = batch[-1][0] + 1
        time.sleep(0.12)
    rows = []
    for c in all_candles:
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
    return pd.DataFrame(rows).drop_duplicates(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)


def ensure_data(assets: list[str], timeframes: list[str], do_fetch: bool) -> None:
    binance_interval = {"1m": "1m", "5m": "5m", "1h": "1h", "4h": "4h", "1d": "1d"}

    for asset in assets:
        ensure_local_derived(asset)
        for tf_label, suffix, _ in TIMEFRAMES:
            if tf_label not in timeframes:
                continue
            if tf_label == "1w":
                continue
            path = _asset_path(asset, suffix)
            if os.path.isfile(path) and os.path.getsize(path) > 500:
                continue
            if tf_label == "4h" and os.path.isfile(_asset_path(asset, "60m")):
                df = pd.read_csv(_asset_path(asset, "60m"), parse_dates=["timestamp"])
                _write_csv(_resample_ohlcv(df, "4h"), path)
                continue
            if not do_fetch:
                continue
            if tf_label not in binance_interval:
                continue
            df = fetch_binance(asset, binance_interval[tf_label], DAYS)
            _write_csv(df, path)
            time.sleep(0.2)

        ensure_local_derived(asset)


def resolve_path(asset: str, tf_label: str, suffix: str) -> str | None:
    path = _asset_path(asset, suffix)
    if os.path.isfile(path) and os.path.getsize(path) > 500:
        return path
    if tf_label == "1h":
        long_path = os.path.join(DATA_DIR, f"{asset.lower()}_usd_60m_1825d.csv")
        if os.path.isfile(long_path):
            return long_path
    return None


def run_professional(data_file: str, indicator_tf: str, label: str) -> dict:
    import config_professional as config
    from backtest_professional import ProfessionalBacktester

    config.TIMEFRAME = indicator_tf
    t0 = time.time()
    bt = ProfessionalBacktester(data_file=data_file, leverage=config.LEVERAGE, capital=config.CAPITAL)
    bt.load_data()
    if len(bt.df) < 220 and indicator_tf in ("1d", "1w"):
        return row(label, "Professional", None, f"insufficient_bars ({len(bt.df)})")
    try:
        bt.prepare_data()
    except ValueError as e:
        return row(label, "Professional", None, str(e))
    bt.run_backtest()
    m = bt.calculate_metrics()
    if m:
        m["elapsed_sec"] = round(time.time() - t0, 1)
    return row(label, "Professional", m)


def run_bear(data_file: str, indicator_tf: str, label: str) -> dict:
    import config_professional as config
    from backtest_bear_chento import BearChentoBacktester

    config.TIMEFRAME = indicator_tf
    t0 = time.time()
    bt = BearChentoBacktester(data_file=data_file, leverage=config.LEVERAGE, capital=config.CAPITAL)
    bt.load_data()
    if len(bt.df) < 220 and indicator_tf in ("1d", "1w"):
        return row(label, "Bear Chento", None, f"insufficient_bars ({len(bt.df)})")
    try:
        bt.prepare_data()
    except ValueError as e:
        return row(label, "Bear Chento", None, str(e))
    bt.run_backtest()
    m = bt.calculate_metrics()
    if m:
        m["elapsed_sec"] = round(time.time() - t0, 1)
    return row(label, "Bear Chento", m)


def run_momentum(data_file: str, label: str) -> dict:
    import config
    from backtester import Backtester

    config.TIMEFRAME = "1h"
    t0 = time.time()
    bt = Backtester(data_file=data_file, leverage=config.LEVERAGE, capital=config.CAPITAL)
    bt.df = pd.read_csv(data_file, parse_dates=["timestamp"])
    if len(bt.df) > 8760:
        bt.df = bt.df.tail(8760).reset_index(drop=True)
    bt.prepare_data()
    bt.run_backtest()
    m = bt.calculate_metrics()
    if m:
        exits = [t for t in bt.trades if t["action"] == "EXIT"]
        reasons = {}
        for t in exits:
            r = t.get("exit_reason", "?")
            reasons[r] = reasons.get(r, 0) + 1
        m["exit_reasons"] = reasons
        hold = [t.get("hold_time_hours", 0) for t in exits if t.get("hold_time_hours")]
        m["avg_hold_time_hours"] = sum(hold) / len(hold) if hold else 0
        m["elapsed_sec"] = round(time.time() - t0, 1)
    return row(label, "Momentum", m)


def run_liquidity(assets: list[str]) -> list[dict]:
    from backtest_liquidity_strategy import backtest_asset, metrics, INITIAL_CAPITAL

    out = []
    for sym in assets:
        path = _asset_path(sym, "60m")
        if not os.path.isfile(path):
            path = os.path.join(DATA_DIR, f"{sym.lower()}_usd_60m_1825d.csv")
        if not os.path.isfile(path):
            out.append(row(f"Liq {sym} B", "ICT Reversal", None, f"missing hourly data"))
            continue
        print(f"  Liquidity {sym} ({path}) ...", flush=True)
        t0 = time.time()
        trades, eq, _ = backtest_asset(sym, path, INITIAL_CAPITAL / 2, variant="B")
        m = metrics(trades, eq, INITIAL_CAPITAL / 2)
        if m:
            dt = pd.DataFrame(trades) if trades else pd.DataFrame()
            m = {
                "total_trades": m["n_trades"],
                "win_rate": m["win_rate"],
                "total_return_pct": m["total_ret_pct"],
                "max_drawdown": m["max_dd_pct"],
                "profit_factor": m["profit_factor"],
                "total_pnl": m["total_pnl"],
                "exit_reasons": dt["exit_reason"].value_counts().to_dict() if len(dt) else {},
                "avg_hold_time_hours": m.get("avg_hold_h", 0),
                "elapsed_sec": round(time.time() - t0, 1),
            }
        out.append(row(f"Liq {sym} B", "ICT Reversal", m))
    return out


def print_table(rows: list[dict]) -> None:
    print("\n" + "=" * 92)
    print("HOLD-EXIT BACKTEST SUMMARY (no stop-loss)")
    print("=" * 92)
    print(f"{'Run':<24} {'Strategy':<14} {'Trades':>6} {'Win%':>7} {'Return%':>9} {'MaxDD%':>8} {'PF':>6} {'Hold(h)':>8}")
    print("-" * 92)
    for r in rows:
        if r.get("skipped"):
            print(f"{r['label']:<24} {r['strategy']:<14}  SKIP — {r.get('reason', '')}")
            continue
        pf = r.get("profit_factor", 0)
        pf_s = f"{pf:.2f}" if isinstance(pf, (int, float)) else str(pf)
        print(
            f"{r['label']:<24} {r['strategy']:<14} "
            f"{r.get('total_trades', 0):>6} "
            f"{r.get('win_rate', 0):>6.1f}% "
            f"{r.get('total_return_pct', 0):>8.2f}% "
            f"{r.get('max_drawdown', 0):>7.2f}% "
            f"{pf_s:>6} "
            f"{r.get('avg_hold_time_hours', 0):>7.1f}"
        )
        ex = r.get("exit_reasons")
        if ex:
            print(f"    exits: {ex}")
    print("=" * 92)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fetch", action="store_true", help="Fetch missing Binance 365d CSVs")
    parser.add_argument("--assets", nargs="+", default=["ETH", "BTC"], choices=["ETH", "BTC"])
    parser.add_argument(
        "--timeframes",
        nargs="+",
        default=[t[0] for t in TIMEFRAMES],
        choices=[t[0] for t in TIMEFRAMES],
    )
    parser.add_argument("--no-bear", action="store_true")
    parser.add_argument("--no-momentum", action="store_true")
    parser.add_argument("--no-liquidity", action="store_true")
    parser.add_argument("--skip-slow", action="store_true", help="Skip 1m timeframe")
    parser.add_argument("--leverage", type=float, default=None, help="Override LEVERAGE in configs")
    parser.add_argument("--fixed-capital", type=float, default=None, help="Enable fixed capital mode (e.g. 1000)")
    args = parser.parse_args()

    tfs = [t for t in args.timeframes if not (args.skip_slow and t == "1m")]
    from hold_exit_rules import exit_rules_description
    import config_professional as cp
    import config as momentum_config

    if args.leverage is not None:
        cp.LEVERAGE = args.leverage
        momentum_config.LEVERAGE = args.leverage
    if args.fixed_capital is not None:
        cp.USE_FIXED_CAPITAL = True
        cp.FIXED_CAPITAL = args.fixed_capital
        cp.CAPITAL = args.fixed_capital
        momentum_config.USE_FIXED_CAPITAL = True
        momentum_config.FIXED_CAPITAL = args.fixed_capital
        momentum_config.CAPITAL = args.fixed_capital

    mode = f"${cp.FIXED_CAPITAL:,.0f} fixed" if cp.USE_FIXED_CAPITAL else f"${cp.CAPITAL:,.0f} compounding"
    print(f"Capital mode: {mode}")
    print(f"Leverage: {cp.LEVERAGE}x")
    print("Exit rules:", exit_rules_description(cp.LEVERAGE))
    print("Assets:", ", ".join(args.assets))
    print("Timeframes:", ", ".join(tfs))
    ensure_data(args.assets, tfs, args.fetch)

    rows: list[dict] = []
    bear_tfs = {"1h", "4h", "1d"}

    for asset in args.assets:
        for tf_label, suffix, indicator_tf in TIMEFRAMES:
            if tf_label not in tfs:
                continue
            path = resolve_path(asset, tf_label, suffix)
            label = f"{asset} {tf_label} {DAYS}d"
            if not path:
                rows.append(row(label, "Professional", None, "missing data"))
                continue
            print(f"\n▶ {label} Professional ...", flush=True)
            rows.append(run_professional(path, indicator_tf, label))
            if not args.no_bear and tf_label in bear_tfs:
                print(f"▶ {label} Bear Chento ...", flush=True)
                rows.append(run_bear(path, indicator_tf, label))

        if not args.no_momentum:
            h1 = resolve_path(asset, "1h", "60m")
            if h1:
                print(f"\n▶ {asset} Momentum 1h ...", flush=True)
                rows.append(run_momentum(h1, f"{asset} 1h {DAYS}d"))

    if not args.no_liquidity:
        print("\n▶ Liquidity strategies (1h) ...", flush=True)
        rows.extend(run_liquidity(args.assets))

    print_table(rows)
    lev = int(cp.LEVERAGE)
    out = os.path.join(RESULTS_DIR, f"hold_exit_backtest_summary_{lev}x.json")
    with open(out, "w") as f:
        json.dump({"leverage": lev, "rows": rows}, f, indent=2, default=str)
    # latest alias
    with open(os.path.join(RESULTS_DIR, "hold_exit_backtest_summary.json"), "w") as f:
        json.dump({"leverage": lev, "rows": rows}, f, indent=2, default=str)
    print(f"\nSaved {out}")


if __name__ == "__main__":
    main()
