"""
Backtesting engine for Ethereum swing trading strategy
"""
import pandas as pd
import numpy as np
import json
from datetime import datetime
import config
from indicators import TechnicalIndicators
from strategy import MomentumSwingStrategy
import matplotlib.pyplot as plt
import seaborn as sns

class Backtester:
    """Backtesting engine with comprehensive performance metrics"""
    
    def __init__(self, data_file, leverage=30, capital=1000):
        self.data_file = data_file
        self.leverage = leverage
        self.initial_capital = capital
        self.df = None
        self.trades = []
        self.equity_curve = []
        
    def load_data(self):
        """Load historical data from CSV"""
        # Determine data file based on timeframe in config
        if config.TIMEFRAME == '4h':
            data_file = f'{config.DATA_DIR}/eth_usd_4h_{config.LOOKBACK_DAYS}d.csv'
        elif config.TIMEFRAME == '1d':
            data_file = f'{config.DATA_DIR}/eth_usd_1440m_{config.LOOKBACK_DAYS}d.csv'
        else:
            data_file = f'{config.DATA_DIR}/eth_usd_60m_{config.LOOKBACK_DAYS}d.csv'
        
        print(f"Loading data from {data_file}...")
        self.df = pd.read_csv(data_file)
        self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
        print(f"Loaded {len(self.df)} candles")
        print(f"Date range: {self.df.iloc[0]['timestamp']} to {self.df.iloc[-1]['timestamp']}")
        return self.df
    
    def prepare_data(self):
        """Add technical indicators to data"""
        print("Calculating precision trading indicators...")
        print("  - 3 SMAs (60, 90, 180)")
        print("  - Trending regime detection")
        print("  - 24h high/low breakout levels")
        self.df = TechnicalIndicators.add_all_indicators(self.df, timeframe=config.TIMEFRAME)
        print("Indicators calculated successfully")
    
    def run_backtest(self):
        """Execute backtest"""
        print("\n" + "=" * 60)
        print("Running Backtest...")
        print("=" * 60)
        print(f"Initial Capital: ${self.initial_capital}")
        print(f"Leverage: {self.leverage}x")
        print(f"Position Size: ${self.initial_capital * self.leverage}")
        print("=" * 60 + "\n")
        
        # Initialize strategy
        strategy = MomentumSwingStrategy(leverage=self.leverage, capital=self.initial_capital)
        
        # Run strategy
        self.trades = strategy.run(self.df)
        
        # Track equity curve
        capital = self.initial_capital
        self.equity_curve = [{'timestamp': self.df.iloc[0]['timestamp'], 'equity': capital}]
        
        for trade in self.trades:
            if trade['action'] == 'EXIT':
                capital += trade['net_pnl']
                self.equity_curve.append({
                    'timestamp': trade['timestamp'],
                    'equity': capital
                })
        
        print(f"\nBacktest complete! Executed {len([t for t in self.trades if t['action'] == 'EXIT'])} trades")
        
    def calculate_metrics(self):
        """Calculate performance metrics"""
        exit_trades = [t for t in self.trades if t['action'] == 'EXIT']
        
        if not exit_trades:
            print("No trades executed!")
            return None
        
        # Basic metrics
        total_trades = len(exit_trades)
        winning_trades = [t for t in exit_trades if t['net_pnl'] > 0]
        losing_trades = [t for t in exit_trades if t['net_pnl'] <= 0]
        
        win_rate = len(winning_trades) / total_trades * 100
        
        total_pnl = sum(t['net_pnl'] for t in exit_trades)
        gross_profit = sum(t['net_pnl'] for t in winning_trades)
        gross_loss = abs(sum(t['net_pnl'] for t in losing_trades))
        
        avg_win = np.mean([t['net_pnl'] for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t['net_pnl'] for t in losing_trades]) if losing_trades else 0
        
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Equity curve analysis
        equity_df = pd.DataFrame(self.equity_curve)
        final_equity = equity_df.iloc[-1]['equity']
        total_return_pct = (final_equity - self.initial_capital) / self.initial_capital * 100
        
        # Drawdown analysis
        equity_df['peak'] = equity_df['equity'].cummax()
        equity_df['drawdown'] = (equity_df['equity'] - equity_df['peak']) / equity_df['peak'] * 100
        max_drawdown = equity_df['drawdown'].min()
        
        # Sharpe ratio (annualized)
        returns = equity_df['equity'].pct_change().dropna()
        if len(returns) > 0:
            sharpe_ratio = (returns.mean() / returns.std()) * np.sqrt(365 * 24 * 60) if returns.std() > 0 else 0
        else:
            sharpe_ratio = 0
        
        # Hold time analysis
        hold_times = [t['hold_time_hours'] for t in exit_trades]
        avg_hold_time = np.mean(hold_times)
        
        # Exit reason analysis
        exit_reasons = {}
        for t in exit_trades:
            reason = t['exit_reason']
            exit_reasons[reason] = exit_reasons.get(reason, 0) + 1
        
        # Liquidation simulation (if price moves against position by more than 1/leverage)
        liquidation_threshold = (1 / self.leverage) * 100
        liquidations = [t for t in exit_trades if abs(t['pnl_pct']) > liquidation_threshold and t['net_pnl'] < 0]
        
        metrics = {
            'total_trades': total_trades,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'gross_profit': gross_profit,
            'gross_loss': gross_loss,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'initial_capital': self.initial_capital,
            'final_equity': final_equity,
            'total_return_pct': total_return_pct,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'avg_hold_time_hours': avg_hold_time,
            'exit_reasons': exit_reasons,
            'liquidations': len(liquidations),
            'leverage': self.leverage
        }
        
        return metrics
    
    def print_results(self, metrics):
        """Print backtest results"""
        print("\n" + "=" * 60)
        print("BACKTEST RESULTS")
        print("=" * 60)
        
        print(f"\n📊 Trading Performance:")
        print(f"  Total Trades: {metrics['total_trades']}")
        print(f"  Winning Trades: {metrics['winning_trades']}")
        print(f"  Losing Trades: {metrics['losing_trades']}")
        print(f"  Win Rate: {metrics['win_rate']:.2f}%")
        
        print(f"\n💰 Profitability:")
        print(f"  Initial Capital: ${metrics['initial_capital']:.2f}")
        print(f"  Final Equity: ${metrics['final_equity']:.2f}")
        print(f"  Total P&L: ${metrics['total_pnl']:.2f}")
        print(f"  Total Return: {metrics['total_return_pct']:.2f}%")
        print(f"  Gross Profit: ${metrics['gross_profit']:.2f}")
        print(f"  Gross Loss: ${metrics['gross_loss']:.2f}")
        print(f"  Profit Factor: {metrics['profit_factor']:.2f}")
        
        print(f"\n📈 Risk Metrics:")
        print(f"  Max Drawdown: {metrics['max_drawdown']:.2f}%")
        print(f"  Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
        print(f"  Average Win: ${metrics['avg_win']:.2f}")
        print(f"  Average Loss: ${metrics['avg_loss']:.2f}")
        print(f"  Simulated Liquidations: {metrics['liquidations']}")
        
        print(f"\n⏱️  Trade Duration:")
        print(f"  Average Hold Time: {metrics['avg_hold_time_hours']:.1f} hours ({metrics['avg_hold_time_hours']/24:.1f} days)")
        
        print(f"\n🚪 Exit Reasons:")
        for reason, count in metrics['exit_reasons'].items():
            pct = (count / metrics['total_trades']) * 100
            print(f"  {reason}: {count} ({pct:.1f}%)")
        
        print("\n" + "=" * 60)
        
        # Warning about liquidations
        if metrics['liquidations'] > 0:
            print(f"\n⚠️  WARNING: {metrics['liquidations']} trades would have resulted in LIQUIDATION!")
            print(f"   At {self.leverage}x leverage, you can only afford a {100/self.leverage:.2f}% adverse move.")
        
    def save_results(self, metrics):
        """Save results to files"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save metrics
        metrics_file = f"{config.RESULTS_DIR}/metrics_{timestamp}.json"
        with open(metrics_file, 'w') as f:
            # Convert non-serializable values
            metrics_clean = metrics.copy()
            if np.isinf(metrics_clean['profit_factor']):
                metrics_clean['profit_factor'] = 'inf'
            json.dump(metrics_clean, f, indent=4)
        print(f"\n📁 Metrics saved to {metrics_file}")
        
        # Save trades
        trades_file = f"{config.RESULTS_DIR}/trades_{timestamp}.csv"
        trades_df = pd.DataFrame(self.trades)
        trades_df.to_csv(trades_file, index=False)
        print(f"📁 Trades saved to {trades_file}")
        
        # Save equity curve
        equity_file = f"{config.RESULTS_DIR}/equity_curve_{timestamp}.csv"
        equity_df = pd.DataFrame(self.equity_curve)
        equity_df.to_csv(equity_file, index=False)
        print(f"📁 Equity curve saved to {equity_file}")
        
        return metrics_file, trades_file, equity_file
    
    def plot_results(self):
        """Create visualization plots"""
        if not self.equity_curve:
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Backtest Results Visualization', fontsize=16)
        
        # Equity curve
        equity_df = pd.DataFrame(self.equity_curve)
        axes[0, 0].plot(equity_df['timestamp'], equity_df['equity'])
        axes[0, 0].axhline(y=self.initial_capital, color='r', linestyle='--', label='Initial Capital')
        axes[0, 0].set_title('Equity Curve')
        axes[0, 0].set_xlabel('Date')
        axes[0, 0].set_ylabel('Equity ($)')
        axes[0, 0].legend()
        axes[0, 0].grid(True)
        
        # Drawdown
        equity_df['peak'] = equity_df['equity'].cummax()
        equity_df['drawdown'] = (equity_df['equity'] - equity_df['peak']) / equity_df['peak'] * 100
        axes[0, 1].fill_between(equity_df['timestamp'], equity_df['drawdown'], 0, color='red', alpha=0.3)
        axes[0, 1].set_title('Drawdown')
        axes[0, 1].set_xlabel('Date')
        axes[0, 1].set_ylabel('Drawdown (%)')
        axes[0, 1].grid(True)
        
        # Trade P&L distribution
        exit_trades = [t for t in self.trades if t['action'] == 'EXIT']
        pnls = [t['net_pnl'] for t in exit_trades]
        axes[1, 0].hist(pnls, bins=30, edgecolor='black', alpha=0.7)
        axes[1, 0].axvline(x=0, color='r', linestyle='--')
        axes[1, 0].set_title('Trade P&L Distribution')
        axes[1, 0].set_xlabel('P&L ($)')
        axes[1, 0].set_ylabel('Frequency')
        axes[1, 0].grid(True)
        
        # Win/Loss pie chart
        winning = len([t for t in exit_trades if t['net_pnl'] > 0])
        losing = len([t for t in exit_trades if t['net_pnl'] <= 0])
        axes[1, 1].pie([winning, losing], labels=['Wins', 'Losses'], autopct='%1.1f%%',
                       colors=['green', 'red'], startangle=90)
        axes[1, 1].set_title('Win/Loss Ratio')
        
        plt.tight_layout()
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        plot_file = f"{config.RESULTS_DIR}/backtest_plot_{timestamp}.png"
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        print(f"📊 Plots saved to {plot_file}")
        
        # Don't show plot in command line
        plt.close()

def main():
    """Main backtesting function"""
    # Check if data file exists (now looking for 365-day data)
    data_file = f"{config.DATA_DIR}/eth_usd_60m_{config.LOOKBACK_DAYS}d.csv"
    
    import os
    if not os.path.exists(data_file):
        print(f"❌ Data file not found: {data_file}")
        print("Please run coinbase_collector.py first to fetch historical hourly data.")
        print(f"Looking for: {data_file}")
        return
    
    # Initialize backtester
    backtester = Backtester(
        data_file=data_file,
        leverage=config.LEVERAGE,
        capital=config.CAPITAL
    )
    
    # Load and prepare data
    backtester.load_data()
    backtester.prepare_data()
    
    # Run backtest
    backtester.run_backtest()
    
    # Calculate and display metrics
    metrics = backtester.calculate_metrics()
    if metrics:
        backtester.print_results(metrics)
        backtester.save_results(metrics)
        backtester.plot_results()
        
        print("\n✅ Backtesting complete!")
        print(f"\nNext steps:")
        print("1. Review the results in the {config.RESULTS_DIR}/ directory")
        print("2. Adjust strategy parameters in config.py if needed")
        print("3. Re-run backtest to optimize performance")
        print("4. Once satisfied, proceed to paper trading")
    else:
        print("❌ Backtest failed - no trades executed")

if __name__ == "__main__":
    main()
