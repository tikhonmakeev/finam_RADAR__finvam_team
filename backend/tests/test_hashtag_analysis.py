"""
Test script for hashtag analysis functionality
"""
import asyncio
from datetime import datetime, timedelta
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.market_data_client import MarketDataClient

# Load environment variables
load_dotenv()

async def test_hashtag_analysis():
    """Test the hashtag analysis functionality"""
    print("🔍 Testing hashtag analysis...")
    
    # Create a news date (use yesterday as the news date for testing)
    news_date = datetime.now() - timedelta(days=1)
    hashtag = "test_hashtag"  # Replace with a real hashtag for testing
    
    async with MarketDataClient() as client:
        # Test with a mock implementation (since we don't have a real API yet)
        print(f"📅 Analyzing hashtag: #{hashtag} around news date: {news_date.strftime('%Y-%m-%d')}")
        
        # Get the analysis
        analysis = await client.get_hashtag_analysis(hashtag, news_date)
        
        # Print the results
        print("\n📊 Analysis Results:")
        print("-" * 50)
        
        # Before stats
        print("📈 Before News (30 days):")
        print(f"  • Total searches: {analysis['before_stats']['total_searches']}")
        print(f"  • Average daily: {analysis['before_stats']['avg_daily']:.2f}")
        print(f"  • Max daily: {analysis['before_stats']['max_daily']} (on {analysis['before_stats']['max_date'] or 'N/A'})")
        
        # After stats
        print("\n📉 After News (2 days):")
        print(f"  • Total searches: {analysis['after_stats']['total_searches']}")
        print(f"  • Average daily: {analysis['after_stats']['avg_daily']:.2f}")
        print(f"  • Max daily: {analysis['after_stats']['max_daily']} (on {analysis['after_stats']['max_date'] or 'N/A'})")
        
        # Impact
        print(f"\n🚀 Impact Multiplier: {analysis['impact_multiplier']:.2f}x")
        
        # Interpretation
        if analysis['impact_multiplier'] > 5:
            print("💥 Significant impact detected!")
        elif analysis['impact_multiplier'] > 2:
            print("📈 Noticeable increase in search volume")
        else:
            print("📊 Baseline search volume")
        
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(test_hashtag_analysis())
