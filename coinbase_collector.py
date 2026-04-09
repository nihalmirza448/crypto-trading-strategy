"""
Data collector for fetching historical Ethereum data from Coinbase
"""
import requests
import pandas as pd
import time
from datetime import datetime, timedelta
import config

class CoinbaseDataCollector:
    def __init__(self):
        self.base_url = "https://api.exchange.coinbase.com"
        
    def get_ohlc_data(self, pair='ETH-USD', granularity=3600, start=None, end=None):
        """
        Fetch OHLC data from Coinbase
        
        Args:
            pair: Trading pair (default: ETH-USD)
            granularity: Timeframe in seconds (60, 300, 900, 3600, 21600, 86400)
            start: ISO 8601 start time
            end: ISO 8601 end time
            
        Coinbase granularity options:
        - 60 = 1 minute
        - 300 = 5 minutes
        - 900 = 15 minutes
        - 3600 = 1 hour
        - 21600 = 6 hours
        - 86400 = 1 day
        """
        endpoint = f"{self.base_url}/products/{pair}/candles"
        params = {
            'granularity': granularity
        }
        
        if start:
            params['start'] = start
        if end:
            params['end'] = end
            
        try:
            response = requests.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if isinstance(data, dict) and 'message' in data:
                print(f"Coinbase API Error: {data['message']}")
                return None
            
            # Coinbase returns: [timestamp, low, high, open, close, volume]
            df = pd.DataFrame(data, columns=[
                'timestamp', 'low', 'high', 'open', 'close', 'volume'
            ])
            
            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
            
            # Reorder columns to match our format
            df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
            
            # Sort by timestamp ascending
            df = df.sort_values('timestamp')
            
            # Convert to float
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)
            
            return df
            
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            return None
        except Exception as e:
            print(f"Error fetching data: {e}")
            return None
    
    def fetch_historical_data(self, days=120, granularity=3600, interval_name="1h"):
        """
        Fetch complete historical data for specified number of days
        
        Args:
            days: Number of days to fetch
            granularity: Timeframe in seconds
            interval_name: Human-readable interval name for filename
        """
        print(f"Fetching {days} days of {interval_name} ETH/USD data from Coinbase...")
        
        # Coinbase limits to 300 candles per request
        max_candles_per_request = 300
        total_candles_needed = (days * 24 * 3600) // granularity
        total_requests = (total_candles_needed // max_candles_per_request) + 1
        
        print(f"Estimated {total_requests} API requests needed")
        print(f"Estimated time: {(total_requests * 0.4):.1f} seconds")
        print(f"Rate limit: Coinbase allows 10 requests/second (very generous)")
        print("=" * 60)
        
        all_data = []
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        current_end = end_time
        request_count = 0
        start_fetch_time = time.time()
        
        while current_end > start_time:
            # Calculate start time for this batch (300 candles back)
            current_start = current_end - timedelta(seconds=granularity * max_candles_per_request)
            
            # Don't go before the requested start time
            if current_start < start_time:
                current_start = start_time
            
            # Fetch data
            df = self.get_ohlc_data(
                pair='ETH-USD',
                granularity=granularity,
                start=current_start.isoformat(),
                end=current_end.isoformat()
            )
            
            if df is None or df.empty:
                print(f"Warning: No data returned for {current_start} to {current_end}")
                # Move backwards anyway
                current_end = current_start
                time.sleep(0.4)  # Rate limiting
                continue
            
            all_data.append(df)
            request_count += 1
            
            # Progress reporting
            if request_count % 5 == 0:
                elapsed = time.time() - start_fetch_time
                progress_pct = (request_count / total_requests) * 100
                print(f"Progress: {request_count}/{total_requests} requests ({progress_pct:.1f}%) | "
                      f"Fetched up to: {df.iloc[0]['timestamp']}")
            
            # Move to next batch
            current_end = current_start
            
            # Rate limiting: Coinbase allows 10 req/sec, we'll use 2.5 req/sec to be safe
            time.sleep(0.4)
            
            # Stop if we've reached the start time
            if current_end <= start_time:
                break
        
        # Combine all data
        if all_data:
            print("\n" + "=" * 60)
            print("Combining and cleaning data...")
            
            full_df = pd.concat(all_data, ignore_index=True)
            full_df = full_df.drop_duplicates(subset=['timestamp'])
            full_df = full_df.sort_values('timestamp')
            full_df.reset_index(drop=True, inplace=True)
            
            total_time = time.time() - start_fetch_time
            
            print(f"✅ Successfully fetched {len(full_df):,} candles in {total_time:.1f} seconds")
            print(f"Date range: {full_df.iloc[0]['timestamp']} to {full_df.iloc[-1]['timestamp']}")
            
            # Save to CSV
            # Convert granularity to minutes for filename
            interval_minutes = granularity // 60
            filename = f"{config.DATA_DIR}/eth_usd_{interval_minutes}m_{days}d.csv"
            
            # Add vwap and count columns to match Kraken format (filled with NaN)
            full_df['vwap'] = (full_df['high'] + full_df['low'] + full_df['close']) / 3  # Simple approximation
            full_df['count'] = 0  # Not provided by Coinbase
            
            full_df.to_csv(filename, index=False)
            print(f"📁 Data saved to {filename}")
            
            return full_df
        else:
            print("❌ No data fetched")
            return None

def main():
    """Main function to run data collection"""
    collector = CoinbaseDataCollector()
    
    print("=" * 60)
    print("Coinbase ETH/USD Multi-Timeframe Data Collector")
    print("=" * 60)
    
    # Define timeframes to fetch
    # Coinbase granularity: seconds, name, interval_minutes
    timeframes = [
        (3600, "1-hour", 60),
        (21600, "6-hour", 360),  # Coinbase doesn't have 4-hour, using 6-hour
        (86400, "1-day", 1440)
    ]
    
    results = {}
    
    for granularity, name, interval_min in timeframes:
        print(f"\n{'=' * 60}")
        print(f"Fetching {name} candles...")
        print(f"{'=' * 60}")
        
        df = collector.fetch_historical_data(
            days=config.LOOKBACK_DAYS, 
            granularity=granularity,
            interval_name=name
        )
        
        if df is not None:
            results[name] = df
            print(f"\n✅ {name} data collected successfully!")
        else:
            print(f"\n❌ {name} data collection failed!")
        
        # Small pause between timeframes
        if granularity != timeframes[-1][0]:
            print("\nWaiting 2 seconds before next timeframe...")
            time.sleep(2)
    
    # Print summary
    print("\n" + "=" * 60)
    print("COLLECTION SUMMARY")
    print("=" * 60)
    
    if results:
        for name, df in results.items():
            print(f"\n{name.upper()} Data:")
            print(f"  Total candles: {len(df):,}")
            print(f"  Date range: {df.iloc[0]['timestamp']} to {df.iloc[-1]['timestamp']}")
            print(f"  Price High: ${df['high'].max():.2f}")
            print(f"  Price Low: ${df['low'].min():.2f}")
            print(f"  Average: ${df['close'].mean():.2f}")
            print(f"  Total volume: {df['volume'].sum():.2f} ETH")
        
        print("\n" + "=" * 60)
        print("✅ All data collection complete! Ready for backtesting.")
        print("=" * 60)
        print("\nFiles saved in the data/ directory:")
        for granularity, name, interval_min in timeframes:
            if name in results:
                print(f"  - eth_usd_{interval_min}m_{config.LOOKBACK_DAYS}d.csv")
    else:
        print("\n❌ All data collection failed!")

if __name__ == "__main__":
    main()
