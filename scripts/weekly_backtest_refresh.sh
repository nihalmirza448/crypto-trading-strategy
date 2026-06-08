#!/bin/bash
# Weekly: fetch latest Binance OHLCV → run hybrid hold-window backtest sweep.
# Installed via ~/Library/LaunchAgents/com.nihal.crypto-weekly-backtest.plist
set -uo pipefail

export PATH="/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"

REPO="/Users/nihal/cursor-projects/crypto trading strategy"
LOG="$REPO/results/weekly_backtest_refresh.log"
PYTHON="$REPO/.venv/bin/python"

ts() { date "+%Y-%m-%dT%H:%M:%S"; }

cd "$REPO" || exit 1
mkdir -p results

{
  echo "$(ts) === weekly backtest refresh start ==="

  echo "$(ts) fetching historical data..."
  "$PYTHON" scripts/fetch_historical_data.py --assets BTC ETH \
    || { echo "$(ts) fetch failed"; exit 1; }

  echo "$(ts) running hybrid 100x window sweep..."
  "$PYTHON" backtest_hybrid_window_sweep.py --leverage 100 \
    || { echo "$(ts) backtest failed"; exit 1; }

  echo "$(ts) === weekly backtest refresh ok ==="
} >> "$LOG" 2>&1
