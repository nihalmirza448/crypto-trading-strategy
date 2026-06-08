#!/usr/bin/env python3
"""
Hybrid strategy backtest — sweep hold windows at a given leverage.

Default: 100x, windows 4/8/12/24/48h, ETH+BTC 1h (365d + 5y).

Outputs:
  results/hybrid_{leverage}x_window_sweep.json
  results/hybrid_{leverage}x_window_sweep.csv
  results/latest_hybrid_window_sweep.json  (alias)
"""

from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime

import pandas as pd

import config_professional as config
from indicators_professional import ProfessionalIndicators
from strategy_hybrid import HybridStrategy

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(REPO_ROOT, "data")
RESULTS_DIR = os.path.join(REPO_ROOT, "results")
FIXED = 1000.0

DEFAULT_DATASETS = [
    ("ETH", "365d", "eth_usd_60m_365d.csv"),
    ("BTC", "365d", "btc_usd_60m_365d.csv"),
    ("ETH", "5y", "eth_usd_60m_1825d.csv"),
    ("BTC", "5y", "btc_usd_60m_1825d.csv"),
]
DEFAULT_WINDOWS = [4, 8, 12, 24, 48]


def run_hybrid(df: pd.DataFrame, leverage: float, window_h: float) -> dict:
    config.LEVERAGE = leverage
    config.HOLD_WINDOW_END_HOURS = window_h
    config.USE_FIXED_CAPITAL = True
    config.FIXED_CAPITAL = FIXED
    config.CAPITAL = FIXED

    strat = HybridStrategy(leverage=leverage, capital=FIXED)
    trades = strat.run(df.copy())
    if strat.position is not None:
        trades.append(strat.exit_position(df, len(df) - 1, "eod_force", 1.0))

    exits = [t for t in trades if t.get("action") == "EXIT"]
    entries = [t for t in trades if t.get("action") == "ENTER"]
    if not exits:
        return {"total_trades": 0}

    wins = [t for t in exits if t["net_pnl"] > 0]
    gp = sum(t["net_pnl"] for t in wins)
    gl = abs(sum(t["net_pnl"] for t in exits if t["net_pnl"] <= 0))
    pf = gp / gl if gl > 0 else float("inf")

    eq = FIXED
    peak = FIXED
    max_dd = 0.0
    for t in exits:
        eq += t["net_pnl"]
        peak = max(peak, eq)
        dd = (eq - peak) / peak * 100 if peak > 0 else 0
        max_dd = min(max_dd, dd)

    reasons: dict[str, int] = {}
    for t in exits:
        r = t.get("exit_reason", "?")
        reasons[r] = reasons.get(r, 0) + 1

    modes: dict[str, int] = {}
    for t in entries:
        d = t.get("confluence_details") or {}
        m = d.get("mode", "?")
        modes[m] = modes.get(m, 0) + 1

    hold_times = [t["hold_time_hours"] for t in exits]
    return {
        "total_trades": len(exits),
        "win_rate": round(len(wins) / len(exits) * 100, 1),
        "total_return_pct": round((eq - FIXED) / FIXED * 100, 2),
        "final_equity": round(eq, 2),
        "max_drawdown_pct": round(max_dd, 2),
        "profit_factor": round(pf, 2) if pf != float("inf") else "inf",
        "avg_hold_hours": round(sum(hold_times) / len(hold_times), 1),
        "exit_reasons": reasons,
        "entry_modes": modes,
        "worst_trade": round(min(t["net_pnl"] for t in exits), 2),
        "best_trade": round(max(t["net_pnl"] for t in exits), 2),
        "window_end_count": reasons.get("window_end", 0),
        "data_last_bar": str(df["timestamp"].iloc[-1]),
    }


