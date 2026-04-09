"""
Automated Strategy Optimizer
Find strategy with: 60%+ win rate, 50%+ avg returns, <10% fees
"""
import pandas as pd
import numpy as np
from datetime import datetime
import json
import os
from indicators import TechnicalIndicators
import itertools

class StrategyOptimizer:
    """
    Systematic strategy optimization to find profitable parameters
    
    Target:
    - Win rate: 60%+
    - Avg return per trade: 50%+
    - Trading fees: <10% of profits
    """
    
    def __init__(self, data_file='data/eth_usd_60m_365d.csv'):
        self.data_file = data_file
        self.df = None
        self.best_strategy = None
        self.best_metrics = None
        self.results = []
        
    def load_data(self):
        """Load historical data"""
        print(f"Loading data from {self.data_file}...")
        self.df = pd.read_csv(self.data_file)
        self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
        print(f"Loaded {len(self.df)} candles")
        
        # Add all indicators
        self.df = TechnicalIndicators.add_all_indicators(self.df, timeframe='1h')
        print("Indicators calculated")
        
    def backtest_strategy(self, params):
        """
        Backtest a specific parameter set
        
        Returns:
            dict: Performance metrics
        """
        leverage = params['leverage']
        capital = 7500
        stop_loss_pct = params['stop_loss_pct']
        take_profit_pct = params['take_profit_pct']
        momentum_threshold = params['momentum_threshold']
        volume_multiplier = params['volume_multiplier']
        rsi_upper = params['rsi_upper']
        rsi_lower = params['rsi_lower']
        use_regime_filter = params['use_regime_filter']
        regime = params['regime']  # 'bull', 'bear', or 'both'
        entry_type = params['entry_type']  # 'breakout', 'pullback', 'reversal'
        max_hold_hours = params['max_hold_hours']
        
        # Trading costs
        fee_pct = 0.08  # Taker fee
        slippage_pct = 0.05
        funding_rate = 0.0034
        
        trades = []
        position = None
        entry_price = 0
        entry_time = None
        entry_idx = 0
        equity = capital
        
        for idx in range(200, len(self.df)):
            if equity <= 0:
                break
                
            row = self.df.iloc[idx]
            
            # Exit logic
            if position is not None:
                current_price = row['close']
                
                # Calculate P&L
                if position == 1:  # Long
                    pnl_pct = ((current_price - entry_price) / entry_price) * 100
                else:  # Short
                    pnl_pct = ((entry_price - current_price) / entry_price) * 100
                
                should_exit = False
                exit_reason = None
                
                # Stop loss
                if pnl_pct <= -stop_loss_pct:
                    should_exit = True
                    exit_reason = 'stop_loss'
                
                # Take profit
                elif pnl_pct >= take_profit_pct:
                    should_exit = True
                    exit_reason = 'take_profit'
                
                # Max hold time
                elif (row['timestamp'] - entry_time).total_seconds() / 3600 >= max_hold_hours:
                    should_exit = True
                    exit_reason = 'max_hold_time'
                
                if should_exit:
                    # Calculate P&L with costs
                    pnl_pct_leveraged = pnl_pct * leverage
                    pnl_dollar = equity * (pnl_pct_leveraged / 100)
                    
                    # Costs
                    fees = equity * leverage * (fee_pct / 100) * 2
                    slippage = equity * leverage * (slippage_pct / 100) * 2
                    hold_hours = (row['timestamp'] - entry_time).total_seconds() / 3600
                    funding = equity * leverage * funding_rate * hold_hours
                    
                    net_pnl = pnl_dollar - fees - slippage - funding
                    
                    trades.append({
                        'entry_time': entry_time,
                        'exit_time': row['timestamp'],
                        'direction': 'LONG' if position == 1 else 'SHORT',
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'pnl_pct': pnl_pct,
                        'pnl_pct_leveraged': pnl_pct_leveraged,
                        'net_pnl': net_pnl,
                        'fees': fees,
                        'exit_reason': exit_reason
                    })
                    
                    equity += net_pnl
                    position = None
                    entry_price = 0
                    entry_time = None
                    
            # Entry logic
            else:
                # Market regime filter
                if use_regime_filter:
                    market_regime = row.get('market_regime', 'neutral')
                    
                    if regime == 'bull' and market_regime != 'bull':
                        continue
                    elif regime == 'bear' and market_regime != 'bear':
                        continue
                
                # Basic filters
                if pd.isna(row['sma_60']) or pd.isna(row['sma_200']):
                    continue
                
                if not row.get('is_trending', False):
                    continue
                
                if row['volume_spike'] < volume_multiplier:
                    continue
                
                # Entry type specific logic
                current_price = row['close']
                momentum = row['momentum_1h']
                
                # LONG conditions
                if regime in ['bull', 'both']:
                    if entry_type == 'breakout':
                        # Breaking high with momentum
                        if (momentum > momentum_threshold and
                            row['rsi'] < rsi_upper and
                            current_price > row['sma_60']):
                            
                            position = 1
                            entry_price = current_price
                            entry_time = row['timestamp']
                            entry_idx = idx
                    
                    elif entry_type == 'pullback':
                        # Pullback to SMA with bounce
                        dist_from_sma60 = abs((current_price - row['sma_60']) / row['sma_60'] * 100)
                        if (dist_from_sma60 < 2.0 and  # Within 2% of SMA60
                            momentum > 0.3 and  # Slight upward momentum
                            row['rsi'] < rsi_upper and
                            current_price > row['sma_200']):
                            
                            position = 1
                            entry_price = current_price
                            entry_time = row['timestamp']
                            entry_idx = idx
                    
                    elif entry_type == 'reversal':
                        # Oversold reversal
                        if (row['rsi'] < rsi_lower and
                            momentum > momentum_threshold and
                            row['volume_spike'] > volume_multiplier * 1.5):
                            
                            position = 1
                            entry_price = current_price
                            entry_time = row['timestamp']
                            entry_idx = idx
                
                # SHORT conditions
                if regime in ['bear', 'both'] and position is None:
                    if entry_type == 'breakout':
                        # Breaking low with momentum
                        if (momentum < -momentum_threshold and
                            row['rsi'] > rsi_lower and
                            current_price < row['sma_60']):
                            
                            position = -1
                            entry_price = current_price
                            entry_time = row['timestamp']
                            entry_idx = idx
                    
                    elif entry_type == 'reversal':
                        # Overbought reversal
                        if (row['rsi'] > rsi_upper and
                            momentum < -momentum_threshold and
                            row['volume_spike'] > volume_multiplier * 1.5):
                            
                            position = -1
                            entry_price = current_price
                            entry_time = row['timestamp']
                            entry_idx = idx
        
        # Calculate metrics
        if len(trades) == 0:
            return None
        
        trades_df = pd.DataFrame(trades)
        wins = trades_df[trades_df['net_pnl'] > 0]
        losses = trades_df[trades_df['net_pnl'] <= 0]
        
        win_rate = len(wins) / len(trades) * 100
        avg_win = wins['net_pnl'].mean() if len(wins) > 0 else 0
        avg_loss = losses['net_pnl'].mean() if len(losses) > 0 else 0
        avg_return_per_trade = ((equity - capital) / len(trades)) / capital * 100
        total_fees = trades_df['fees'].sum()
        total_profit = equity - capital
        fees_pct_of_profit = (total_fees / abs(total_profit) * 100) if total_profit != 0 else 999
        
        return {
            'params': params,
            'total_trades': len(trades),
            'win_rate': win_rate,
            'avg_return_per_trade': avg_return_per_trade,
            'final_equity': equity,
            'total_return': (equity - capital) / capital * 100,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'fees_pct_of_profit': fees_pct_of_profit,
            'total_fees': total_fees
        }
    
    def optimize(self, max_iterations=500):
        """
        Run optimization loop to find best strategy
        
        Target criteria:
        - Win rate >= 60%
        - Avg return per trade >= 50%
        - Fees < 10% of profits
        """
        print("\n" + "="*70)
        print("STARTING STRATEGY OPTIMIZATION")
        print("="*70)
        print(f"\nTarget Criteria:")
        print(f"  - Win Rate: >= 60%")
        print(f"  - Avg Return per Trade: >= 50%")
        print(f"  - Fees: < 10% of profits")
        print(f"\nMax iterations: {max_iterations}")
        print("\n" + "="*70)
        
        # Parameter grid
        param_grid = {
            'leverage': [3, 5, 7, 10],
            'stop_loss_pct': [2.0, 3.0, 4.0, 5.0],
            'take_profit_pct': [4.0, 6.0, 8.0, 10.0],
            'momentum_threshold': [0.5, 1.0, 1.5, 2.0],
            'volume_multiplier': [1.2, 1.5, 2.0],
            'rsi_upper': [70, 75, 80],
            'rsi_lower': [20, 25, 30],
            'use_regime_filter': [True],
            'regime': ['bull', 'bear', 'both'],
            'entry_type': ['breakout', 'pullback', 'reversal'],
            'max_hold_hours': [4, 6, 8, 12]
        }
        
        # Generate all combinations (sample if too many)
        keys = list(param_grid.keys())
        values = list(param_grid.values())
        
        all_combinations = list(itertools.product(*values))
        
        # Limit to max_iterations
        if len(all_combinations) > max_iterations:
            import random
            random.seed(42)
            combinations = random.sample(all_combinations, max_iterations)
        else:
            combinations = all_combinations
        
        print(f"Testing {len(combinations)} parameter combinations...\n")
        
        best_score = 0
        iteration = 0
        strategies_meeting_criteria = []
        
        for combo in combinations:
            iteration += 1
            
            params = dict(zip(keys, combo))
            
            # Run backtest
            metrics = self.backtest_strategy(params)
            
            if metrics is None:
                continue
            
            # Check if meets criteria
            meets_criteria = (
                metrics['win_rate'] >= 60 and
                metrics['avg_return_per_trade'] >= 50 and
                metrics['fees_pct_of_profit'] < 10 and
                metrics['total_trades'] >= 5  # Minimum sample size
            )
            
            if meets_criteria:
                strategies_meeting_criteria.append(metrics)
                print(f"\n{'='*70}")
                print(f"✅ STRATEGY FOUND - Iteration {iteration}")
                print(f"{'='*70}")
                self._print_metrics(metrics)
            
            # Score function (even if doesn't meet all criteria)
            score = (
                metrics['win_rate'] * 0.4 +
                min(metrics['avg_return_per_trade'], 100) * 0.4 +
                max(0, 20 - metrics['fees_pct_of_profit']) * 0.2
            )
            
            if score > best_score:
                best_score = score
                self.best_strategy = params
                self.best_metrics = metrics
            
            # Progress update
            if iteration % 50 == 0:
                print(f"\nProgress: {iteration}/{len(combinations)} tested")
                print(f"Best score so far: {best_score:.1f}")
                if self.best_metrics:
                    print(f"  Win rate: {self.best_metrics['win_rate']:.1f}%")
                    print(f"  Avg return: {self.best_metrics['avg_return_per_trade']:.1f}%")
                    print(f"  Fees: {self.best_metrics['fees_pct_of_profit']:.1f}%")
        
        print(f"\n{'='*70}")
        print("OPTIMIZATION COMPLETE")
        print(f"{'='*70}")
        
        if len(strategies_meeting_criteria) > 0:
            print(f"\n✅ Found {len(strategies_meeting_criteria)} strategies meeting ALL criteria!")
            
            # Sort by total return
            strategies_meeting_criteria.sort(key=lambda x: x['total_return'], reverse=True)
            
            print("\nTop 3 Strategies:")
            for i, metrics in enumerate(strategies_meeting_criteria[:3]):
                print(f"\n{'-'*70}")
                print(f"Strategy #{i+1}:")
                self._print_metrics(metrics)
            
            self.best_strategy = strategies_meeting_criteria[0]['params']
            self.best_metrics = strategies_meeting_criteria[0]
            
        else:
            print(f"\n⚠️  No strategy met ALL criteria.")
            print(f"\nBest strategy found (closest):")
            if self.best_metrics:
                self._print_metrics(self.best_metrics)
        
        return self.best_strategy, self.best_metrics
    
    def _print_metrics(self, metrics):
        """Print formatted metrics"""
        print(f"\nParameters:")
        for key, val in metrics['params'].items():
            print(f"  {key}: {val}")
        
        print(f"\nPerformance:")
        print(f"  Total Trades: {metrics['total_trades']}")
        print(f"  Win Rate: {metrics['win_rate']:.1f}%")
        print(f"  Avg Return per Trade: {metrics['avg_return_per_trade']:.1f}%")
        print(f"  Total Return: {metrics['total_return']:.1f}%")
        print(f"  Final Equity: ${metrics['final_equity']:.2f}")
        print(f"  Avg Win: ${metrics['avg_win']:.2f}")
        print(f"  Avg Loss: ${metrics['avg_loss']:.2f}")
        print(f"  Fees (% of profit): {metrics['fees_pct_of_profit']:.1f}%")
        print(f"  Total Fees: ${metrics['total_fees']:.2f}")
        
        # Check criteria
        print(f"\nCriteria Met:")
        print(f"  Win Rate >= 60%: {'✅' if metrics['win_rate'] >= 60 else '❌'} ({metrics['win_rate']:.1f}%)")
        print(f"  Avg Return >= 50%: {'✅' if metrics['avg_return_per_trade'] >= 50 else '❌'} ({metrics['avg_return_per_trade']:.1f}%)")
        print(f"  Fees < 10%: {'✅' if metrics['fees_pct_of_profit'] < 10 else '❌'} ({metrics['fees_pct_of_profit']:.1f}%)")
    
    def save_results(self):
        """Save optimization results"""
        if self.best_strategy is None:
            print("No results to save")
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'results/optimization_results_{timestamp}.json'
        
        results = {
            'timestamp': timestamp,
            'best_strategy': self.best_strategy,
            'best_metrics': self.best_metrics
        }
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n✅ Results saved to {filename}")

