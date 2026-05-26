#!/usr/bin/env python3
"""
Sweep leverage with fixed $1,000 capital (no compounding per trade).

Compares 20x, 25x, 50x, 100x on Professional strategy across ETH/BTC timeframes.
"""

from __future__ import annotations

import json
import os
import time

import pandas as pd

import config_professional as config
from indicators_professional import ProfessionalIndicators
from strategy_professional import ProfessionalStrategy

RESULTS_DIR = "results"
FIXED_CAPITAL = 1000.0
LEVERAGES = [20, 25, 50, 100]

RUNS = [
    ("ETH", "1h", "data/eth_usd_60m_365d.csv", "1h"),
    ("ETH", "4h", "data/eth_usd_240m_365d.csv", "4h"),
    ("BTC", "1h", "data/btc_usd_60m_365d.csv", "1h"),
    ("BTC", "4h", "data/btc_usd_240m_365d.csv", "4h"),
]


def run_one(df: pd.DataFrame, leverage: float, indicator_tf: str) -> dict | None:
    config.LEVERAGE = leverage
    config.USE_FIXED_CAPITAL = True
    config.FIXED_CAPITAL = FIXED_CAPITAL
    config.CAPITAL = FIXED_CAPITAL
    config.TIMEFRAME = indicator_tf

    strategy = ProfessionalStrategy(leverage=leverage, capital=FIXED_CAPITAL)
    trades = strategy.run(df.copy())
    exits = [t for t in trades if t.get("action") == "EXIT"]
    if not exits:
        return None

    wins = [t for t in exits if t["net_pnl"] > 0]
    total_pnl = sum(t["net_pnl"] for t in exits)
    gp = sum(t["net_pnl"] for t in wins)
    gl = abs(sum(t["net_pnl"] for t in exits if t["net_pnl"] <= 0))
    pf = gp / gl if gl > 0 else float("inf")
    reasons: dict = {}
    for t in exits:
        r = t.get("exit_reason", "?")
        reasons[r] = reasons.get(r, 0) + 1

    final_equity = strategy.equity
    return {
        "leverage": leverage,
        "total_trades": len(exits),
        "win_rate": round(len(wins) / len(exits) * 100, 2),
        "total_pnl": round(total_pnl, 2),
        "total_return_pct": round((final_equity - FIXED_CAPITAL) / FIXED_CAPITAL * 100, 2),
        "final_equity": round(final_equity, 2),
        "profit_factor": round(pf, 3) if pf != float("inf") else "inf",
        "avg_hold_hours": round(sum(t["hold_time_hours"] for t in exits) / len(exits), 1),
        "exit_reasons": reasons,
    }


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    config.USE_FIXED_CAPITAL = True
    config.FIXED_CAPITAL = FIXED_CAPITAL

    print(f"Fixed capital: ${FIXED_CAPITAL:,.0f} (no compounding)")
    print(f"Leverage sweep: {LEVERAGES}\n")

    all_rows = []
    prepared: dict[str, pd.DataFrame] = {}

    for asset, tf_label, path, indicator_tf in RUNS:
        if not os.path.isfile(path):
            print(f"SKIP {asset} {tf_label}: missing {path}")
            continue
        key = f"{asset}_{indicator_tf}"
        if key not in prepared:
            print(f"Loading + indicators {asset} {tf_label} ...", flush=True)
            t0 = time.time()
            df = pd.read_csv(path, parse_dates=["timestamp"])
            config.TIMEFRAME = indicator_tf
            prepared[key] = ProfessionalIndicators.add_all_indicators(df, timeframe=indicator_tf)
            print(f"  done in {time.time() - t0:.1f}s", flush=True)

        df = prepared[key]
        for lev in LEVERAGES:
            print(f"  {asset} {tf_label} @ {lev}x ...", flush=True)
            t0 = time.time()
            m = run_one(df, lev, indicator_tf)
            elapsed = round(time.time() - t0, 1)
            if not m:
                all_rows.append({
                    "asset": asset,
                    "timeframe": tf_label,
                    "leverage": lev,
                    "skipped": True,
                    "reason": "no_trades",
                })
                continue
            all_rows.append({"asset": asset, "timeframe": tf_label, "elapsed_sec": elapsed, **m})

    if not all_rows:
        print("No results.")
        return

    df_out = pd.DataFrame([r for r in all_rows if not r.get("skipped")])
    out_csv = os.path.join(RESULTS_DIR, "leverage_sweep_fixed_1k.csv")
    df_out.to_csv(out_csv, index=False)

    print("\n" + "=" * 90)
    print("LEVERAGE SWEEP — $1,000 fixed capital, Professional strategy")
    print("=" * 90)
    if len(df_out):
        cols = ["asset", "timeframe", "leverage", "total_trades", "win_rate", "total_return_pct", "profit_factor", "total_pnl"]
        print(df_out[cols].to_string(index=False))

    # Best per asset/tf
    print("\n" + "-" * 90)
    print("BEST BY RETURN %")
    for (asset, tf), g in df_out.groupby(["asset", "timeframe"]):
        best = g.loc[g["total_return_pct"].idxmax()]
        print(
            f"  {asset} {tf}: {int(best['leverage'])}x — "
            f"return {best['total_return_pct']:+.1f}%  WR {best['win_rate']:.1f}%  "
            f"trades {int(best['total_trades'])}  PF {best['profit_factor']}"
        )

    print("\nBEST BY WIN RATE (min 5 trades)")
    eligible = df_out[df_out["total_trades"] >= 5]
    for (asset, tf), g in eligible.groupby(["asset", "timeframe"]):
        best = g.loc[g["win_rate"].idxmax()]
        print(
            f"  {asset} {tf}: {int(best['leverage'])}x — "
            f"WR {best['win_rate']:.1f}%  return {best['total_return_pct']:+.1f}%  "
            f"trades {int(best['total_trades'])}"
        )

    # Overall best return
    if len(df_out):
        overall_ret = df_out.loc[df_out["total_return_pct"].idxmax()]
        overall_wr = eligible.loc[eligible["win_rate"].idxmax()] if len(eligible) else overall_ret
        print("\nOVERALL (all runs)")
        print(
            f"  Highest return: {overall_ret['asset']} {overall_ret['timeframe']} "
            f"{int(overall_ret['leverage'])}x → {overall_ret['total_return_pct']:+.1f}% "
            f"(WR {overall_ret['win_rate']:.1f}%, {int(overall_ret['total_trades'])} trades)"
        )
        if len(eligible):
            print(
                f"  Highest win rate (≥5 trades): {overall_wr['asset']} {overall_wr['timeframe']} "
                f"{int(overall_wr['leverage'])}x → {overall_wr['win_rate']:.1f}% "
                f"(return {overall_wr['total_return_pct']:+.1f}%)"
            )

    out_json = os.path.join(RESULTS_DIR, "leverage_sweep_fixed_1k.json")
    with open(out_json, "w") as f:
        json.dump(
            {"fixed_capital": FIXED_CAPITAL, "leverages": LEVERAGES, "runs": all_rows},
            f,
            indent=2,
            default=str,
        )
    print(f"\nSaved {out_csv}")
    print(f"Saved {out_json}")


if __name__ == "__main__":
    main()
