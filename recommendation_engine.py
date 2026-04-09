"""
Smart Trading Recommendation Engine
Based on Parabolic Bull Run Strategy + CoinGlass Data
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from coinglass_client import CoinGlassClient
from indicators import TechnicalIndicators

class RecommendationEngine:
    """
    Intelligent trading recommendation system

    Combines:
    - Parabolic bull run detection
    - CoinGlass liquidation heatmaps
    - Volume profiles
    - Market sentiment
    """

    def __init__(self, df=None, coinglass_client=None):
        """
        Initialize recommendation engine

        Args:
            df: DataFrame with OHLCV data and indicators
            coinglass_client: CoinGlassClient instance (optional)
        """
        self.df = df
        self.coinglass = coinglass_client or CoinGlassClient()
        self.last_recommendation = None

    def detect_parabolic_bull_run(self, df=None):
        """
        Detect if market is in parabolic bull run conditions

        Parabolic Bull Run Criteria:
        1. Price >20% above 200 SMA
        2. 200 SMA rising at >3% per week
        3. All major SMAs aligned (60 < 90 < 180 < 200)
        4. Strong upward momentum
        5. High volume

        Returns:
            dict: Bull run analysis with confidence score
        """
        if df is None:
            df = self.df

        if df is None or len(df) < 200:
            return {'is_parabolic': False, 'confidence': 0, 'reason': 'Insufficient data'}

        latest = df.iloc[-1]
        current_price = latest['close']

        # Calculate SMAs if not present
        sma_200 = df['close'].rolling(window=200).mean().iloc[-1]
        sma_180 = df['close'].rolling(window=180).mean().iloc[-1]
        sma_90 = df['close'].rolling(window=90).mean().iloc[-1]
        sma_60 = df['close'].rolling(window=60).mean().iloc[-1]

        # Criterion 1: Price >20% above 200 SMA
        distance_from_200 = ((current_price - sma_200) / sma_200) * 100
        criterion_1 = distance_from_200 > 20

        # Criterion 2: 200 SMA slope (weekly change)
        # Assume 4h candles: 42 candles = 1 week
        if len(df) >= 242:  # 200 + 42
            sma_200_week_ago = df['close'].rolling(window=200).mean().iloc[-42]
            sma_slope_weekly = ((sma_200 - sma_200_week_ago) / sma_200_week_ago) * 100
        else:
            sma_slope_weekly = 0

        criterion_2 = sma_slope_weekly > 3.0

        # Criterion 3: SMA alignment
        criterion_3 = (sma_60 > sma_90 > sma_180 > sma_200)

        # Criterion 4: Strong momentum
        momentum = latest.get('momentum_1h', 0)
        criterion_4 = momentum > 0.5

        # Criterion 5: High volume
        volume_spike = latest.get('volume_spike', 1.0)
        criterion_5 = volume_spike > 1.3

        # Calculate confidence score
        criteria_met = sum([
            criterion_1,
            criterion_2,
            criterion_3,
            criterion_4,
            criterion_5
        ])

        confidence = (criteria_met / 5) * 100

        # Determine if parabolic
        is_parabolic = criteria_met >= 3  # At least 3/5 criteria

        return {
            'is_parabolic': is_parabolic,
            'confidence': confidence,
            'distance_from_200_sma': distance_from_200,
            'sma_slope_weekly': sma_slope_weekly,
            'sma_aligned': criterion_3,
            'momentum': momentum,
            'volume_spike': volume_spike,
            'criteria_met': criteria_met,
            'details': {
                'price_above_200sma': criterion_1,
                'sma_rising_fast': criterion_2,
                'smas_aligned': criterion_3,
                'strong_momentum': criterion_4,
                'high_volume': criterion_5
            }
        }

    def analyze_liquidation_zones(self, liquidation_data):
        """
        Analyze liquidation zones for trading opportunities

        Returns:
            dict: Liquidation analysis with support/resistance
        """
        current_price = liquidation_data['current_price']
        high_risk_long = liquidation_data['high_risk_long_level']
        high_risk_short = liquidation_data['high_risk_short_level']

        # Calculate distances
        distance_to_long_liq = ((high_risk_long - current_price) / current_price) * 100
        distance_to_short_liq = ((high_risk_short - current_price) / current_price) * 100

        # Determine support/resistance strength
        total_long_liq = liquidation_data['total_long_liquidations']
        total_short_liq = liquidation_data['total_short_liquidations']

        # More short liquidations above = strong resistance
        # More long liquidations below = strong support

        resistance_strength = 'STRONG' if total_short_liq > total_long_liq * 1.5 else 'MODERATE'
        support_strength = 'STRONG' if total_long_liq > total_short_liq * 1.5 else 'MODERATE'

        return {
            'support_level': high_risk_long,
            'resistance_level': high_risk_short,
            'distance_to_support': abs(distance_to_long_liq),
            'distance_to_resistance': abs(distance_to_short_liq),
            'support_strength': support_strength,
            'resistance_strength': resistance_strength,
            'bias': 'LONG' if total_short_liq > total_long_liq else 'SHORT'
        }

    def get_recommendation(self, df=None, fetch_coinglass=True):
        """
        Generate comprehensive trading recommendation

        Returns:
            dict: Complete recommendation with reasoning
        """
        if df is not None:
            self.df = df

        print("\n" + "="*70)
        print("GENERATING TRADING RECOMMENDATION")
        print("="*70)

        # 1. Detect parabolic bull run
        print("\n1️⃣  Analyzing Parabolic Bull Run Conditions...")
        bull_run = self.detect_parabolic_bull_run()

        print(f"   Parabolic Bull Run: {'✓ YES' if bull_run['is_parabolic'] else '✗ NO'}")
        print(f"   Confidence: {bull_run['confidence']:.0f}%")
        print(f"   Distance from 200 SMA: {bull_run['distance_from_200_sma']:+.1f}%")
        print(f"   SMA Slope (weekly): {bull_run['sma_slope_weekly']:+.2f}%")

        # 2. Get CoinGlass data
        if fetch_coinglass:
            print("\n2️⃣  Fetching CoinGlass Market Data...")
            coinglass_data = self.coinglass.get_market_summary()
        else:
            print("\n2️⃣  Using cached/mock CoinGlass data...")
            coinglass_data = {
                'liquidations': self.coinglass._get_mock_liquidation_data(),
                'long_short_ratio': self.coinglass._get_mock_long_short_ratio(),
                'volume_profile': self.coinglass.get_volume_profile()
            }

        # 3. Analyze liquidation zones
        print("\n3️⃣  Analyzing Liquidation Zones...")
        liq_analysis = self.analyze_liquidation_zones(coinglass_data['liquidations'])
        print(f"   Support: ${liq_analysis['support_level']:,.0f} ({liq_analysis['support_strength']})")
        print(f"   Resistance: ${liq_analysis['resistance_level']:,.0f} ({liq_analysis['resistance_strength']})")

        # 4. Check market sentiment
        print("\n4️⃣  Evaluating Market Sentiment...")
        ls_ratio = coinglass_data.get('long_short_ratio', {})
        print(f"   Long/Short Ratio: {ls_ratio.get('ratio', 1.0):.2f}")
        print(f"   Sentiment: {ls_ratio.get('sentiment', 'NEUTRAL')}")

        # 5. Generate recommendation
        print("\n5️⃣  Generating Recommendation...")
        recommendation = self._generate_recommendation_logic(
            bull_run,
            liq_analysis,
            ls_ratio,
            coinglass_data
        )

        # Print recommendation
        self._print_recommendation(recommendation)

        self.last_recommendation = recommendation
        return recommendation

    def _generate_recommendation_logic(self, bull_run, liq_analysis, ls_ratio, coinglass_data):
        """Core recommendation logic"""

        current_price = coinglass_data['liquidations']['current_price']

        # Initialize recommendation
        recommendation = {
            'action': 'WAIT',
            'direction': None,
            'confidence': 0,
            'entry_zone': None,
            'stop_loss': None,
            'take_profit': None,
            'leverage': 5,
            'reasoning': [],
            'risk_level': 'HIGH',
            'timestamp': datetime.now().isoformat()
        }

        # PARABOLIC BULL RUN STRATEGY
        if bull_run['is_parabolic'] and bull_run['confidence'] >= 60:
            # Strong parabolic bull run = LONG bias
            recommendation['action'] = 'ENTER LONG'
            recommendation['direction'] = 'LONG'
            recommendation['confidence'] = bull_run['confidence']
            recommendation['leverage'] = 5  # Conservative 5x
            recommendation['risk_level'] = 'MEDIUM'

            # Entry: Wait for pullback to SMA60 or buy breakout
            recommendation['entry_zone'] = (current_price * 0.97, current_price * 1.02)
            recommendation['stop_loss'] = current_price * 0.97  # 3% stop
            recommendation['take_profit'] = current_price * 1.05  # 5% target

            recommendation['reasoning'].append(
                f"✓ PARABOLIC BULL RUN detected ({bull_run['confidence']:.0f}% confidence)"
            )
            recommendation['reasoning'].append(
                f"  - Price {bull_run['distance_from_200_sma']:+.1f}% above 200 SMA"
            )
            recommendation['reasoning'].append(
                f"  - SMA slope: {bull_run['sma_slope_weekly']:+.2f}% per week"
            )

            # Check liquidation zones
            if liq_analysis['bias'] == 'LONG':
                recommendation['confidence'] += 10
                recommendation['reasoning'].append(
                    f"✓ Liquidation bias supports LONG (more shorts to squeeze)"
                )

            # Check long/short ratio
            if ls_ratio.get('ratio', 1.0) < 0.9:  # More shorts than longs
                recommendation['confidence'] += 10
                recommendation['reasoning'].append(
                    f"✓ L/S ratio {ls_ratio['ratio']:.2f} - many shorts to squeeze"
                )

        # BEAR MARKET / CONSOLIDATION
        elif not bull_run['is_parabolic']:
            # Check if we're in bear market
            if bull_run['distance_from_200_sma'] < -10:
                # Deep below 200 SMA = bear market
                recommendation['action'] = 'CONSIDER SHORT'
                recommendation['direction'] = 'SHORT'
                recommendation['confidence'] = 40
                recommendation['leverage'] = 3  # Lower leverage for shorts
                recommendation['risk_level'] = 'HIGH'

                recommendation['entry_zone'] = (current_price * 0.98, current_price * 1.03)
                recommendation['stop_loss'] = current_price * 1.025  # 2.5% stop
                recommendation['take_profit'] = current_price * 0.96  # 4% target

                recommendation['reasoning'].append(
                    f"⚠ Bear market conditions (price {bull_run['distance_from_200_sma']:.1f}% below 200 SMA)"
                )
                recommendation['reasoning'].append(
                    f"  - Consider shorting rallies into resistance"
                )

                # Check if too many people already short
                if ls_ratio.get('ratio', 1.0) < 0.7:  # Too many shorts
                    recommendation['action'] = 'WAIT'
                    recommendation['confidence'] = 20
                    recommendation['reasoning'].append(
                        f"⚠ Too many shorts already ({ls_ratio['ratio']:.2f}) - risk of squeeze"
                    )

            else:
                # Consolidation / neutral
                recommendation['action'] = 'WAIT'
                recommendation['direction'] = None
                recommendation['confidence'] = 0
                recommendation['reasoning'].append(
                    "⚠ No clear parabolic trend - WAIT for better setup"
                )
                recommendation['reasoning'].append(
                    f"  - Price only {bull_run['distance_from_200_sma']:+.1f}% from 200 SMA"
                )
                recommendation['reasoning'].append(
                    f"  - SMA slope: {bull_run['sma_slope_weekly']:+.2f}% per week (need >3%)"
                )

        # Add liquidation zone warnings
        if liq_analysis['distance_to_support'] < 5:
            recommendation['reasoning'].append(
                f"⚠ Close to support liquidation zone (${liq_analysis['support_level']:,.0f})"
            )

        if liq_analysis['distance_to_resistance'] < 5:
            recommendation['reasoning'].append(
                f"⚠ Close to resistance liquidation zone (${liq_analysis['resistance_level']:,.0f})"
            )

        # Cap confidence at 100
        recommendation['confidence'] = min(recommendation['confidence'], 100)

        return recommendation

    def _print_recommendation(self, rec):
        """Pretty print recommendation"""
        print("\n" + "="*70)
        print("📊 TRADING RECOMMENDATION")
        print("="*70)

        # Action
        if rec['action'] == 'ENTER LONG':
            print(f"\n🟢 ACTION: {rec['action']}")
        elif rec['action'] == 'CONSIDER SHORT':
            print(f"\n🔴 ACTION: {rec['action']}")
        else:
            print(f"\n⚪ ACTION: {rec['action']}")

        # Confidence
        conf_bar = "█" * int(rec['confidence'] / 10)
        print(f"   Confidence: {rec['confidence']:.0f}% {conf_bar}")

        if rec['direction']:
            print(f"\n   Direction: {rec['direction']}")
            print(f"   Leverage: {rec['leverage']}x (Conservative)")
            print(f"   Risk Level: {rec['risk_level']}")

            if rec['entry_zone']:
                print(f"\n   Entry Zone: ${rec['entry_zone'][0]:,.0f} - ${rec['entry_zone'][1]:,.0f}")
            if rec['stop_loss']:
                print(f"   Stop Loss: ${rec['stop_loss']:,.0f}")
            if rec['take_profit']:
                print(f"   Take Profit: ${rec['take_profit']:,.0f}")

        # Reasoning
        print(f"\n   Reasoning:")
        for reason in rec['reasoning']:
            print(f"   {reason}")

        print("\n" + "="*70)
        print(f"⏰ Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70 + "\n")

    def save_recommendation(self, filename=None):
        """Save recommendation to JSON file"""
        if self.last_recommendation is None:
            print("No recommendation to save!")
            return

        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"results/recommendation_{timestamp}.json"

        import json
        with open(filename, 'w') as f:
            json.dump(self.last_recommendation, f, indent=2)

        print(f"✓ Recommendation saved to {filename}")


def test_recommendation_engine():
    """Test the recommendation engine"""
    import config
    import glob
    import os

    print("\n" + "="*70)
    print("TESTING RECOMMENDATION ENGINE")
    print("="*70)

    # Load historical data - auto-detect available files
    data_files = glob.glob(f'{config.DATA_DIR}/eth_usd_*_{config.LOOKBACK_DAYS}d.csv')
    if not data_files:
        data_files = glob.glob(f'{config.DATA_DIR}/eth_usd_*.csv')

    if not data_files:
        print(f"\n❌ No data files found in {config.DATA_DIR}/")
        print("   Run: python data_collector.py --days 1825")
        return None

    data_file = sorted(data_files)[-1]
    print(f"\nLoading data from {os.path.basename(data_file)}...")

    try:
        df = pd.read_csv(data_file)
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        # Add indicators if not present
        if 'momentum_1h' not in df.columns:
            print("Adding technical indicators...")
            from indicators import TechnicalIndicators
            df = TechnicalIndicators.add_all_indicators(df, timeframe='4h')

        print(f"✓ Loaded {len(df)} candles")
        print(f"  Date range: {df.iloc[0]['timestamp']} to {df.iloc[-1]['timestamp']}")

        # Initialize engine
        engine = RecommendationEngine(df=df)

        # Get recommendation
        recommendation = engine.get_recommendation(fetch_coinglass=False)

        # Save it
        engine.save_recommendation()

        return recommendation

    except FileNotFoundError:
        print(f"❌ Data file not found: {data_file}")
        print("   Run: python data_collector.py first")
        return None


if __name__ == "__main__":
    test_recommendation_engine()
