#!/usr/bin/env python3
"""
Command-line tool to get instant trading recommendations
Combines CoinGlass data + Parabolic Bull Run analysis
"""
import argparse
import sys
import pandas as pd
from datetime import datetime
import config
from coinglass_client import CoinGlassClient
from recommendation_engine import RecommendationEngine
from indicators import TechnicalIndicators


def main():
    parser = argparse.ArgumentParser(
        description='Get ETH trading recommendation with CoinGlass data'
    )
    parser.add_argument(
        '--fetch-coinglass',
        action='store_true',
        help='Fetch live data from CoinGlass API (slower but current)'
    )
    parser.add_argument(
        '--symbol',
        default='ETH',
        help='Trading symbol (default: ETH)'
    )
    parser.add_argument(
        '--save',
        action='store_true',
        help='Save recommendation to JSON file'
    )
    parser.add_argument(
        '--parabolic-only',
        action='store_true',
        help='Only check parabolic bull run status'
    )

    args = parser.parse_args()

    print("\n" + "="*70)
    print("🚀 ETHEREUM TRADING RECOMMENDATION SYSTEM")
    print("="*70)

    # 1. Load historical data
    print(f"\n📊 Loading historical data...")

    # Try to find available data files
    import os
    import glob

    data_files = glob.glob(f'{config.DATA_DIR}/eth_usd_*_{config.LOOKBACK_DAYS}d.csv')
    if not data_files:
        # Try any available data file
        data_files = glob.glob(f'{config.DATA_DIR}/eth_usd_*.csv')

    if not data_files:
        print(f"\n❌ ERROR: No data files found in {config.DATA_DIR}/")
        print("   Run this first: python data_collector.py --days 1825")
        sys.exit(1)

    # Use the first available file
    data_file = sorted(data_files)[-1]  # Use most recent or largest
    print(f"   Using data file: {os.path.basename(data_file)}")

    try:
        df = pd.read_csv(data_file)
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        # Add indicators if missing
        if 'momentum_1h' not in df.columns:
            print("   Calculating technical indicators...")
            df = TechnicalIndicators.add_all_indicators(df, timeframe='4h')

        print(f"   ✓ Loaded {len(df)} candles")
        print(f"   ✓ Date range: {df.iloc[0]['timestamp'].date()} to {df.iloc[-1]['timestamp'].date()}")
        print(f"   ✓ Current price: ${df.iloc[-1]['close']:,.2f}")

    except FileNotFoundError:
        print(f"\n❌ ERROR: Data file not found: {data_file}")
        print("   Run this first: python data_collector.py --days 1825")
        sys.exit(1)

    # 2. Initialize clients
    print(f"\n🔧 Initializing systems...")
    coinglass = CoinGlassClient()
    engine = RecommendationEngine(df=df, coinglass_client=coinglass)
    print("   ✓ CoinGlass client ready")
    print("   ✓ Recommendation engine ready")

    # 3. Check parabolic status if requested
    if args.parabolic_only:
        print("\n" + "="*70)
        print("📈 PARABOLIC BULL RUN ANALYSIS")
        print("="*70)

        bull_run = engine.detect_parabolic_bull_run()

        if bull_run['is_parabolic']:
            print("\n✅ PARABOLIC BULL RUN DETECTED!")
        else:
            print("\n❌ NOT IN PARABOLIC BULL RUN")

        print(f"\nConfidence: {bull_run['confidence']:.0f}%")
        print(f"Distance from 200 SMA: {bull_run['distance_from_200_sma']:+.1f}%")
        print(f"SMA Slope (weekly): {bull_run['sma_slope_weekly']:+.2f}%")
        print(f"\nCriteria Met: {bull_run['criteria_met']}/5")

        print("\nDetailed Criteria:")
        details = bull_run['details']
        print(f"  {'✓' if details['price_above_200sma'] else '✗'} Price >20% above 200 SMA")
        print(f"  {'✓' if details['sma_rising_fast'] else '✗'} SMA rising >3% per week")
        print(f"  {'✓' if details['smas_aligned'] else '✗'} All SMAs aligned")
        print(f"  {'✓' if details['strong_momentum'] else '✗'} Strong momentum")
        print(f"  {'✓' if details['high_volume'] else '✗'} High volume")

        print("\n" + "="*70)
        return

    # 4. Get full recommendation
    recommendation = engine.get_recommendation(fetch_coinglass=args.fetch_coinglass)

    # 5. Save if requested
    if args.save:
        engine.save_recommendation()

    # 6. Display summary
    print("\n" + "="*70)
    print("📋 QUICK SUMMARY")
    print("="*70)

    if recommendation['action'] == 'ENTER LONG':
        print("\n🟢 RECOMMENDATION: GO LONG")
        print(f"   Entry: ${recommendation['entry_zone'][0]:,.0f} - ${recommendation['entry_zone'][1]:,.0f}")
        print(f"   Stop Loss: ${recommendation['stop_loss']:,.0f}")
        print(f"   Take Profit: ${recommendation['take_profit']:,.0f}")
        print(f"   Leverage: {recommendation['leverage']}x")
    elif recommendation['action'] == 'CONSIDER SHORT':
        print("\n🔴 RECOMMENDATION: CONSIDER SHORT")
        print(f"   Entry: ${recommendation['entry_zone'][0]:,.0f} - ${recommendation['entry_zone'][1]:,.0f}")
        print(f"   Stop Loss: ${recommendation['stop_loss']:,.0f}")
        print(f"   Take Profit: ${recommendation['take_profit']:,.0f}")
        print(f"   Leverage: {recommendation['leverage']}x")
    else:
        print("\n⚪ RECOMMENDATION: WAIT")
        print("   No clear setup - stay out of the market")

    print(f"\n   Confidence: {recommendation['confidence']:.0f}%")
    print(f"   Risk Level: {recommendation['risk_level']}")

    print("\n" + "="*70)

    # 7. Pro tip
    if recommendation['action'] != 'WAIT':
        print("\n💡 PRO TIP:")
        print("   Start with 5x leverage (conservative)")
        print("   Use ONLY 50% of capital for this trade")
        print("   Set stop loss IMMEDIATELY after entry")
        print("   Take profits at target, don't be greedy")

    print("\n⚠️  DISCLAIMER:")
    print("   This is NOT financial advice. High leverage trading is extremely risky.")
    print("   Only trade with money you can afford to lose.")
    print("   Past performance does not guarantee future results.")

    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
