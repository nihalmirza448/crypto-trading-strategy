"""
Fetch BTC OHLCV data from Binance public API (no auth needed)
Saves to data/btc_usd_60m_1825d.csv matching ETH data format

Prefer: python scripts/fetch_historical_data.py --assets BTC ETH
"""
import os
import sys

REPO = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(REPO, "scripts"))
from fetch_historical_data import refresh_asset  # noqa: E402

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    refresh_asset("BTC")