def run_sweep(
    leverage: float = 100.0,
    windows: list[int] | None = None,
    datasets: list[tuple[str, str, str]] | None = None,
) -> list[dict]:
    windows = windows or DEFAULT_WINDOWS
    datasets = datasets or DEFAULT_DATASETS
    os.makedirs(RESULTS_DIR, exist_ok=True)

    prepared: dict[str, pd.DataFrame] = {}
    rows: list[dict] = []

    for asset, label, filename in datasets:
        path = os.path.join(DATA_DIR, filename)
        if not os.path.isfile(path):
            print(f"SKIP {asset} {label}: missing {path}", flush=True)
            continue
        key = f"{asset}_{filename}"
        if key not in prepared:
            print(f"Indicators {asset} {label} ({filename})...", flush=True)
            df = pd.read_csv(path, parse_dates=["timestamp"])
            config.TIMEFRAME = "1h"
            prepared[key] = ProfessionalIndicators.add_all_indicators(df, timeframe="1h")
            print(f"  {len(prepared[key])} bars, last={prepared[key].timestamp.iloc[-1]}", flush=True)

        df = prepared[key]
        for w in windows:
            t0 = time.time()
            m = run_hybrid(df, leverage, float(w))
            m.update(
                {
                    "asset": asset,
                    "dataset": label,
                    "leverage": leverage,
                    "window_h": w,
                    "bars": len(df),
                    "elapsed_sec": round(time.time() - t0, 1),
                }
            )
            rows.append(m)
            if m.get("total_trades"):
                print(
                    f"  {asset} {label} {w:>2}h: trades={m['total_trades']:>4} "
                    f"WR={m['win_rate']:>5.1f}% ret={m['total_return_pct']:>9.1f}%",
                    flush=True,
                )
            else:
                print(f"  {asset} {label} {w:>2}h: no trades", flush=True)

    return rows


def save_results(rows: list[dict], leverage: float) -> dict:
    payload = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "leverage": leverage,
        "windows": DEFAULT_WINDOWS,
        "rows": rows,
    }
    lev_tag = int(leverage) if leverage == int(leverage) else leverage
    json_path = os.path.join(RESULTS_DIR, f"hybrid_{lev_tag}x_window_sweep.json")
    csv_path = os.path.join(RESULTS_DIR, f"hybrid_{lev_tag}x_window_sweep.csv")
    latest_path = os.path.join(RESULTS_DIR, "latest_hybrid_window_sweep.json")

    with open(json_path, "w") as f:
        json.dump(payload, f, indent=2, default=str)
    with open(latest_path, "w") as f:
        json.dump(payload, f, indent=2, default=str)

    flat = []
    for r in rows:
        row = {k: v for k, v in r.items() if k not in ("exit_reasons", "entry_modes")}
        row["exit_reasons"] = json.dumps(r.get("exit_reasons", {}))
        row["entry_modes"] = json.dumps(r.get("entry_modes", {}))
        flat.append(row)
    pd.DataFrame(flat).to_csv(csv_path, index=False)

    return {"json": json_path, "csv": csv_path, "latest": latest_path}


def print_table(rows: list[dict], dataset: str = "365d") -> None:
    subset = [r for r in rows if r.get("dataset") == dataset and r.get("total_trades")]
    if not subset:
        return
    print(f"\n{'=' * 100}")
    print(f"HYBRID WINDOW SWEEP — {dataset} (leverage {subset[0]['leverage']}x)")
    print(f"{'=' * 100}")
    print(f"{'Asset':<5} {'Win':>4} {'Trades':>6} {'WR%':>6} {'Return%':>10} {'MaxDD%':>8} {'WinEnd':>6}")
    print("-" * 100)
    for r in sorted(subset, key=lambda x: (x["asset"], x["window_h"])):
        print(
            f"{r['asset']:<5} {r['window_h']:>3}h {r['total_trades']:>6} "
            f"{r['win_rate']:>5.1f}% {r['total_return_pct']:>9.1f}% "
            f"{r['max_drawdown_pct']:>7.1f}% {r.get('window_end_count', 0):>6}"
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--leverage", type=float, default=100.0)
    parser.add_argument("--windows", nargs="+", type=int, default=DEFAULT_WINDOWS)
    args = parser.parse_args()

    print(f"Hybrid window sweep @ {args.leverage}x, windows={args.windows}", flush=True)
    rows = run_sweep(leverage=args.leverage, windows=args.windows)
    paths = save_results(rows, args.leverage)
    print_table(rows, "365d")
    print_table(rows, "5y")
    print(f"\nSaved {paths['json']}")
    print(f"Saved {paths['csv']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
