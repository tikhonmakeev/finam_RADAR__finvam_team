from http import HTTPStatus

from fastapi import APIRouter
from fastapi.params import Query

from dependencies import tg_parser, interfax_parser, vector_store
from models.news_filter import NewsFilter
from models.news_item import NewsItem

from models.parsing_source_schema import ParsingSourceSchema

router = APIRouter(prefix="/news")

@router.get("/{id}", response_model=NewsItem | None)
async def get_news_item_by_id():
    return vector_store.get_news_item_by_id()

@router.get("/", response_model=list[NewsItem])
async def get_news_items_by_filters(news_filter: NewsFilter = Query(None)):
    return vector_store.get_news_by_filters(news_filter)

@router.post("/", status_code=HTTPStatus.CREATED)
async def parse_period(parsing_source_schema: ParsingSourceSchema):
    news = []
    if parsing_source_schema.tg_schema:
        news.extend(
            tg_parser.parse(
                parsing_source_schema.tg_schema.from_date,
                parsing_source_schema.tg_schema.to_date
            )
        )
    if parsing_source_schema.interfax_schema:
        news.extend(
            interfax_parser.parse(
                parsing_source_schema.interfax_schema.from_date,
                parsing_source_schema.interfax_schema.to_date
            )
        )
    return news
