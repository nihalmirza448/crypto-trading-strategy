#!/usr/bin/env python3
"""
Comprehensive Market Analyzer with Discord Notifications
Analyzes ETH market conditions and sends alerts when conditions change
"""
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import requests
import config
from coinglass_client import CoinGlassClient
from recommendation_engine import RecommendationEngine
from indicators import TechnicalIndicators
import glob

load_dotenv()


class MarketAnalyzer:
    """
    Comprehensive market analysis with Discord notifications
    """

    def __init__(self, discord_webhook_url=None):
        """
        Initialize analyzer

        Args:
            discord_webhook_url: Discord webhook URL for notifications
        """
        self.discord_webhook = discord_webhook_url or os.getenv('DISCORD_WEBHOOK_URL')
        self.coinglass = CoinGlassClient()
        self.last_state_file = 'results/last_market_state.json'
        self.load_historical_data()

    def load_historical_data(self):
        """Load historical ETH data"""
        print("\n📊 Loading historical data...")

        # Find available data files
        data_files = glob.glob(f'{config.DATA_DIR}/eth_usd_*_{config.LOOKBACK_DAYS}d.csv')
        if not data_files:
            data_files = glob.glob(f'{config.DATA_DIR}/eth_usd_*.csv')

        if not data_files:
            raise FileNotFoundError(f"No data files found in {config.DATA_DIR}/")

        data_file = sorted(data_files)[-1]
        print(f"   Using: {os.path.basename(data_file)}")

        self.df = pd.read_csv(data_file)
        self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])

        # Add indicators if missing
        if 'momentum_1h' not in self.df.columns:
            print("   Calculating indicators...")
            self.df = TechnicalIndicators.add_all_indicators(self.df, timeframe='4h')

        print(f"   ✓ Loaded {len(self.df)} candles")
        print(f"   ✓ Date range: {self.df.iloc[0]['timestamp'].date()} to {self.df.iloc[-1]['timestamp'].date()}")

    def get_current_price(self):
        """Get current ETH price from latest data"""
        return self.df.iloc[-1]['close']

    def analyze_market(self):
        """
        Comprehensive market analysis

        Returns:
            dict: Complete market analysis
        """
        print("\n" + "="*70)
        print("📈 ETHEREUM MARKET ANALYSIS")
        print("="*70)

        # Initialize recommendation engine
        engine = RecommendationEngine(df=self.df, coinglass_client=self.coinglass)

        # Get current price and basic info
        latest = self.df.iloc[-1]
        current_price = latest['close']
        timestamp = latest['timestamp']

        print(f"\n⏰ Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📊 Data Current As Of: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"💰 Current ETH Price: ${current_price:,.2f}")

        # 1. Parabolic Bull Run Analysis
        print("\n" + "="*70)
        print("1️⃣  PARABOLIC BULL RUN ANALYSIS")
        print("="*70)

        bull_run = engine.detect_parabolic_bull_run()

        if bull_run['is_parabolic']:
            print("\n🚀 STATUS: PARABOLIC BULL RUN DETECTED!")
            status_emoji = "🟢"
        else:
            print("\n⚪ STATUS: NOT IN PARABOLIC BULL RUN")
            status_emoji = "⚪"

        print(f"\nConfidence: {bull_run['confidence']:.0f}%")
        print(f"Criteria Met: {bull_run['criteria_met']}/5")
        print(f"\nKey Metrics:")
        print(f"  • Distance from 200 SMA: {bull_run['distance_from_200_sma']:+.1f}%")
        print(f"  • SMA Slope (weekly): {bull_run['sma_slope_weekly']:+.2f}%")
        print(f"  • SMAs Aligned: {'✓' if bull_run['sma_aligned'] else '✗'}")
        print(f"  • Momentum: {bull_run['momentum']:+.2f}%")
        print(f"  • Volume Spike: {bull_run['volume_spike']:.2f}x")

        print("\nCriteria Checklist:")
        details = bull_run['details']
        print(f"  {'✓' if details['price_above_200sma'] else '✗'} Price >20% above 200 SMA")
        print(f"  {'✓' if details['sma_rising_fast'] else '✗'} SMA rising >3% per week")
        print(f"  {'✓' if details['smas_aligned'] else '✗'} All SMAs aligned")
        print(f"  {'✓' if details['strong_momentum'] else '✗'} Strong momentum")
        print(f"  {'✓' if details['high_volume'] else '✗'} High volume")

        # 2. CoinGlass Data
        print("\n" + "="*70)
        print("2️⃣  COINGLASS MARKET DATA")
        print("="*70)

        coinglass_data = self.coinglass.get_market_summary()
        liq = coinglass_data['liquidations']
        ls_ratio = coinglass_data['long_short_ratio']
        oi = coinglass_data['open_interest']

        print(f"\n💥 LIQUIDATION ZONES:")
        print(f"  • Support (Long Liq): ${liq['high_risk_long_level']:,.0f} ({((liq['high_risk_long_level']-current_price)/current_price*100):+.1f}%)")
        print(f"  • Resistance (Short Liq): ${liq['high_risk_short_level']:,.0f} ({((liq['high_risk_short_level']-current_price)/current_price*100):+.1f}%)")
        print(f"  • Total Long Liquidations: ${liq['total_long_liquidations']/1e6:.0f}M")
        print(f"  • Total Short Liquidations: ${liq['total_short_liquidations']/1e6:.0f}M")

        # Determine liquidation bias
        if liq['total_short_liquidations'] > liq['total_long_liquidations'] * 1.2:
            liq_bias = "BULLISH (More shorts to squeeze)"
        elif liq['total_long_liquidations'] > liq['total_short_liquidations'] * 1.2:
            liq_bias = "BEARISH (More longs to liquidate)"
        else:
            liq_bias = "NEUTRAL (Balanced)"

        print(f"  • Liquidation Bias: {liq_bias}")

        print(f"\n📊 SENTIMENT INDICATORS:")
        print(f"  • Long/Short Ratio: {ls_ratio['ratio']:.2f}")
        print(f"  • Longs: {ls_ratio['long_percentage']:.1f}%")
        print(f"  • Shorts: {ls_ratio['short_percentage']:.1f}%")
        print(f"  • Sentiment: {ls_ratio['sentiment']}")
        print(f"  • Open Interest: ${oi['total_oi']/1e9:.2f}B ({oi['trend']})")

        # 3. Technical Levels
        print("\n" + "="*70)
        print("3️⃣  TECHNICAL LEVELS")
        print("="*70)

        sma_60 = latest.get('sma_60', None)
        sma_90 = latest.get('sma_90', None)
        sma_100 = self.df['close'].rolling(window=100).mean().iloc[-1]
        sma_180 = latest.get('sma_180', None)
        sma_200 = self.df['close'].rolling(window=200).mean().iloc[-1]

        print(f"\n📈 MOVING AVERAGES:")
        print(f"  • SMA 60:  ${sma_60:,.2f} ({((current_price-sma_60)/sma_60*100):+.1f}%)")
        print(f"  • SMA 90:  ${sma_90:,.2f} ({((current_price-sma_90)/sma_90*100):+.1f}%)")
        print(f"  • SMA 100: ${sma_100:,.2f} ({((current_price-sma_100)/sma_100*100):+.1f}%)")
        print(f"  • SMA 180: ${sma_180:,.2f} ({((current_price-sma_180)/sma_180*100):+.1f}%)")
        print(f"  • SMA 200: ${sma_200:,.2f} ({((current_price-sma_200)/sma_200*100):+.1f}%)")

        rsi = latest.get('rsi', None)
        bb_upper = latest.get('bb_upper', None)
        bb_lower = latest.get('bb_lower', None)

        print(f"\n📊 OSCILLATORS:")
        print(f"  • RSI(14): {rsi:.1f} ({'Overbought' if rsi > 70 else 'Oversold' if rsi < 30 else 'Neutral'})")
        print(f"  • Bollinger Upper: ${bb_upper:,.2f}")
        print(f"  • Bollinger Lower: ${bb_lower:,.2f}")

        # 4. Trading Recommendation
        print("\n" + "="*70)
        print("4️⃣  TRADING RECOMMENDATION")
        print("="*70)

        recommendation = engine.get_recommendation(fetch_coinglass=False)

        if recommendation['action'] == 'ENTER LONG':
            action_emoji = "🟢"
        elif recommendation['action'] == 'CONSIDER SHORT':
            action_emoji = "🔴"
        else:
            action_emoji = "⚪"

        print(f"\n{action_emoji} ACTION: {recommendation['action']}")
        print(f"Confidence: {recommendation['confidence']:.0f}%")
        print(f"Risk Level: {recommendation['risk_level']}")

        if recommendation['direction']:
            print(f"\nDirection: {recommendation['direction']}")
            print(f"Leverage: {recommendation['leverage']}x")
            if recommendation['entry_zone']:
                print(f"Entry Zone: ${recommendation['entry_zone'][0]:,.0f} - ${recommendation['entry_zone'][1]:,.0f}")
            if recommendation['stop_loss']:
                print(f"Stop Loss: ${recommendation['stop_loss']:,.0f}")
            if recommendation['take_profit']:
                print(f"Take Profit: ${recommendation['take_profit']:,.0f}")

        print(f"\nReasoning:")
        for reason in recommendation['reasoning']:
            print(f"  {reason}")

        # Compile full analysis
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'data_timestamp': timestamp.isoformat(),
            'current_price': current_price,
            'parabolic': bull_run,
            'liquidations': liq,
            'sentiment': {
                'long_short_ratio': ls_ratio,
                'open_interest': oi,
                'liquidation_bias': liq_bias
            },
            'technical_levels': {
                'sma_60': sma_60,
                'sma_90': sma_90,
                'sma_100': sma_100,
                'sma_180': sma_180,
                'sma_200': sma_200,
                'rsi': rsi,
                'bb_upper': bb_upper,
                'bb_lower': bb_lower
            },
            'recommendation': recommendation
        }

        print("\n" + "="*70)
        print("✅ ANALYSIS COMPLETE")
        print("="*70 + "\n")

        return analysis

    def check_significant_change(self, current_analysis):
        """
        Check if market conditions have changed significantly

        Returns:
            tuple: (has_changed, change_description)
        """
        if not os.path.exists(self.last_state_file):
            return True, "First analysis - no previous state to compare"

        try:
            with open(self.last_state_file, 'r') as f:
                last_state = json.load(f)
        except:
            return True, "Could not load previous state"

        changes = []

        # Check parabolic status change
        if current_analysis['parabolic']['is_parabolic'] != last_state['parabolic']['is_parabolic']:
            if current_analysis['parabolic']['is_parabolic']:
                changes.append("🚀 PARABOLIC BULL RUN DETECTED!")
            else:
                changes.append("⚠️ Exited parabolic bull run")

        # Check recommendation change
        if current_analysis['recommendation']['action'] != last_state['recommendation']['action']:
            changes.append(f"📊 Recommendation changed: {last_state['recommendation']['action']} → {current_analysis['recommendation']['action']}")

        # Check significant confidence change (>20%)
        conf_diff = abs(current_analysis['recommendation']['confidence'] - last_state['recommendation']['confidence'])
        if conf_diff > 20:
            changes.append(f"📈 Confidence changed: {last_state['recommendation']['confidence']:.0f}% → {current_analysis['recommendation']['confidence']:.0f}%")

        # Check significant price change (>5%)
        price_diff = abs((current_analysis['current_price'] - last_state['current_price']) / last_state['current_price'] * 100)
        if price_diff > 5:
            changes.append(f"💰 Significant price move: ${last_state['current_price']:,.2f} → ${current_analysis['current_price']:,.2f} ({price_diff:+.1f}%)")

        if changes:
            return True, "\n".join(changes)
        else:
            return False, "No significant changes detected"

    def save_current_state(self, analysis):
        """Save current market state for comparison"""
        os.makedirs('results', exist_ok=True)
        with open(self.last_state_file, 'w') as f:
            json.dump(analysis, f, indent=2, default=str)

    def send_discord_alert(self, analysis, change_description):
        """
        Send market analysis to Discord

        Args:
            analysis: Market analysis dict
            change_description: Description of changes
        """
        if not self.discord_webhook:
            print("\n⚠️  No Discord webhook URL configured")
            print("   Add DISCORD_WEBHOOK_URL to .env file to enable alerts")
            return

        # Build Discord embed
        parabolic = analysis['parabolic']
        rec = analysis['recommendation']

        # Determine color based on recommendation
        if rec['action'] == 'ENTER LONG':
            color = 0x00ff00  # Green
            title_emoji = "🟢"
        elif rec['action'] == 'CONSIDER SHORT':
            color = 0xff0000  # Red
            title_emoji = "🔴"
        else:
            color = 0xcccccc  # Gray
            title_emoji = "⚪"

        # Build embed
        embed = {
            "title": f"{title_emoji} ETH Market Alert - {rec['action']}",
            "description": f"**{change_description}**",
            "color": color,
            "fields": [
                {
                    "name": "💰 Current Price",
                    "value": f"${analysis['current_price']:,.2f}",
                    "inline": True
                },
                {
                    "name": "📊 Confidence",
                    "value": f"{rec['confidence']:.0f}%",
                    "inline": True
                },
                {
                    "name": "⚠️ Risk Level",
                    "value": rec['risk_level'],
                    "inline": True
                },
                {
                    "name": "🚀 Parabolic Status",
                    "value": "✅ YES" if parabolic['is_parabolic'] else "❌ NO",
                    "inline": True
                },
                {
                    "name": "📈 Criteria Met",
                    "value": f"{parabolic['criteria_met']}/5",
                    "inline": True
                },
                {
                    "name": "📊 Distance from 200 SMA",
                    "value": f"{parabolic['distance_from_200_sma']:+.1f}%",
                    "inline": True
                },
            ],
            "footer": {
                "text": f"Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            }
        }

        # Add entry/exit levels if available
        if rec['entry_zone']:
            embed['fields'].append({
                "name": "🎯 Entry Zone",
                "value": f"${rec['entry_zone'][0]:,.0f} - ${rec['entry_zone'][1]:,.0f}",
                "inline": True
            })

        if rec['stop_loss']:
            embed['fields'].append({
                "name": "🛑 Stop Loss",
                "value": f"${rec['stop_loss']:,.0f}",
                "inline": True
            })

        if rec['take_profit']:
            embed['fields'].append({
                "name": "🎯 Take Profit",
                "value": f"${rec['take_profit']:,.0f}",
                "inline": True
            })

        # Add reasoning
        reasoning_text = "\n".join(f"• {r}" for r in rec['reasoning'][:3])  # First 3 reasons
        embed['fields'].append({
            "name": "🧠 Key Reasoning",
            "value": reasoning_text,
            "inline": False
        })

        # Send to Discord
        payload = {
            "embeds": [embed],
            "username": "ETH Market Analyzer"
        }

        try:
            response = requests.post(self.discord_webhook, json=payload)
            response.raise_for_status()
            print("\n✅ Discord alert sent successfully!")
        except Exception as e:
            print(f"\n❌ Failed to send Discord alert: {e}")

    def run_analysis(self, send_alert_always=False):
        """
        Run complete market analysis and send Discord alert if needed

        Args:
            send_alert_always: If True, always send Discord alert regardless of changes
        """
        # Get current analysis
        analysis = self.analyze_market()

        # Check for significant changes
        has_changed, change_desc = self.check_significant_change(analysis)

        # Save current state
        self.save_current_state(analysis)

        # Send Discord alert if conditions changed or forced
        if has_changed or send_alert_always:
            print(f"\n📢 CHANGE DETECTED:")
            print(f"   {change_desc}")
            self.send_discord_alert(analysis, change_desc)
        else:
            print(f"\n✅ No significant changes since last analysis")
            print(f"   Skipping Discord notification")

        # Save detailed report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f'results/market_analysis_{timestamp}.json'
        with open(report_file, 'w') as f:
            json.dump(analysis, f, indent=2, default=str)
        print(f"\n📄 Detailed report saved: {report_file}")

        return analysis


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Analyze ETH market conditions')
    parser.add_argument('--force-alert', action='store_true',
                       help='Send Discord alert even if no changes detected')
    parser.add_argument('--webhook', type=str,
                       help='Discord webhook URL (overrides .env)')

    args = parser.parse_args()

    print("\n" + "="*70)
    print("🔍 ETHEREUM MARKET ANALYZER")
    print("="*70)

    # Initialize analyzer
    analyzer = MarketAnalyzer(discord_webhook_url=args.webhook)

    # Run analysis
    analyzer.run_analysis(send_alert_always=args.force_alert)

    print("\n" + "="*70)
    print("✅ ANALYSIS COMPLETE")
    print("="*70)
    print("\nTo run automatically:")
    print("  • Every 4 hours: Add to crontab")
    print("  • On demand: python market_analyzer.py")
    print("  • Force alert: python market_analyzer.py --force-alert")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
