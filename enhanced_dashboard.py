"""
Enhanced Flask Dashboard with CoinGlass Data & Trading Recommendations
"""
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime
import config
from coinglass_client import CoinGlassClient
from recommendation_engine import RecommendationEngine

app = Flask(__name__)
CORS(app)

# Initialize clients
coinglass = CoinGlassClient()
recommendation_engine = None


def convert_numpy_types(obj):
    """Convert numpy types to Python native types for JSON serialization"""
    if isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_numpy_types(item) for item in obj)
    elif isinstance(obj, (np.integer, np.int64, np.int32, np.int16, np.int8)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32, np.float16)):
        return float(obj)
    elif isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (pd.Timestamp, datetime)):
        return obj.isoformat() if hasattr(obj, 'isoformat') else str(obj)
    elif pd.isna(obj):
        return None
    elif obj is None:
        return None
    else:
        return obj


def get_latest_results():
    """Get the most recent backtest results"""
    results_dir = config.RESULTS_DIR

    # Find latest files
    metrics_files = [f for f in os.listdir(results_dir) if f.startswith('metrics_') and f.endswith('.json')]

    if not metrics_files:
        return None

    latest_metrics = sorted(metrics_files)[-1]

    try:
        with open(os.path.join(results_dir, latest_metrics), 'r') as f:
            metrics = json.load(f)
        return metrics
    except Exception as e:
        print(f"Error loading results: {e}")
        return None


def load_historical_data():
    """Load historical data for recommendation engine"""
    import glob

    # Auto-detect available data files
    data_files = glob.glob(f'{config.DATA_DIR}/eth_usd_*_{config.LOOKBACK_DAYS}d.csv')
    if not data_files:
        data_files = glob.glob(f'{config.DATA_DIR}/eth_usd_*.csv')

    if not data_files:
        print(f"❌ No data files found in {config.DATA_DIR}/")
        return None

    data_file = sorted(data_files)[-1]
    print(f"Using data: {os.path.basename(data_file)}")

    try:
        df = pd.read_csv(data_file)
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        # Add indicators if not present
        if 'momentum_1h' not in df.columns:
            from indicators import TechnicalIndicators
            df = TechnicalIndicators.add_all_indicators(df, timeframe='4h')

        return df
    except FileNotFoundError:
        print(f"❌ Data file not found: {data_file}")
        return None


@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('enhanced_dashboard.html',
                         timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))


@app.route('/api/recommendation', methods=['GET'])
def get_recommendation():
    """Get trading recommendation"""
    global recommendation_engine

    try:
        # Load data if needed
        if recommendation_engine is None:
            df = load_historical_data()
            if df is None:
                return jsonify({'error': 'Historical data not available. Run data_collector.py first.'})

            recommendation_engine = RecommendationEngine(df=df, coinglass_client=coinglass)

        # Get fresh recommendation
        fetch_coinglass = request.args.get('fetch_coinglass', 'false').lower() == 'true'
        recommendation = recommendation_engine.get_recommendation(fetch_coinglass=fetch_coinglass)

        # Convert numpy types to native Python types
        recommendation = convert_numpy_types(recommendation)

        return jsonify(recommendation)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/coinglass/liquidations', methods=['GET'])
def get_liquidations():
    """Get liquidation heatmap data"""
    try:
        symbol = request.args.get('symbol', 'ETH')
        data = coinglass.get_liquidation_heatmap(symbol=symbol)
        data = convert_numpy_types(data)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/coinglass/volume_profile', methods=['GET'])
def get_volume_profile():
    """Get volume profile data"""
    try:
        symbol = request.args.get('symbol', 'ETH')
        timeframe = request.args.get('timeframe', '1d')
        data = coinglass.get_volume_profile(symbol=symbol, timeframe=timeframe)
        data = convert_numpy_types(data)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/coinglass/long_short_ratio', methods=['GET'])
def get_long_short_ratio():
    """Get long/short ratio"""
    try:
        symbol = request.args.get('symbol', 'ETH')
        data = coinglass.get_long_short_ratio(symbol=symbol)
        data = convert_numpy_types(data)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/coinglass/market_summary', methods=['GET'])
def get_market_summary():
    """Get complete market summary"""
    try:
        symbol = request.args.get('symbol', 'ETH')
        data = coinglass.get_market_summary(symbol=symbol)
        data = convert_numpy_types(data)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/backtest/metrics', methods=['GET'])
def get_backtest_metrics():
    """Get latest backtest metrics"""
    metrics = get_latest_results()
    if metrics is None:
        return jsonify({'error': 'No backtest results available'})
    return jsonify(metrics)


@app.route('/api/parabolic_check', methods=['GET'])
def check_parabolic():
    """Check if market is in parabolic bull run"""
    global recommendation_engine

    try:
        if recommendation_engine is None:
            df = load_historical_data()
            if df is None:
                return jsonify({'error': 'Historical data not available'})

            recommendation_engine = RecommendationEngine(df=df)

        bull_run = recommendation_engine.detect_parabolic_bull_run()

        # Convert numpy types to native Python types
        bull_run = convert_numpy_types(bull_run)

        return jsonify(bull_run)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'services': {
            'coinglass': 'available',
            'recommendation_engine': 'available' if recommendation_engine else 'not_initialized'
        }
    })


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("🚀 ENHANCED ETHEREUM TRADING DASHBOARD")
    print("=" * 70)
    print("\n📊 Features:")
    print("  - Real-time trading recommendations")
    print("  - CoinGlass liquidation heatmaps")
    print("  - Volume profiles at price levels")
    print("  - Long/Short ratio analysis")
    print("  - Parabolic bull run detection")
    print("\n🌐 Dashboard: http://127.0.0.1:5003")
    print("📡 API Docs: http://127.0.0.1:5003/api/")
    print("\n⚡ Press CTRL+C to stop")
    print("=" * 70 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5003)
