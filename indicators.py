"""
Technical indicators for momentum and volatility detection
"""
import pandas as pd
import numpy as np
import config  # Import config for SMA_PERIODS

class TechnicalIndicators:
    """Calculate technical indicators for trading signals"""
    
    @staticmethod
    def calculate_rsi(df, period=14):
        """Calculate Relative Strength Index"""
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def calculate_macd(df, fast=12, slow=26, signal=9):
        """Calculate MACD indicator"""
        exp1 = df['close'].ewm(span=fast, adjust=False).mean()
        exp2 = df['close'].ewm(span=slow, adjust=False).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        histogram = macd - signal_line
        
        return macd, signal_line, histogram
    
    @staticmethod
    def calculate_bollinger_bands(df, period=20, std_dev=2):
        """Calculate Bollinger Bands"""
        sma = df['close'].rolling(window=period).mean()
        std = df['close'].rolling(window=period).std()
        
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        bandwidth = (upper_band - lower_band) / sma
        
        return upper_band, sma, lower_band, bandwidth
    
    @staticmethod
    def calculate_atr(df, period=14):
        """Calculate Average True Range for volatility"""
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        atr = true_range.rolling(window=period).mean()
        
        return atr
    
    @staticmethod
    def calculate_momentum(df, period=1):
        """Calculate price momentum over period (in hours for hourly data)"""
        return df['close'].pct_change(period) * 100
    
    @staticmethod
    def calculate_sma(df, period=30):
        """Calculate Simple Moving Average"""
        return df['close'].rolling(window=period).mean()
    
    @staticmethod
    def calculate_volume_profile(df, period=20):
        """Calculate volume statistics"""
        volume_ma = df['volume'].rolling(window=period).mean()
        volume_std = df['volume'].rolling(window=period).std()
        volume_spike = df['volume'] / volume_ma
        
        return volume_ma, volume_std, volume_spike
    
    @staticmethod
    def detect_rapid_movement(df, period=1, threshold=3.0):
        """
        Detect significant price movements (for hourly data)
        
        Args:
            period: Number of candles to measure movement
            threshold: Minimum % change to qualify as significant
        """
        price_change = df['close'].pct_change(period) * 100
        is_rapid = abs(price_change) >= threshold
        direction = np.sign(price_change)
        
        return is_rapid, direction, price_change
    
    @staticmethod
    def calculate_volatility_regime(df, short_period=20, long_period=100):
        """
        Determine if market is in high or low volatility regime
        """
        short_volatility = df['close'].pct_change().rolling(window=short_period).std() * 100
        long_volatility = df['close'].pct_change().rolling(window=long_period).std() * 100
        
        volatility_ratio = short_volatility / long_volatility
        
        return short_volatility, long_volatility, volatility_ratio
    
    @staticmethod
    def add_all_indicators(df, timeframe='1h'):
        """
        Add all indicators for precision trading
        Includes trending regime detection and breakout filters
        """
        # RSI - 14 period and 30 period
        df['rsi'] = TechnicalIndicators.calculate_rsi(df, period=14)
        df['rsi_14'] = df['rsi']  # Alias for clarity
        df['rsi_30'] = TechnicalIndicators.calculate_rsi(df, period=30)
        
        # MACD (optional)
        macd, signal, histogram = TechnicalIndicators.calculate_macd(df)
        df['macd'] = macd
        df['macd_signal'] = signal
        df['macd_histogram'] = histogram
        
        # Bollinger Bands
        upper, middle, lower, bandwidth = TechnicalIndicators.calculate_bollinger_bands(df, period=20)
        df['bb_upper'] = upper
        df['bb_middle'] = middle
        df['bb_lower'] = lower
        df['bb_bandwidth'] = bandwidth
        
        # ATR
        df['atr'] = TechnicalIndicators.calculate_atr(df, period=14)
        
        # SMAs - Use config periods or defaults
        sma_periods = getattr(config, 'SMA_PERIODS', [60, 90, 180])
        df['sma_60'] = TechnicalIndicators.calculate_sma(df, period=sma_periods[0])
        df['sma_90'] = TechnicalIndicators.calculate_sma(df, period=sma_periods[1])
        df['sma_180'] = TechnicalIndicators.calculate_sma(df, period=sma_periods[2])
        
        # 100 SMA for market regime detection (changed from 200)
        df['sma_100'] = TechnicalIndicators.calculate_sma(df, period=100)
        df['sma_200'] = TechnicalIndicators.calculate_sma(df, period=200)  # Keep for compatibility
        
        # Momentum
        df['momentum_1h'] = TechnicalIndicators.calculate_momentum(df, period=1)
        df['momentum_4h'] = TechnicalIndicators.calculate_momentum(df, period=4)
        df['momentum_24h'] = TechnicalIndicators.calculate_momentum(df, period=24)
        
        # Volume
        volume_ma, volume_std, volume_spike = TechnicalIndicators.calculate_volume_profile(df, period=20)
        df['volume_ma'] = volume_ma
        df['volume_std'] = volume_std
        df['volume_spike'] = volume_spike
        
        # PRECISION FILTER: Trending regime detection
        df['rolling_volatility'] = df['close'].pct_change().rolling(window=6).std() * 100
        volatility_threshold = df['rolling_volatility'].quantile(0.60)
        df['is_trending'] = df['rolling_volatility'] > volatility_threshold
        df['is_consolidating'] = df['rolling_volatility'] < df['rolling_volatility'].quantile(0.40)
        
        # MARKET REGIME: Bull vs Bear based on 200 SMA
        df['market_regime'] = 'neutral'
        df.loc[df['close'] > df['sma_200'], 'market_regime'] = 'bull'
        df.loc[df['close'] < df['sma_200'], 'market_regime'] = 'bear'
        
        # PULLBACK DETECTION: Distance from SMA60 and SMA90
        df['distance_from_sma60_pct'] = ((df['close'] - df['sma_60']) / df['sma_60']) * 100
        df['distance_from_sma90_pct'] = ((df['close'] - df['sma_90']) / df['sma_90']) * 100
        
        # BOUNCE DETECTION: Price recovering from recent low
        df['low_3h'] = df['low'].rolling(window=3).min()
        df['bounce_from_low_pct'] = ((df['close'] - df['low_3h']) / df['low_3h']) * 100
        
        # LOWER HIGHS DETECTION (for bear market shorts)
        df['high_24h'] = df['high'].rolling(window=24).max()
        df['high_24h_prev'] = df['high_24h'].shift(24)
        df['is_lower_high'] = df['high_24h'] < df['high_24h_prev']
        
        # 24h low for reference
        df['low_24h'] = df['low'].rolling(window=24).min()
        
        # Rapid movement detection
        is_rapid, direction, change = TechnicalIndicators.detect_rapid_movement(df, period=1, threshold=1.0)
        df['is_rapid_move'] = is_rapid
        df['move_direction'] = direction
        df['price_change_1h'] = change
        
        # Volatility regime
        short_vol, long_vol, vol_ratio = TechnicalIndicators.calculate_volatility_regime(df, short_period=20, long_period=100)
        df['volatility_short'] = short_vol
        df['volatility_long'] = long_vol
        df['volatility_ratio'] = vol_ratio
        
        return df

def test_indicators():
    """Test function to verify indicators work correctly"""
    # Create sample data
    dates = pd.date_range(start='2024-01-01', periods=1000, freq='1min')
    np.random.seed(42)
    
    # Generate random walk price data
    returns = np.random.randn(1000) * 0.001
    price = 2000 * (1 + returns).cumprod()
    
    df = pd.DataFrame({
        'timestamp': dates,
        'open': price * (1 + np.random.randn(1000) * 0.0005),
        'high': price * (1 + abs(np.random.randn(1000)) * 0.001),
        'low': price * (1 - abs(np.random.randn(1000)) * 0.001),
        'close': price,
        'volume': np.random.randint(100, 1000, 1000).astype(float)
    })
    
    # Add indicators
    df = TechnicalIndicators.add_all_indicators(df)
    
    print("Indicator Test Results:")
    print("=" * 60)
    print(df[['timestamp', 'close', 'rsi', 'macd', 'bb_bandwidth', 
              'momentum_5m', 'volume_spike']].tail(10))
    print("\nIndicators calculated successfully!")

if __name__ == "__main__":
    test_indicators()