def main():
    """Run optimization"""
    optimizer = StrategyOptimizer()
    optimizer.load_data()
    
    best_params, best_metrics = optimizer.optimize(max_iterations=500)
    
    if best_params:
        optimizer.save_results()
        
        print(f"\n{'='*70}")
        print("FINAL RECOMMENDATION:")
        print(f"{'='*70}")
        
        if best_metrics['win_rate'] >= 60 and best_metrics['avg_return_per_trade'] >= 50:
            print("\n✅ SUCCESS! Found strategy meeting all targets!")
            print("\nImplement these parameters in config.py:")
            print(f"\nLEVERAGE = {best_params['leverage']}")
            print(f"STOP_LOSS_PCT = {best_params['stop_loss_pct']}")
            print(f"TAKE_PROFIT_PCT = {best_params['take_profit_pct']}")
            print(f"MOMENTUM_THRESHOLD_1H = {best_params['momentum_threshold']}")
            print(f"VOLUME_SPIKE_MULTIPLIER = {best_params['volume_multiplier']}")
            print(f"RSI_OVERBOUGHT = {best_params['rsi_upper']}")
            print(f"RSI_OVERSOLD = {best_params['rsi_lower']}")
            print(f"MAX_HOLD_TIME_HOURS = {best_params['max_hold_hours']}")
            print(f"\nEntry Type: {best_params['entry_type']}")
            print(f"Trade Regime: {best_params['regime']} markets only")
        else:
            print("\n⚠️  Could not find strategy meeting ALL targets.")
            print("\nClosest strategy found (implement with caution):")
            print(f"\nActual Performance:")
            print(f"  Win Rate: {best_metrics['win_rate']:.1f}% (target: 60%)")
            print(f"  Avg Return: {best_metrics['avg_return_per_trade']:.1f}% (target: 50%)")
            print(f"  Fees: {best_metrics['fees_pct_of_profit']:.1f}% (target: <10%)")

if __name__ == "__main__":
    main()
