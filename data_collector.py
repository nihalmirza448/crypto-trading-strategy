"""
Data collector for fetching historical Ethereum data from Kraken
"""
import requests
import pandas as pd
import time
from datetime import datetime, timedelta
import json
import config

class KrakenDataCollector:
    def __init__(self):
        self.base_url = config.KRAKEN_REST_URL
        
    def get_ohlc_data(self, pair='ETHUSD', interval=1, since=None):
        """
        Fetch OHLC data from Kraken
        
        Args:
            pair: Trading pair (default: ETHUSD)
            interval: Timeframe in minutes (1, 5, 15, 30, 60, etc.)
            since: Unix timestamp to fetch data from
        """
        endpoint = f"{self.base_url}/0/public/OHLC"
        params = {
            'pair': pair,
            'interval': interval
        }
        
        if since:
            params['since'] = since
            
        try:
            response = requests.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data['error']:
                print(f"Kraken API Error: {data['error']}")
                return None, None
                
            # Extract OHLC data
            pair_key = list(data['result'].keys())[0]  # Get the pair key
            ohlc_data = data['result'][pair_key]
            
            # Convert to DataFrame
            df = pd.DataFrame(ohlc_data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 
                'vwap', 'volume', 'count'
            ])
            
            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
            
            # Convert price columns to float
            for col in ['open', 'high', 'low', 'close', 'vwap', 'volume']:
                df[col] = df[col].astype(float)
                
            return df, data['result']['last']
            
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            return None, None
        except Exception as e:
            print(f"Error fetching data: {e}")
            return None, None
    
    def fetch_historical_data(self, days=120, interval=1):
        """
        Fetch complete historical data for specified number of days
        
        Args:
            days: Number of days to fetch
            interval: Timeframe in minutes
        """
        print(f"Fetching {days} days of {interval}-minute ETH/USD data from Kraken...")
        
        # Calculate start timestamp
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        since = int(start_time.timestamp())
        
        # Estimate total requests needed (Kraken returns ~720 candles per request)
        total_candles_needed = days * 24 * 60 // interval
        estimated_requests = total_candles_needed // 720 + 1
        estimated_time_minutes = (estimated_requests * 3.5) / 60
        
        print(f"Estimated {estimated_requests} API requests needed")
        print(f"Estimated time: {estimated_time_minutes:.1f} minutes")
        print(f"Rate limit: ~17 requests/minute (safe for Kraken's limits)")
        print("=" * 60)
        
        all_data = []
        request_count = 0
        retry_count = 0
        max_retries = 5
        start_fetch_time = time.time()
        
        while True:
            result = self.get_ohlc_data(
                pair='ETHUSD',
                interval=interval,
                since=since
            )
            
            # Handle None return (API error with exponential backoff)
            if result is None or result[0] is None:
                retry_count += 1
                if retry_count > max_retries:
                    print(f"\n❌ Failed after {max_retries} retries. Kraken may be rate limiting.")
                    print("Try again in 5-10 minutes or reduce LOOKBACK_DAYS in config.py")
                    break
                
                # Exponential backoff: 5s, 10s, 20s, 40s, 60s
                retry_wait = min(5 * (2 ** (retry_count - 1)), 60)
                print(f"⚠️  API error (retry {retry_count}/{max_retries}). Waiting {retry_wait}s...")
                time.sleep(retry_wait)
                continue
            
            # Reset retry counter on success
            retry_count = 0
            
            df, last_timestamp = result
            
            if df.empty:
                break
                
            all_data.append(df)
            request_count += 1
            
            # Progress reporting
            if request_count % 10 == 0:
                elapsed = (time.time() - start_fetch_time) / 60
                progress_pct = (request_count / estimated_requests) * 100
                eta_minutes = (elapsed / request_count) * (estimated_requests - request_count)
                print(f"Progress: {request_count}/{estimated_requests} requests ({progress_pct:.1f}%) | "
                      f"Latest: {df.iloc[-1]['timestamp']} | ETA: {eta_minutes:.1f}m")
            
            # Check if we've reached the end
            if int(last_timestamp) >= int(end_time.timestamp()):
                break
                
            since = last_timestamp
            
            # Rate limiting: 3.5 seconds = ~17 requests/minute (safely within Kraken's 15-20 limit)
            time.sleep(3.5)
        
        # Combine all data
        if all_data:
            print("\n" + "=" * 60)
            print("Combining and cleaning data...")
            
            full_df = pd.concat(all_data, ignore_index=True)
            full_df = full_df.drop_duplicates(subset=['timestamp'])
            full_df = full_df.sort_values('timestamp')
            full_df.reset_index(drop=True, inplace=True)
            
            total_time = (time.time() - start_fetch_time) / 60
            
            print(f"✅ Successfully fetched {len(full_df):,} candles in {total_time:.1f} minutes")
            print(f"Date range: {full_df.iloc[0]['timestamp']} to {full_df.iloc[-1]['timestamp']}")
            
            # Save to CSV
            filename = f"{config.DATA_DIR}/eth_usd_{interval}m_{days}d.csv"
            full_df.to_csv(filename, index=False)
            print(f"📁 Data saved to {filename}")
            
            return full_df
        else:
            print("❌ No data fetched")
            return None
    
    def get_recent_trades(self, pair='ETHUSD', since=None):
        """Fetch recent trades for volume analysis"""
        endpoint = f"{self.base_url}/0/public/Trades"
        params = {'pair': pair}
        
        if since:
            params['since'] = since
            
        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data['error']:
                print(f"Error: {data['error']}")
                return None
                
            return data['result']
        except Exception as e:
            print(f"Error fetching trades: {e}")
            return None

def main():
    """Main function to run data collection"""
    collector = KrakenDataCollector()
    
    print("=" * 60)
    print("Kraken ETH/USD Multi-Timeframe Data Collector")
    print("=" * 60)
    
    # Define timeframes to fetch (in minutes)
    timeframes = [
        (60, "1-hour"),
        (240, "4-hour"),
        (1440, "1-day")
    ]
    
    results = {}
    
    for interval, name in timeframes:
        print(f"\n{'=' * 60}")
        print(f"Fetching {name} candles...")
        print(f"{'=' * 60}")
        
        df = collector.fetch_historical_data(days=config.LOOKBACK_DAYS, interval=interval)
        
        if df is not None:
            results[name] = df
            print(f"\n✅ {name} data collected successfully!")
        else:
            print(f"\n❌ {name} data collection failed!")
        
        # Add a small pause between different timeframes
        if interval != timeframes[-1][0]:  # Don't wait after the last one
            print("\nWaiting 5 seconds before next timeframe...")
            time.sleep(5)
    
    # Print summary of all collected data
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
        for interval, name in timeframes:
            if name in results:
                print(f"  - eth_usd_{interval}m_{config.LOOKBACK_DAYS}d.csv")
    else:
        print("\n❌ All data collection failed!")

if __name__ == "__main__":
    main()
