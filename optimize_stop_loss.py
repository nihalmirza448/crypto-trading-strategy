"""
Systematically test different stop loss values to find the optimal configuration
"""
import pandas as pd
import json
from backtester import Backtester
import config

def test_stop_loss_values():
    """Test multiple stop loss values and compare results"""
    
    # Stop loss values to test (in percentage)
    stop_loss_values = [0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0]
    
    # Store results
    results = []
    
    print("="*80)
    print("STOP LOSS OPTIMIZATION - TESTING MULTIPLE VALUES")
    print("="*80)
    print(f"\nTesting {len(stop_loss_values)} different stop loss values...")
    print(f"Leverage: {config.LEVERAGE}x")
    print(f"Timeframe: {config.TIMEFRAME}")
    print(f"Period: {config.LOOKBACK_DAYS} days")
    print("="*80 + "\n")
    
    for stop_loss_pct in stop_loss_values:
        print(f"\n{'='*80}")
        print(f"Testing Stop Loss: {stop_loss_pct}%")
        print(f"{'='*80}")
        
        # Update config temporarily
        original_stop = config.STOP_LOSS_PCT
        original_bear_stop = config.BEAR_STOP_LOSS_PCT
        
        config.STOP_LOSS_PCT = stop_loss_pct
        config.BEAR_STOP_LOSS_PCT = stop_loss_pct
        
        # Adjust take profit to be 2x stop loss (maintain risk/reward)
        original_tp = config.TAKE_PROFIT_PCT
        original_bear_tp = config.BEAR_TAKE_PROFIT_PCT
        config.TAKE_PROFIT_PCT = stop_loss_pct * 2
        config.BEAR_TAKE_PROFIT_PCT = stop_loss_pct * 2
        
        try:
            # Determine data file based on timeframe
            if config.TIMEFRAME == '4h':
                data_file = f'{config.DATA_DIR}/eth_usd_4h_{config.LOOKBACK_DAYS}d.csv'
            elif config.TIMEFRAME == '1d':
                data_file = f'{config.DATA_DIR}/eth_usd_1440m_{config.LOOKBACK_DAYS}d.csv'
            else:
                data_file = f'{config.DATA_DIR}/eth_usd_60m_{config.LOOKBACK_DAYS}d.csv'
            
            # Run backtest
            backtester = Backtester(
                data_file=data_file,
                leverage=config.LEVERAGE,
                capital=config.CAPITAL
            )
            backtester.load_data()
            backtester.prepare_data()
            backtester.run_backtest()
            metrics = backtester.calculate_metrics()
            
            # Store results
            result = {
                'stop_loss_pct': stop_loss_pct,
                'take_profit_pct': stop_loss_pct * 2,
                'total_trades': metrics['total_trades'],
                'win_rate': metrics['win_rate'],
                'winning_trades': metrics['winning_trades'],
                'losing_trades': metrics['losing_trades'],
                'avg_win': metrics['avg_win'],
                'avg_loss': metrics['avg_loss'],
                'profit_factor': metrics['profit_factor'],
                'total_return_pct': metrics['total_return_pct'],
                'final_equity': metrics['final_equity'],
                'gross_profit': metrics['gross_profit'],
                'gross_loss': metrics['gross_loss'],
                'breakeven_wr': abs(metrics['avg_loss'] / (metrics['avg_win'] + abs(metrics['avg_loss']))) * 100 if metrics['total_trades'] > 0 else 0,
                'wr_gap': abs(metrics['avg_loss'] / (metrics['avg_win'] + abs(metrics['avg_loss']))) * 100 - metrics['win_rate'] if metrics['total_trades'] > 0 else 999
            }
            results.append(result)
            
            print(f"\n✅ Completed:")
            print(f"   Trades: {metrics['total_trades']}, Win Rate: {metrics['win_rate']:.1f}%, Return: {metrics['total_return_pct']:.1f}%")
            
        except Exception as e:
            print(f"\n❌ Error testing {stop_loss_pct}%: {e}")
            results.append({
                'stop_loss_pct': stop_loss_pct,
                'error': str(e)
            })
        
        # Restore original config
        config.STOP_LOSS_PCT = original_stop
        config.BEAR_STOP_LOSS_PCT = original_bear_stop
        config.TAKE_PROFIT_PCT = original_tp
        config.BEAR_TAKE_PROFIT_PCT = original_bear_tp
    
    return results

