"""
News hotness scoring based on market data analysis
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from typing import Dict, Optional

from backend.data.moex_indices import MOEX_INDEX_TICKERS
from backend.services.market_data_client import MarketDataClient

logger = logging.getLogger(__name__)

@dataclass
class MarketMetrics:
    """Market metrics for hotness scoring"""
    immediate_price_change: float = 0.0
    sustained_price_change: float = 0.0  
    volume_anomaly: float = 0.0
    volatility_spike: float = 0.0
    hotness_score: float = 0.0

class HotnessScorer:
    def __init__(self):
        self.weights = {
            'immediate_price': 0.30,  # price 15min after news
            'sustained_price': 0.20,  # price 1h after news  
            'volume_anomaly': 0.35,   # volume in 15min after news
            'volatility_spike': 0.15,  # candle range after news
        }
        
    async def calculate_hotness(self, news_item: Dict, news_time: datetime) -> Optional[MarketMetrics]:
        """
        Calculate news hotness based on market data
        
        Args:
            news_item: Processed news item with tags
            news_time: News publication time
            
        Returns:
            MarketMetrics with hotness scores
        """
        try:
            # Get primary sector
            sector = self._get_primary_sector(news_item)
            if not sector:
                logger.warning(f"No sector found for news: {news_item.get('title')}")
                return None
            
            ticker = MOEX_INDEX_TICKERS.get(sector)
            if not ticker:
                logger.warning(f"No ticker found for sector: {sector}")
                return None
            
            async with MarketDataClient() as client:
                # Get baseline data (last 50 candles)
                baseline_data = await client.get_index_data(ticker, '15min', 50)
                if baseline_data is None:
                    return None
                
                # Get post-news data
                news_data = await self._get_post_news_data(client, ticker, news_time)
                if not news_data:
                    return None
                
                # Calculate metrics
                metrics = MarketMetrics()
                
                # 1. Immediate price change (15min)
                metrics.immediate_price_change = await self._calculate_price_score(
                    baseline_data, news_data, news_time, '15min'
                )
                
                # 2. Sustained price change (1h)  
                metrics.sustained_price_change = await self._calculate_price_score(
                    baseline_data, news_data, news_time, '1h'
                )
                
                # 3. Volume anomaly
                metrics.volume_anomaly = self._calculate_volume_anomaly_score(
                    baseline_data, news_data
                )
                
                # 4. Volatility spike
                metrics.volatility_spike = self._calculate_volatility_score(
                    baseline_data, news_data
                )
                
                # Calculate final score
                metrics.hotness_score = (
                    metrics.immediate_price_change * self.weights['immediate_price'] +
                    metrics.sustained_price_change * self.weights['sustained_price'] + 
                    metrics.volume_anomaly * self.weights['volume_anomaly'] +
                    metrics.volatility_spike * self.weights['volatility_spike']
                )
                
                logger.info(f"Hotness scores for {sector}: {metrics}")
                return metrics
                
        except Exception as e:
            logger.error(f"Error calculating hotness: {e}")
            return None
    
    def _get_primary_sector(self, news_item: Dict) -> Optional[str]:
        """Get primary sector from news tags"""
        tags = news_item.get('tags', [])
        if tags:
            return tags[0]  # Take first (primary) tag
        return None
    
    async def _get_post_news_data(self, client: MarketDataClient, ticker: str, 
                                news_time: datetime) -> Optional[pd.DataFrame]:
        """Get market data after news publication"""
        try:
            # Get data for 2 hours after news
            data = await client.get_index_data(ticker, '15min', 20)  # ~5 hours of data
            
            if data is not None:
                # Filter data after news
                post_news_data = data[data['begin'] >= news_time]
                return post_news_data
                
            return None
            
        except Exception as e:
            logger.error(f"Error getting post-news data: {e}")
            return None
    
    async def _calculate_price_score(self, baseline_data: pd.DataFrame, 
                                   news_data: pd.DataFrame, news_time: datetime,
                                   period: str) -> float:
        """Calculate price change score"""
        try:
            if period == '15min':
                # For 15min, take first candle after news
                if len(news_data) < 1:
                    return 0.0
                
                immediate_candle = news_data.iloc[0]
                imm_price = immediate_candle['close']
                
                # If less than 2 hours passed
                if datetime.now() < news_time + timedelta(hours=2):
                    return 0.5  # Return base score while data is incomplete
                
            elif period == '1h':
                # For 1h, take candle 1h after news
                if len(news_data) < 4:  # 4 candles * 15min = 1h
                    return 0.0
                imm_price = news_data.iloc[0]['close']
                sust_price = news_data.iloc[3]['close']  # 4th candle (1h later)
            else:
                return 0.0
            
            # Baseline prices (average before news)
            baseline_prices = baseline_data['close'].values
            if len(baseline_prices) == 0:
                return 0.0
            
            avg_baseline = np.mean(baseline_prices)
            
            if period == '15min':
                current_price = imm_price
            else:
                current_price = sust_price
            
            # Percentage change
            price_change = abs((current_price - avg_baseline) / avg_baseline)
            
            # Normalize using hyperbolic function
            k = 0.025  # At 2.5% change, score = 0.5
            score = price_change / (price_change + k)
            
            return min(score, 0.9999)
            
        except Exception as e:
            logger.error(f"Error calculating price score: {e}")
            return 0.0
    
    def _calculate_volume_anomaly_score(self, baseline_data: pd.DataFrame, 
                                      news_data: pd.DataFrame) -> float:
        """Calculate volume anomaly score"""
        try:
            if len(baseline_data) < 5 or len(news_data) < 1:
                return 0.0
            
            # Baseline volumes
            baseline_volumes = baseline_data['volume'].values
            
            # Current volume (first candle after news)
            current_volume = news_data.iloc[0]['volume']
            
            mu = np.mean(baseline_volumes)
            sigma = np.std(baseline_volumes)
            
            if sigma == 0:
                return 0.0
            
            # Z-score
            z_score = abs((current_volume - mu) / sigma)
            
            # Normalize to [0, 1) using hyperbolic function
            k = 2.0  # At z=2, score ≈ 0.5
            score = z_score / (z_score + k)
            
            return min(score, 0.9999)
            
        except Exception as e:
            logger.error(f"Error calculating volume anomaly: {e}")
            return 0.0
    
    def _calculate_volatility_score(self, baseline_data: pd.DataFrame,
                                  news_data: pd.DataFrame) -> float:
        """Calculate volatility score"""
        try:
            if len(baseline_data) < 5 or len(news_data) < 1:
                return 0.0
            
            # Baseline volatility (average candle range)
            baseline_ranges = (baseline_data['high'] - baseline_data['low']) / baseline_data['close']
            avg_baseline_range = np.mean(baseline_ranges)
            
            # Current volatility (first candle after news)
            current_candle = news_data.iloc[0]
            current_range = (current_candle['high'] - current_candle['low']) / current_candle['close']
            
            if avg_baseline_range == 0:
                return 0.0
            
            # Ratio of current to baseline volatility
            volatility_ratio = current_range / avg_baseline_range
            
            # Normalize
            k = 1.5  # At ratio 1.5, score = 0.6
            score = (volatility_ratio - 1) / ((volatility_ratio - 1) + k)
            
            return max(min(score, 0.9999), 0.0)
            
        except Exception as e:
            logger.error(f"Error calculating volatility score: {e}")
            return 0.0
