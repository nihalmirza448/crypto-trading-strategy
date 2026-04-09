"""
Real-Time Market Monitor with Live Analysis
Combines WebSocket streaming with market analysis and recommendations
"""
import time
from datetime import datetime, timedelta
import pandas as pd
import json
from realtime_client import KrakenWebSocketClient
from recommendation_engine import RecommendationEngine
import config

class RealTimeMarketMonitor:
    """
    Real-time market monitoring with live analysis

    Features:
    - Live price streaming
    - Real-time candle updates
    - Continuous market analysis
    - Alert system for significant changes
    - Discord notifications (optional)
    """

    def __init__(self, pair='ETH/USD', analysis_interval=60):
        self.pair = pair
        self.analysis_interval = analysis_interval  # seconds between analysis updates

        # Initialize WebSocket client
        self.ws_client = KrakenWebSocketClient(pair=pair)

        # Initialize recommendation engine
        self.engine = RecommendationEngine()

        # State tracking
        self.last_analysis = None
        self.last_analysis_time = None
        self.last_recommendation = None
        self.alert_history = []

        # Callbacks
        self.on_alert_callback = None

    def _should_run_analysis(self):
        """Check if enough time has passed for new analysis"""
        if self.last_analysis_time is None:
            return True

        elapsed = (datetime.now() - self.last_analysis_time).total_seconds()
        return elapsed >= self.analysis_interval

    def _analyze_market(self):
        """Run market analysis with current data"""
        try:
            # Get current market data
            current_price = self.ws_client.get_current_price()
            ticker = self.ws_client.get_ticker()
            current_candle = self.ws_client.get_current_ohlc()

            if not current_price:
                return None

            # Load historical data for analysis
            # (In production, you'd maintain this in memory or update periodically)
            import glob
            data_files = glob.glob(f'{config.DATA_DIR}/eth_usd_240m_*.csv')
            if data_files:
                latest_file = sorted(data_files)[-1]
                df = pd.read_csv(latest_file)
                df['timestamp'] = pd.to_datetime(df['timestamp'])

                # Append current forming candle if available
                if current_candle:
                    current_row = pd.DataFrame([{
                        'timestamp': current_candle['timestamp'],
                        'open': current_candle['open'],
                        'high': current_candle['high'],
                        'low': current_candle['low'],
                        'close': current_candle['close'],
                        'volume': current_candle['volume'],
                        'vwap': current_candle['vwap'],
                        'count': current_candle['count']
                    }])
                    df = pd.concat([df, current_row], ignore_index=True)

                # Get parabolic analysis
                parabolic = self.engine.detect_parabolic_bull_run(df)

                # Get recommendation
                recommendation = self.engine.get_recommendation(df)

                analysis = {
                    'timestamp': datetime.now(),
                    'current_price': current_price,
                    'ticker': ticker,
                    'current_candle': current_candle,
                    'parabolic': parabolic,
                    'recommendation': recommendation,
                    'market_connected': self.ws_client.connected
                }

                self.last_analysis = analysis
                self.last_analysis_time = datetime.now()

                # Check for alerts
                self._check_alerts(analysis)

                return analysis

        except Exception as e:
            print(f"Error analyzing market: {e}")
            return None

    def _check_alerts(self, current_analysis):
        """Check for significant changes and trigger alerts"""
        if not self.last_recommendation:
            self.last_recommendation = current_analysis['recommendation']
            return

        alerts = []

        # Check for recommendation change
        if current_analysis['recommendation']['action'] != self.last_recommendation['action']:
            alerts.append({
                'type': 'RECOMMENDATION_CHANGE',
                'message': f"Recommendation changed: {self.last_recommendation['action']} → {current_analysis['recommendation']['action']}",
                'severity': 'HIGH'
            })

        # Check for parabolic status change
        current_parabolic = current_analysis['parabolic']['is_parabolic']
        if self.last_analysis and self.last_analysis['parabolic']['is_parabolic'] != current_parabolic:
            status = "ENTERED" if current_parabolic else "EXITED"
            alerts.append({
                'type': 'PARABOLIC_CHANGE',
                'message': f"Market {status} parabolic bull run!",
                'severity': 'CRITICAL'
            })

        # Check for significant price move (>3% in analysis interval)
        if self.last_analysis:
            price_change = ((current_analysis['current_price'] - self.last_analysis['current_price'])
                          / self.last_analysis['current_price']) * 100
            if abs(price_change) > 3.0:
                alerts.append({
                    'type': 'PRICE_SPIKE',
                    'message': f"Significant price move: {price_change:+.2f}%",
                    'severity': 'MEDIUM'
                })

        # Trigger alerts
        for alert in alerts:
            self._trigger_alert(alert, current_analysis)

        # Update last recommendation
        self.last_recommendation = current_analysis['recommendation']

    def _trigger_alert(self, alert, analysis):
        """Trigger an alert"""
        alert['timestamp'] = datetime.now()
        self.alert_history.append(alert)

        # Print alert
        severity_emoji = {'CRITICAL': '🚨', 'HIGH': '⚠️', 'MEDIUM': '📊', 'LOW': 'ℹ️'}
        emoji = severity_emoji.get(alert['severity'], '📢')

        print(f"\n{emoji} ALERT [{alert['severity']}]: {alert['message']}")
        print(f"   Price: ${analysis['current_price']:,.2f}")
        print(f"   Action: {analysis['recommendation']['action']}")
        print(f"   Confidence: {analysis['recommendation']['confidence']:.0f}%\n")

        # Custom callback
        if self.on_alert_callback:
            self.on_alert_callback(alert, analysis)

    def display_dashboard(self):
        """Display real-time dashboard"""
        print(f"\n{'='*80}")
        print(f"{'REAL-TIME ETHEREUM MARKET MONITOR':^80}")
        print(f"{'='*80}\n")

        while True:
            try:
                # Get current data
                price = self.ws_client.get_current_price()
                ticker = self.ws_client.get_ticker()
                current_candle = self.ws_client.get_current_ohlc()
                order_book = self.ws_client.get_order_book(depth=3)

                # Run analysis periodically
                if self._should_run_analysis():
                    analysis = self._analyze_market()
                    if analysis:
                        self._display_analysis(analysis)

                # Display live data
                print(f"\r{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | ", end='')

                if price:
                    print(f"💰 ${price:,.2f}", end='')

                if ticker:
                    spread = ticker['spread']
                    print(f" | Bid: ${ticker['bid']:,.2f} | Ask: ${ticker['ask']:,.2f} | Spread: ${spread:.2f}", end='')

                if current_candle:
                    candle_change = ((current_candle['close'] - current_candle['open']) / current_candle['open']) * 100
                    candle_emoji = '🟢' if candle_change > 0 else '🔴' if candle_change < 0 else '⚪'
                    print(f" | {candle_emoji} Candle: {candle_change:+.2f}%", end='')

                if order_book:
                    best_bid = order_book['bids'][0][0] if order_book['bids'] else 0
                    best_ask = order_book['asks'][0][0] if order_book['asks'] else 0
                    print(f" | L2: ${best_bid:.2f}/${best_ask:.2f}", end='')

                # Analysis status
                if self.last_analysis:
                    action = self.last_analysis['recommendation']['action']
                    confidence = self.last_analysis['recommendation']['confidence']
                    action_emoji = '🟢' if action == 'ENTER LONG' else '🔴' if action == 'SHORT' else '⚪'
                    print(f" | {action_emoji} {action} ({confidence:.0f}%)", end='')

                print(' ' * 10, end='', flush=True)  # Clear rest of line

                time.sleep(1)

            except KeyboardInterrupt:
                print("\n\nStopping monitor...")
                break
            except Exception as e:
                print(f"\nError in dashboard: {e}")
                time.sleep(1)

    def _display_analysis(self, analysis):
        """Display full analysis results"""
        print(f"\n\n{'='*80}")
        print(f"📊 MARKET ANALYSIS UPDATE - {analysis['timestamp'].strftime('%H:%M:%S')}")
        print(f"{'='*80}")

        # Current Price
        print(f"\n💰 Current Price: ${analysis['current_price']:,.2f}")

        # Parabolic Status
        parabolic = analysis['parabolic']
        status_emoji = '🚀' if parabolic['is_parabolic'] else '⚪'
        print(f"\n{status_emoji} Parabolic Bull Run: {'YES' if parabolic['is_parabolic'] else 'NO'}")
        print(f"   Confidence: {parabolic['confidence']:.0f}%")
        print(f"   Criteria Met: {parabolic['criteria_met']}/5")
        print(f"   Distance from 200 SMA: {parabolic['distance_from_200_sma']:+.1f}%")

        # Recommendation
        rec = analysis['recommendation']
        action_emoji = '🟢' if rec['action'] == 'ENTER LONG' else '🔴' if 'SHORT' in rec['action'] else '⚪'
        print(f"\n{action_emoji} Recommendation: {rec['action']}")
        print(f"   Confidence: {rec['confidence']:.0f}%")
        print(f"   Risk Level: {rec['risk_level']}")

        if rec['action'] != 'WAIT':
            print(f"\n📊 Trading Levels:")
            print(f"   Entry Zone: ${rec['entry_min']:,.2f} - ${rec['entry_max']:,.2f}")
            print(f"   Stop Loss: ${rec['stop_loss']:,.2f} (-{((analysis['current_price'] - rec['stop_loss'])/analysis['current_price']*100):.1f}%)")
            print(f"   Take Profit: ${rec['take_profit']:,.2f} (+{((rec['take_profit'] - analysis['current_price'])/analysis['current_price']*100):.1f}%)")
            print(f"   Risk/Reward: 1:{rec['risk_reward_ratio']:.1f}")

        # Key Reasoning
        print(f"\n🧠 Key Points:")
        for reason in rec['reasoning'][:5]:
            print(f"   • {reason}")

        print(f"\n{'='*80}\n")

    def start(self):
        """Start the real-time monitor"""
        print(f"\n{'='*80}")
        print(f"Starting Real-Time Market Monitor")
        print(f"Analysis Interval: {self.analysis_interval} seconds")
        print(f"{'='*80}\n")

        # Start WebSocket client
        if not self.ws_client.start():
            print("Failed to start WebSocket client")
            return False

        print("✓ WebSocket connected")
        print("✓ Real-time data streaming active")
        print("✓ Analysis engine ready")
        print("\nStarting dashboard...\n")

        # Wait for initial data
        time.sleep(2)

        # Run initial analysis
        self._analyze_market()

        # Start dashboard
        self.display_dashboard()

        return True

    def stop(self):
        """Stop the monitor"""
        self.ws_client.stop()


def main():
    """Main function"""
    # Create monitor with 60-second analysis updates
    monitor = RealTimeMarketMonitor(pair='ETH/USD', analysis_interval=60)

    # Optional: Add alert callback for Discord, etc.
    def handle_alert(alert, analysis):
        # Here you could send Discord notifications, log to file, etc.
        # For now, just using console output
        pass

    monitor.on_alert_callback = handle_alert

    # Start monitoring
    try:
        monitor.start()
    except KeyboardInterrupt:
        print("\n\nStopping...")
    finally:
        monitor.stop()
        print("\nMonitor stopped.")


if __name__ == "__main__":
    main()
