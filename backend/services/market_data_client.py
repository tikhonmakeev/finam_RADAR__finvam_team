"""
Client for fetching market data from MOEX
"""
import aiohttp
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Optional, Dict, Any
import json

logger = logging.getLogger(__name__)

class MarketDataClient:
    def __init__(self):
        self.base_url = "https://iss.moex.com/iss"
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_index_data(self, ticker: str, timeframe: str = '15min', 
                           limit: int = 50) -> Optional[pd.DataFrame]:
        """
        Get historical data for an index
        
        Args:
            ticker: Index ticker (MOEXIT, MOEXOG, etc.)
            timeframe: Bar interval (1min, 10min, 15min, 1h, D)
            limit: Number of bars to return
            
        Returns:
            DataFrame with columns: [begin, end, open, high, low, close, volume]
        """
        try:
            url = f"{self.base_url}/engines/stock/markets/index/boards/SNDX/securities/{ticker}/candles.json"
            
            params = {
                'interval': self._convert_timeframe(timeframe),
                'limit': limit,
                'from': (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Check if we have the expected data structure
                    if 'candles' not in data or 'data' not in data['candles']:
                        logger.error(f"Unexpected response format for {ticker}")
                        return None
                        
                    candles = data['candles']['data']
                    
                    if not candles:
                        logger.warning(f"No data returned for {ticker}")
                        return None
                    
                    # Get column names from the response
                    columns = data['candles'].get('columns', [
                        'open', 'close', 'high', 'low', 'value', 'volume',
                        'begin', 'end'
                    ])
                    
                    # Create DataFrame with available columns
                    df = pd.DataFrame(candles, columns=columns)
                    
                    # Ensure we have the required columns
                    required_columns = ['begin', 'end', 'open', 'high', 'low', 'close', 'volume']
                    for col in required_columns:
                        if col not in df.columns:
                            logger.error(f"Missing required column in response: {col}")
                            return None
                    
                    # Convert timestamps
                    df['begin'] = pd.to_datetime(df['begin'])
                    df['end'] = pd.to_datetime(df['end'])
                    
                    # Ensure numeric columns are of correct type
                    numeric_cols = ['open', 'high', 'low', 'close', 'volume']
                    for col in numeric_cols:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                    
                    return df[required_columns]
                else:
                    error_text = await response.text()
                    logger.error(f"HTTP error {response.status} for {ticker}: {error_text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {e}")
            return None
    
    def _convert_timeframe(self, timeframe: str) -> int:
        """Convert timeframe to MOEX format"""
        tf_mapping = {
            '1min': 1,
            '10min': 10, 
            '15min': 60,  # MOEX uses 60 for 15min
            '1h': 4,
            'D': 24
        }
        return tf_mapping.get(timeframe, 60)

    async def get_hashtag_stats(self, hashtag: str, news_date: datetime) -> Dict[str, Dict]:
        """
        Get search statistics for a hashtag around news date
        
        Args:
            hashtag: The hashtag to search for (without #)
            news_date: The date of the news article
            
        Returns:
            Dictionary with 'before' and 'after' periods data
            {
                'before': {date_str: count, ...},  # 30 days before news
                'after': {date_str: count, ...}    # News day + next day
            }
        """
        try:
            # Calculate date ranges
            end_date = news_date + timedelta(days=1)  # Include next day
            start_date = news_date - timedelta(days=30)
            
            # Format dates for API
            date_format = '%Y-%m-%d'
            params = {
                'hashtag': hashtag,
                'start_date': start_date.strftime(date_format),
                'end_date': end_date.strftime(date_format)
            }
            
            # This is a placeholder - you'll need to implement the actual API call
            # to your search analytics service
            async with self.session.get(
                "https://api.yoursearchservice.com/v1/hashtag/stats",
                params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Process the data into before/after periods
                    result = {'before': {}, 'after': {}}
                    
                    for date_str, count in data.get('daily_stats', {}).items():
                        current_date = datetime.strptime(date_str, date_format).date()
                        
                        if current_date < news_date.date():
                            result['before'][date_str] = count
                        elif current_date <= end_date.date():
                            result['after'][date_str] = count
                    
                    return result
                else:
                    logger.error(f"Error fetching hashtag stats: {response.status}")
                    return {'before': {}, 'after': {}}
                    
        except Exception as e:
            logger.error(f"Error in get_hashtag_stats: {e}")
            return {'before': {}, 'after': {}}
    
    async def get_hashtag_analysis(self, hashtag: str, news_date: datetime) -> Dict[str, Any]:
        """
        Analyze hashtag search volume around news date
        
        Args:
            hashtag: The hashtag to analyze (without #)
            news_date: The date of the news article
            
        Returns:
            Dictionary with analysis results:
            {
                'before_stats': {
                    'total_searches': int,
                    'avg_daily': float,
                    'max_daily': int,
                    'max_date': str
                },
                'after_stats': {
                    'total_searches': int,
                    'avg_daily': float,
                    'max_daily': int,
                    'max_date': str
                },
                'impact_multiplier': float  # After searches / Before average
            }
        """
        stats = await self.get_hashtag_stats(hashtag, news_date)
        
        def calculate_stats(period_data: Dict[str, int]) -> Dict[str, Any]:
            if not period_data:
                return {
                    'total_searches': 0,
                    'avg_daily': 0.0,
                    'max_daily': 0,
                    'max_date': None
                }
                
            values = list(period_data.values())
            max_idx = max(range(len(values)), key=values.__getitem__)
            max_date = list(period_data.keys())[max_idx]
            
            return {
                'total_searches': sum(values),
                'avg_daily': sum(values) / len(values) if values else 0,
                'max_daily': max(values) if values else 0,
                'max_date': max_date
            }
        
        before_stats = calculate_stats(stats['before'])
        after_stats = calculate_stats(stats['after'])
        
        # Calculate impact multiplier (avoid division by zero)
        before_avg = before_stats['avg_daily'] or 1  # Avoid division by zero
        impact_multiplier = (after_stats['avg_daily'] / before_avg) if before_avg > 0 else 0
        
        return {
            'before_stats': before_stats,
            'after_stats': after_stats,
            'impact_multiplier': round(impact_multiplier, 2)
        }
        
    async def get_current_price(self, ticker: str) -> Optional[float]:
        """Get current index price"""
        try:
            url = f"{self.base_url}/engines/stock/markets/index/boards/SNDX/securities/{ticker}.json"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    market_data = data['marketdata']['data']
                    if market_data:
                        return market_data[0][12]  # LAST price
                return None
                
        except Exception as e:
            logger.error(f"Error fetching current price for {ticker}: {e}")
            return None
