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
            DataFrame with columns: [open, high, low, close, volume]
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
                    candles = data['candles']['data']
                    
                    if not candles:
                        return None
                    
                    df = pd.DataFrame(candles, columns=[
                        'open', 'close', 'high', 'low', 'value', 'volume',
                        'begin', 'end', 'ticker'
                    ])
                    
                    # Convert timestamps
                    df['begin'] = pd.to_datetime(df['begin'])
                    df['end'] = pd.to_datetime(df['end'])
                    
                    return df[['begin', 'end', 'open', 'high', 'low', 'close', 'volume']]
                else:
                    logger.error(f"HTTP error {response.status} for {ticker}")
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
