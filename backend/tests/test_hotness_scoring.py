"""
Tests for hotness scoring functionality
"""
import asyncio
import logging
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add project root to path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from backend.ai_model.hotness_scorer import HotnessScorer
from backend.data.moex_indices import MOEX_INDEX_TICKERS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_hotness_scoring():
    """Test hotness scoring for a sample news item"""
    scorer = HotnessScorer()
    
    # Use a historical date when MOEX was open (2025-10-01 14:30:00)
    news_time = datetime(2025, 10, 1, 14, 30, 0)
    
    # Test news item for Oil & Gas sector
    test_news = {
        'title': 'Газпром увеличил добычу газа на 10%',
        'text': 'Компания Газпром сообщила о рекордной добыче газа в этом квартале.',
        'source': 'Тестовый источник',
        'date': news_time.isoformat(),
        'tags': ['Нефть и газ']
    }
    
    logger.info("🧪 Testing hotness scoring...")
    logger.info(f"📰 News: {test_news['title']}")
    logger.info(f"🏷️ Sector: {test_news['tags'][0]}")
    metrics = await scorer.calculate_hotness(test_news, news_time)
    
    if metrics:
        logger.info("✅ Hotness metrics:")
        logger.info(f"   📈 Immediate price (15min): {metrics.immediate_price_change:.3f}")
        logger.info(f"   📊 Sustained price (1h): {metrics.sustained_price_change:.3f}")
        logger.info(f"   📊 Volume anomaly: {metrics.volume_anomaly:.3f}")
        logger.info(f"   📊 Volatility spike: {metrics.volatility_spike:.3f}")
        logger.info(f"   🔥 Hotness score: {metrics.hotness_score:.3f}")
        
        # Determine hotness level
        if metrics.hotness_score >= 0.7:
            level = "HIGH"
        elif metrics.hotness_score >= 0.4:
            level = "MEDIUM"
        else:
            level = "LOW"
            
        logger.info(f"   🚨 Hotness level: {level}")
    else:
        logger.error("❌ Failed to calculate hotness metrics")

async def test_all_sectors():
    """Test hotness scoring for all sectors"""
    scorer = HotnessScorer()
    
    for sector, ticker in MOEX_INDEX_TICKERS.items():
        logger.info(f"\n🔍 Testing sector: {sector} ({ticker})")
        
        test_news = {
            'title': f'Тестовая новость для сектора {sector}',
            'text': f'Тестовое содержание для сектора {sector}. Важные изменения на рынке.',
            'source': 'Тестовый источник',
            'date': (datetime.now() - timedelta(hours=2)).isoformat(),
            'tags': [sector]
        }
        
        news_time = datetime.fromisoformat(test_news['date'])
        metrics = await scorer.calculate_hotness(test_news, news_time)
        
        if metrics:
            logger.info(f"   ✅ Hotness: {metrics.hotness_score:.3f}")
        else:
            logger.info("   ❌ Data not available")

if __name__ == "__main__":
    logger.info("🚀 Starting hotness scoring tests...")
    
    # Run single test
    asyncio.run(test_hotness_scoring())
    
    # Uncomment to test all sectors (takes longer)
    # asyncio.run(test_all_sectors())
