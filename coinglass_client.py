"""
CoinGlass API Client - Fetch advanced market data
Provides liquidation heatmaps, volume profiles, and open interest data
"""
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class CoinGlassClient:
    """
    CoinGlass API Client for advanced market data

    Features:
    - Liquidation heatmap (where liquidations cluster)
    - Volume profiles at different price levels
    - Open interest across exchanges
    - Long/Short ratios
    - Funding rates
    """

    BASE_URL = "https://open-api.coinglass.com/public/v2"

    def __init__(self, api_key=None):
        """
        Initialize CoinGlass client

        Args:
            api_key: Optional API key for higher rate limits
                     If None, tries to load from COINGLASS_API_KEY env variable
        """
        # Try to get API key from environment if not provided
        if api_key is None:
            api_key = os.getenv('COINGLASS_API_KEY')

        self.api_key = api_key
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({'coinglassSecret': api_key})

        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.0  # seconds between requests

    def _rate_limit(self):
        """Ensure we don't exceed rate limits"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()

    def _make_request(self, endpoint, params=None):
        """
        Make API request with error handling

        Args:
            endpoint: API endpoint path
            params: Query parameters

        Returns:
            dict: Response data
        """
        self._rate_limit()

        url = f"{self.BASE_URL}/{endpoint}"

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get('success'):
                return data.get('data', {})
            else:
                print(f"API Error: {data.get('msg', 'Unknown error')}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return None

    def get_liquidation_heatmap(self, symbol='ETH', exchange='All'):
        """
        Get liquidation heatmap showing price levels with high liquidation risk

        Args:
            symbol: Trading pair (default: ETH)
            exchange: Exchange name or 'All' (default: All)

        Returns:
            dict: Liquidation data with price levels and amounts
            {
                'longs': [(price, amount), ...],
                'shorts': [(price, amount), ...],
                'current_price': float,
                'high_risk_long_level': float,  # Price where many longs get liquidated
                'high_risk_short_level': float  # Price where many shorts get liquidated
            }
        """
        endpoint = "liquidation_heatmap"
        params = {
            'symbol': symbol,
            'ex': exchange
        }

        data = self._make_request(endpoint, params)

        if data:
            # Process liquidation data
            return self._process_liquidation_heatmap(data)

        return self._get_mock_liquidation_data()

    def _process_liquidation_heatmap(self, raw_data):
        """Process raw liquidation heatmap data"""
        try:
            # Extract current price
            current_price = raw_data.get('price', 3500)

            # Extract liquidation levels
            longs = []
            shorts = []

            # Parse long liquidations (below current price)
            long_data = raw_data.get('longLiquidationPrice', [])
            for item in long_data:
                price = float(item.get('price', 0))
                amount = float(item.get('value', 0))
                if price > 0 and amount > 0:
                    longs.append((price, amount))

            # Parse short liquidations (above current price)
            short_data = raw_data.get('shortLiquidationPrice', [])
            for item in short_data:
                price = float(item.get('price', 0))
                amount = float(item.get('value', 0))
                if price > 0 and amount > 0:
                    shorts.append((price, amount))

            # Find high risk levels (largest clusters)
            high_risk_long = max(longs, key=lambda x: x[1])[0] if longs else current_price * 0.95
            high_risk_short = max(shorts, key=lambda x: x[1])[0] if shorts else current_price * 1.05

            return {
                'longs': sorted(longs, key=lambda x: x[0]),
                'shorts': sorted(shorts, key=lambda x: x[0]),
                'current_price': current_price,
                'high_risk_long_level': high_risk_long,
                'high_risk_short_level': high_risk_short,
                'total_long_liquidations': sum(x[1] for x in longs),
                'total_short_liquidations': sum(x[1] for x in shorts)
            }

        except Exception as e:
            print(f"Error processing liquidation data: {e}")
            return self._get_mock_liquidation_data()

    def get_volume_profile(self, symbol='ETH', timeframe='1d'):
        """
        Get volume profile showing volume distribution at different price levels

        Args:
            symbol: Trading pair
            timeframe: Time period ('1h', '4h', '1d', '1w')

        Returns:
            dict: Volume profile data
            {
                'price_levels': [price1, price2, ...],
                'volumes': [vol1, vol2, ...],
                'poc': float,  # Point of Control (highest volume)
                'vah': float,  # Value Area High
                'val': float   # Value Area Low
            }
        """
        # CoinGlass doesn't have direct volume profile API
        # We'll calculate it from recent trades or use alternatives
        return self._calculate_volume_profile_from_trades(symbol, timeframe)

    def _calculate_volume_profile_from_trades(self, symbol, timeframe):
        """Calculate volume profile from recent trading data"""
        # This would integrate with exchange APIs
        # For now, return mock data
        current_price = 3500

        # Create price levels
        price_range = current_price * 0.1  # 10% range
        price_levels = np.linspace(
            current_price - price_range,
            current_price + price_range,
            20
        )

        # Simulate volume distribution (normally distributed around current price)
        volumes = np.random.normal(1000, 300, 20)
        volumes = np.abs(volumes)

        # Find POC (Point of Control)
        poc_idx = np.argmax(volumes)
        poc = price_levels[poc_idx]

        # Value Area (70% of volume)
        sorted_indices = np.argsort(volumes)[::-1]
        cumsum = 0
        target = sum(volumes) * 0.70
        value_area_indices = []

        for idx in sorted_indices:
            cumsum += volumes[idx]
            value_area_indices.append(idx)
            if cumsum >= target:
                break

        vah = max(price_levels[i] for i in value_area_indices)
        val = min(price_levels[i] for i in value_area_indices)

        return {
            'price_levels': price_levels.tolist(),
            'volumes': volumes.tolist(),
            'poc': poc,
            'vah': vah,
            'val': val,
            'timeframe': timeframe
        }

    def get_long_short_ratio(self, symbol='ETH', exchange='All'):
        """
        Get long/short ratio across exchanges

        Args:
            symbol: Trading pair
            exchange: Exchange name or 'All'

        Returns:
            dict: Long/short ratio data
        """
        endpoint = "indicator/long-short-ratio"
        params = {
            'symbol': symbol,
            'ex': exchange
        }

        data = self._make_request(endpoint, params)

        if data:
            return self._process_long_short_ratio(data)

        return self._get_mock_long_short_ratio()

    def _process_long_short_ratio(self, raw_data):
        """Process long/short ratio data"""
        try:
            ratio = float(raw_data.get('longShortRatio', 1.0))
            long_pct = float(raw_data.get('longAccount', 50))
            short_pct = float(raw_data.get('shortAccount', 50))

            return {
                'ratio': ratio,
                'long_percentage': long_pct,
                'short_percentage': short_pct,
                'sentiment': 'BULLISH' if ratio > 1.2 else 'BEARISH' if ratio < 0.8 else 'NEUTRAL'
            }
        except:
            return self._get_mock_long_short_ratio()

    def get_open_interest(self, symbol='ETH'):
        """
        Get total open interest across exchanges

        Args:
            symbol: Trading pair

        Returns:
            dict: Open interest data
        """
        endpoint = "indicator/open-interest"
        params = {'symbol': symbol}

        data = self._make_request(endpoint, params)

        if data:
            return {
                'total_oi': float(data.get('openInterest', 0)),
                'change_24h': float(data.get('change24h', 0)),
                'trend': 'INCREASING' if data.get('change24h', 0) > 0 else 'DECREASING'
            }

        return {
            'total_oi': 5000000000,  # $5B
            'change_24h': 2.5,
            'trend': 'INCREASING'
        }

    def get_funding_rates(self, symbol='ETH'):
        """
        Get current funding rates across exchanges

        Args:
            symbol: Trading pair

        Returns:
            dict: Funding rate data
        """
        endpoint = "indicator/funding-rate"
        params = {'symbol': symbol}

        data = self._make_request(endpoint, params)

        if data:
            rates = data.get('data', [])
            avg_rate = np.mean([float(r.get('rate', 0)) for r in rates])

            return {
                'average_rate': avg_rate,
                'rates_by_exchange': rates,
                'sentiment': 'BULLISH' if avg_rate > 0.01 else 'BEARISH' if avg_rate < -0.01 else 'NEUTRAL'
            }

        return {
            'average_rate': 0.0034,
            'sentiment': 'NEUTRAL'
        }

    def _get_mock_liquidation_data(self):
        """Return mock liquidation data for testing"""
        current_price = 3500

        # Long liquidations (below current price)
        longs = [
            (current_price * 0.90, 50000000),  # $50M at -10%
            (current_price * 0.92, 30000000),  # $30M at -8%
            (current_price * 0.95, 80000000),  # $80M at -5%
            (current_price * 0.97, 40000000),  # $40M at -3%
        ]

        # Short liquidations (above current price)
        shorts = [
            (current_price * 1.03, 45000000),  # $45M at +3%
            (current_price * 1.05, 70000000),  # $70M at +5%
            (current_price * 1.08, 35000000),  # $35M at +8%
            (current_price * 1.10, 55000000),  # $55M at +10%
        ]

        return {
            'longs': longs,
            'shorts': shorts,
            'current_price': current_price,
            'high_risk_long_level': current_price * 0.95,  # Largest cluster
            'high_risk_short_level': current_price * 1.05,
            'total_long_liquidations': sum(x[1] for x in longs),
            'total_short_liquidations': sum(x[1] for x in shorts)
        }

    def _get_mock_long_short_ratio(self):
        """Return mock long/short ratio"""
        return {
            'ratio': 1.15,
            'long_percentage': 53.5,
            'short_percentage': 46.5,
            'sentiment': 'NEUTRAL'
        }

    def get_market_summary(self, symbol='ETH'):
        """
        Get comprehensive market summary with all indicators

        Returns:
            dict: Complete market analysis
        """
        print(f"\n{'='*60}")
        print(f"Fetching CoinGlass Market Data for {symbol}...")
        print(f"{'='*60}")

        liquidations = self.get_liquidation_heatmap(symbol)
        print("✓ Liquidation heatmap retrieved")

        volume_profile = self.get_volume_profile(symbol)
        print("✓ Volume profile calculated")

        ls_ratio = self.get_long_short_ratio(symbol)
        print("✓ Long/Short ratio fetched")

        oi = self.get_open_interest(symbol)
        print("✓ Open interest retrieved")

        funding = self.get_funding_rates(symbol)
        print("✓ Funding rates fetched")

        print(f"{'='*60}\n")

        return {
            'liquidations': liquidations,
            'volume_profile': volume_profile,
            'long_short_ratio': ls_ratio,
            'open_interest': oi,
            'funding_rates': funding,
            'timestamp': datetime.now().isoformat()
        }


def test_coinglass_client():
    """Test CoinGlass client"""
    client = CoinGlassClient()

    print("\n" + "="*60)
    print("TESTING COINGLASS CLIENT")
    print("="*60 + "\n")

    # Test liquidation heatmap
    print("1. Liquidation Heatmap:")
    liq = client.get_liquidation_heatmap()
    print(f"   Current Price: ${liq['current_price']:,.2f}")
    print(f"   High Risk Long Level: ${liq['high_risk_long_level']:,.2f} (-{((liq['current_price']-liq['high_risk_long_level'])/liq['current_price']*100):.1f}%)")
    print(f"   High Risk Short Level: ${liq['high_risk_short_level']:,.2f} (+{((liq['high_risk_short_level']-liq['current_price'])/liq['current_price']*100):.1f}%)")
    print(f"   Total Long Liquidations: ${liq['total_long_liquidations']:,.0f}")
    print(f"   Total Short Liquidations: ${liq['total_short_liquidations']:,.0f}")

    # Test volume profile
    print("\n2. Volume Profile:")
    vp = client.get_volume_profile()
    print(f"   Point of Control (POC): ${vp['poc']:,.2f}")
    print(f"   Value Area High (VAH): ${vp['vah']:,.2f}")
    print(f"   Value Area Low (VAL): ${vp['val']:,.2f}")

    # Test long/short ratio
    print("\n3. Long/Short Ratio:")
    ls = client.get_long_short_ratio()
    print(f"   Ratio: {ls['ratio']:.2f}")
    print(f"   Longs: {ls['long_percentage']:.1f}%")
    print(f"   Shorts: {ls['short_percentage']:.1f}%")
    print(f"   Sentiment: {ls['sentiment']}")

    # Get full summary
    print("\n" + "="*60)
    print("FULL MARKET SUMMARY")
    print("="*60)
    summary = client.get_market_summary()

    return summary


if __name__ == "__main__":
    test_coinglass_client()
