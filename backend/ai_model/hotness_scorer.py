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
            logger.info(f"🔍 Starting hotness calculation for news: {news_item.get('title')}")
            
            # Get primary sector
            sector = self._get_primary_sector(news_item)
            if not sector:
                logger.warning(f"No sector found for news: {news_item.get('title')}")
                return None
            logger.info(f"📊 Found sector: {sector}")
            
            ticker = MOEX_INDEX_TICKERS.get(sector)
            if not ticker:
                logger.warning(f"No ticker found for sector: {sector}")
                return None
            logger.info(f"📈 Using ticker: {ticker}")
            
            async with MarketDataClient() as client:
                logger.info("🔧 Fetching baseline data...")
                # Get baseline data (last 50 candles)
                baseline_data = await client.get_index_data(ticker, '15min', 50)
                if baseline_data is None:
                    logger.warning("No baseline data returned")
                    return None
                logger.info(f"📊 Got baseline data with {len(baseline_data)} rows")
                
                # Get post-news data
                logger.info("🔧 Fetching post-news data...")
                news_data = await self._get_post_news_data(client, ticker, news_time)
                if news_data is None or news_data.empty:
                    logger.warning("No post-news data returned")
                    return None
                logger.info(f"📈 Got post-news data with {len(news_data)} rows")
                
                # Calculate metrics
                metrics = MarketMetrics()
                
                try:
                    # 1. Immediate price change (15min)
                    logger.info("📉 Calculating immediate price change...")
                    metrics.immediate_price_change = await self._calculate_price_score(
                        baseline_data, news_data, news_time, '15min'
                    )
                    logger.info(f"   Immediate price change: {metrics.immediate_price_change:.4f}")
                    
                    # 2. Sustained price change (1h)  
                    logger.info("📈 Calculating sustained price change...")
                    metrics.sustained_price_change = await self._calculate_price_score(
                        baseline_data, news_data, news_time, '1h'
                    )
                    logger.info(f"   Sustained price change: {metrics.sustained_price_change:.4f}")
                    
                    # 3. Volume anomaly
                    logger.info("📊 Calculating volume anomaly...")
                    metrics.volume_anomaly = self._calculate_volume_anomaly_score(
                        baseline_data, news_data
                    )
                    logger.info(f"   Volume anomaly: {metrics.volume_anomaly:.4f}")
                    
                    # 4. Volatility spike
                    logger.info("⚡ Calculating volatility spike...")
                    metrics.volatility_spike = self._calculate_volatility_score(
                        baseline_data, news_data
                    )
                    logger.info(f"   Volatility spike: {metrics.volatility_spike:.4f}")
                    
                    # Calculate final score
                    metrics.hotness_score = (
                        metrics.immediate_price_change * self.weights['immediate_price'] +
                        metrics.sustained_price_change * self.weights['sustained_price'] + 
                        metrics.volume_anomaly * self.weights['volume_anomaly'] +
                        metrics.volatility_spike * self.weights['volatility_spike']
                    )
                    
                    logger.info(f"🎯 Final hotness score for {sector}: {metrics.hotness_score:.4f}")
                    return metrics
                    
                except Exception as e:
                    logger.error(f"Error in metric calculation: {e}", exc_info=True)
                    return None
                
        except Exception as e:
            logger.error(f"Error in calculate_hotness: {str(e)}\n{type(e).__name__}", exc_info=True)
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
            logger.debug(f"🔍 Fetching post-news data for {ticker} after {news_time}")
            
            # Get data for 2 hours after news
            data = await client.get_index_data(ticker, '15min', 20)  # ~5 hours of data
            
            if data is None:
                logger.warning(f"❌ No data returned for ticker: {ticker}")
                return None
                
            if not isinstance(data, pd.DataFrame):
                logger.error(f"❌ Expected DataFrame, got {type(data)} for ticker: {ticker}")
                return None
                
            if data.empty:
                logger.warning(f"⚠️ Empty DataFrame returned for ticker: {ticker}")
                return None
                
            logger.debug(f"📊 Raw data columns: {data.columns.tolist()}")
            logger.debug(f"📅 Data time range: {data['begin'].min()} to {data['begin'].max()}" if 'begin' in data.columns else "❌ No 'begin' column found")
            
            if 'begin' not in data.columns:
                logger.error(f"❌ Missing 'begin' column in market data for {ticker}")
                logger.error(f"Available columns: {data.columns.tolist()}")
                return None
            
            try:
                # Ensure 'begin' is datetime
                data['begin'] = pd.to_datetime(data['begin'])
                
                # Log the time range we're working with
                news_timestamp = pd.Timestamp(news_time)
                logger.debug(f"🕒 News time: {news_timestamp}")
                logger.debug(f"📅 Data range: {data['begin'].min()} to {data['begin'].max()}")
                
                # Create a mask for filtering
                mask = data['begin'] >= news_timestamp
                
                if not mask.any():
                    logger.warning(f"⚠️ No data points after news time: {news_time}")
                    logger.debug(f"Earliest data point: {data['begin'].min()}")
                    return None
                
                # Apply the mask to get post-news data
                post_news_data = data.loc[mask].copy()
                
                if post_news_data.empty:
                    logger.warning(f"⚠️ Filtered DataFrame is empty for ticker: {ticker}")
                    return None
                
                logger.debug(f"✅ Found {len(post_news_data)} data points after news time")
                logger.debug(f"📅 Post-news data range: {post_news_data['begin'].min()} to {post_news_data['begin'].max()}")
                
                return post_news_data
                
            except Exception as e:
                logger.error(f"❌ Error processing market data for {ticker}: {e}", exc_info=True)
                logger.debug(f"Data types: {data.dtypes}")
                logger.debug(f"Sample data: {data.head().to_dict()}")
                return None
            
        except Exception as e:
            logger.error(f"❌ Error getting post-news data for {ticker}: {e}", exc_info=True)
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
            # Check if we have enough data
            if baseline_data.empty or news_data.empty or len(baseline_data) < 5 or len(news_data) < 1:
                return 0.0
            
            # Ensure we're working with numeric values
            baseline_high = pd.to_numeric(baseline_data['high'], errors='coerce').values
            baseline_low = pd.to_numeric(baseline_data['low'], errors='coerce').values
            baseline_close = pd.to_numeric(baseline_data['close'], errors='coerce').values
            
            # Filter out any NaN or inf values
            valid_mask = ~(np.isnan(baseline_high) | np.isnan(baseline_low) | np.isnan(baseline_close) |
                         np.isinf(baseline_high) | np.isinf(baseline_low) | (baseline_close == 0))
            
            if not np.any(valid_mask):
                return 0.0
                
            baseline_high = baseline_high[valid_mask]
            baseline_low = baseline_low[valid_mask]
            baseline_close = baseline_close[valid_mask]
            
            # Calculate baseline ranges
            baseline_ranges = (baseline_high - baseline_low) / baseline_close
            avg_baseline_range = np.mean(baseline_ranges)
            
            if np.isnan(avg_baseline_range) or avg_baseline_range <= 0:
                return 0.0
            
            # Get current candle data
            current_candle = news_data.iloc[0]
            try:
                current_high = float(current_candle['high'])
                current_low = float(current_candle['low'])
                current_close = float(current_candle['close'])
                
                if current_close <= 0:
                    return 0.0
                    
                current_range = (current_high - current_low) / current_close
                
                # Ratio of current to baseline volatility
                volatility_ratio = current_range / avg_baseline_range
                
                # Normalize using a sigmoid-like function
                k = 1.5  # At ratio 1.5, score = 0.6
                score = (volatility_ratio - 1) / ((volatility_ratio - 1) + k)
                
                # Ensure score is within [0, 0.9999] range
                return float(np.clip(score, 0.0, 0.9999))
                
            except (ValueError, TypeError, KeyError) as e:
                logger.error(f"Error processing current candle data: {e}")
                return 0.0
            
        except Exception as e:
            logger.error(f"Error in _calculate_volatility_score: {e}", exc_info=True)
            return 0.0
