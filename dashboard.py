"""
Flask Dashboard for Ethereum Trading Strategy Metrics
"""
from flask import Flask, render_template, jsonify
import pandas as pd
import json
import os
from datetime import datetime
import config

app = Flask(__name__)

def get_latest_results():
    """Get the most recent backtest results"""
    results_dir = config.RESULTS_DIR
    
    # Find latest files
    metrics_files = [f for f in os.listdir(results_dir) if f.startswith('metrics_') and f.endswith('.json')]
    trades_files = [f for f in os.listdir(results_dir) if f.startswith('trades_') and f.endswith('.csv')]
    equity_files = [f for f in os.listdir(results_dir) if f.startswith('equity_curve_') and f.endswith('.csv')]
    
    if not metrics_files:
        return None, None, None
    
    # Get most recent
    latest_metrics = sorted(metrics_files)[-1]
    latest_trades = sorted(trades_files)[-1] if trades_files else None
    latest_equity = sorted(equity_files)[-1] if equity_files else None
    
    # Load data
    metrics = None
    trades = None
    equity = None
    
    try:
        with open(os.path.join(results_dir, latest_metrics), 'r') as f:
            metrics = json.load(f)
            
        if latest_trades:
            trades = pd.read_csv(os.path.join(results_dir, latest_trades))
            
        if latest_equity:
            equity = pd.read_csv(os.path.join(results_dir, latest_equity))
    except Exception as e:
        print(f"Error loading results: {e}")
    
    return metrics, trades, equity

@app.route('/')
def dashboard():
    """Main dashboard page"""
    metrics, trades, equity = get_latest_results()
    
    if metrics is None:
        return render_template('no_data.html')
    
    return render_template('dashboard.html', 
                         metrics=metrics,
                         timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

@app.route('/api/equity_curve')
def equity_curve_api():
    """API endpoint for equity curve data"""
    _, _, equity = get_latest_results()
    
    if equity is None:
        return jsonify({'error': 'No data available'})
    
    data = {
        'timestamps': equity['timestamp'].tolist(),
        'equity': equity['equity'].tolist()
    }
    
    return jsonify(data)

@app.route('/api/trades')
def trades_api():
    """API endpoint for trades data"""
    _, trades, _ = get_latest_results()
    
    if trades is None:
        return jsonify({'error': 'No data available'})
    
    # Get only exit trades for analysis
    exit_trades = trades[trades['action'] == 'EXIT']
    
    data = {
        'timestamps': exit_trades['timestamp'].tolist(),
        'pnl': exit_trades['net_pnl'].tolist(),
        'directions': exit_trades['direction'].tolist(),
        'exit_reasons': exit_trades['exit_reason'].tolist()
    }
    
    return jsonify(data)

@app.route('/api/metrics')
def metrics_api():
    """API endpoint for metrics"""
    metrics, _, _ = get_latest_results()
    
    if metrics is None:
        return jsonify({'error': 'No data available'})
    
    return jsonify(metrics)

@app.route('/trades')
def trades_page():
    """Detailed trades page"""
    metrics, trades, _ = get_latest_results()
    
    if trades is None:
        return render_template('no_data.html')
    
    # Convert to HTML table
    exit_trades = trades[trades['action'] == 'EXIT']
    
    return render_template('trades.html', 
                         trades=exit_trades.to_dict('records'),
                         metrics=metrics)

if __name__ == '__main__':
    print("=" * 60)
    print("Starting Ethereum Trading Dashboard")
    print("=" * 60)
    print("Dashboard will be available at: http://127.0.0.1:5002")
    print("Press CTRL+C to stop the server")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5002)
