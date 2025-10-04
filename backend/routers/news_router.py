from fastapi import APIRouter
from fastapi.params import Query

from models.news_filter import NewsFilter
from parsers.interfax_parser.run import InterfaxParser
from models.news_item import NewsItem
from datetime import datetime

router = APIRouter()

@router.get("/news", response_model=list[NewsItem])
async def get_news(news_filter: NewsFilter = Query(None)):
    parser = InterfaxParser()
    news = parser.parse(datetime.now(), datetime.now())
    return news