def analyze_results(results):
    """Analyze and display results"""
    
    # Filter out errors
    valid_results = [r for r in results if 'error' not in r]
    
    if not valid_results:
        print("\n❌ No valid results to analyze")
        return
    
    # Convert to DataFrame for easy analysis
    df = pd.DataFrame(valid_results)
    
    print("\n" + "="*120)
    print("STOP LOSS OPTIMIZATION RESULTS")
    print("="*120)
    
    # Display table
    print(f"\n{'Stop':<6} {'TP':<6} {'Trades':<8} {'Wins':<6} {'Loss':<6} {'WR%':<8} {'Avg Win':<10} {'Avg Loss':<11} {'PF':<6} {'Return%':<10} {'BE WR%':<8} {'Gap%':<8}")
    print("-"*120)
    
    for _, row in df.iterrows():
        print(f"{row['stop_loss_pct']:<6.2f} {row['take_profit_pct']:<6.2f} "
              f"{row['total_trades']:<8} {row['winning_trades']:<6} {row['losing_trades']:<6} "
              f"{row['win_rate']:<8.1f} ${row['avg_win']:<9.0f} ${row['avg_loss']:<10.0f} "
              f"{row['profit_factor']:<6.2f} {row['total_return_pct']:<10.1f} "
              f"{row['breakeven_wr']:<8.1f} {row['wr_gap']:<8.1f}")
    
    print("\n" + "="*120)
    print("RANKINGS BY KEY METRICS")
    print("="*120)
    
    # Best by total return
    best_return = df.loc[df['total_return_pct'].idxmax()]
    print(f"\n🏆 BEST TOTAL RETURN:")
    print(f"   Stop: {best_return['stop_loss_pct']}%, WR: {best_return['win_rate']:.1f}%, Return: {best_return['total_return_pct']:.1f}%")
    
    # Best by win rate
    best_wr = df.loc[df['win_rate'].idxmax()]
    print(f"\n🎯 HIGHEST WIN RATE:")
    print(f"   Stop: {best_wr['stop_loss_pct']}%, WR: {best_wr['win_rate']:.1f}%, Return: {best_wr['total_return_pct']:.1f}%")
    
    # Best by profit factor
    best_pf = df.loc[df['profit_factor'].idxmax()]
    print(f"\n💰 BEST PROFIT FACTOR:")
    print(f"   Stop: {best_pf['stop_loss_pct']}%, PF: {best_pf['profit_factor']:.2f}, Return: {best_pf['total_return_pct']:.1f}%")
    
    # Smallest win rate gap (closest to break-even)
    best_gap = df.loc[df['wr_gap'].abs().idxmin()]
    print(f"\n📊 CLOSEST TO BREAK-EVEN:")
    print(f"   Stop: {best_gap['stop_loss_pct']}%, Need: {best_gap['breakeven_wr']:.1f}%, Have: {best_gap['win_rate']:.1f}%, Gap: {best_gap['wr_gap']:.1f}%")
    
    # Any profitable configs?
    profitable = df[df['total_return_pct'] > 0]
    if len(profitable) > 0:
        print(f"\n✅ PROFITABLE CONFIGURATIONS: {len(profitable)}")
        for _, row in profitable.iterrows():
            print(f"   Stop: {row['stop_loss_pct']}%, Return: {row['total_return_pct']:.1f}%")
    else:
        print(f"\n❌ NO PROFITABLE CONFIGURATIONS FOUND")
    
    # Save results
    df.to_csv('results/stop_loss_optimization.csv', index=False)
    print(f"\n📁 Full results saved to results/stop_loss_optimization.csv")
    
    return df

if __name__ == "__main__":
    results = test_stop_loss_values()
    df = analyze_results(results)
