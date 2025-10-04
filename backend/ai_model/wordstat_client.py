import os
import httpx
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

YANDEX_API_URL = "https://api.wordstat.yandex.net/v1/dynamics"
YANDEX_OAUTH_TOKEN = os.getenv("YANDEX_OAUTH_TOKEN")  # твой OAuth токен
YANDEX_CLIENT_ID = os.getenv("YANDEX_CLIENT_ID")  # clientId приложения

HEADERS = {
    "Authorization": f"Bearer {YANDEX_OAUTH_TOKEN}",
    "Client-Id": YANDEX_CLIENT_ID,
    "Content-Type": "application/json; charset=utf-8"
}


async def fetch_wordstat(keyword: str, news_date: str, region_id: int = 225) -> dict:
    """
    Получаем статистику из Яндекс Wordstat: 30 дней до новости и 2 дня события.

    Args:
        keyword (str): ключевое слово (без #)
        news_date (str): дата новости YYYY-MM-DD
        region_id (int): ID региона (по умолчанию 225 — Россия)

    Returns:
        dict: {"history_count": int, "event_count": int}
    """
    news_date = datetime.strptime(news_date, "%Y-%m-%d").date()
    start_date = (news_date - timedelta(days=30)).isoformat()
    end_date = (news_date + timedelta(days=1)).isoformat()  # событие + 1 день

    payload = {
        "phrase": f"+{keyword}",  # по API требование: оператор + перед словом
        "period": "daily",
        "fromDate": start_date,
        "toDate": end_date,
        "regions": [region_id],
        "devices": ["all"]
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(YANDEX_API_URL, headers=HEADERS, json=payload)
            resp.raise_for_status()
            data = resp.json()

            dynamics = data.get("dynamics", [])

            history_count, event_count = 0, 0
            for d in dynamics:
                date_str = d.get("date")
                count = d.get("count", 0)
                date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()

                if news_date - timedelta(days=30) <= date_obj < news_date:
                    history_count += count
                elif news_date <= date_obj <= news_date + timedelta(days=1):
                    event_count += count

            return {
                "history_count": history_count,
                "event_count": event_count
            }

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP ошибка Wordstat API: {e}")
        raise
    except Exception as e:
        logger.error(f"Ошибка при запросе Wordstat API: {e}")
        return {"history_count": 0, "event_count": 0}
