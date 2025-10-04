from http import HTTPStatus

from fastapi import APIRouter
from fastapi.params import Query

from dependencies import vector_store, parser
from models.news_filter import NewsFilter
from models.news_item import NewsItem
from datetime import datetime

router = APIRouter(prefix="/news")

@router.get("/{id}", response_model=NewsItem | None)
async def get_news_item_by_id():
    return vector_store.get_news_item_by_id()

@router.get("/", response_model=list[NewsItem])
async def get_news_items_by_filters(news_filter: NewsFilter = Query(None)):
    return vector_store.get_news_by_filters(news_filter)

@router.post("/", status_code=HTTPStatus.CREATED)
async def parse_period():
    news = parser.parse(datetime.now(), datetime.now())
    return news
