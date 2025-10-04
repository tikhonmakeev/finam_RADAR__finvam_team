from datetime import datetime
from http import HTTPStatus

from fastapi import APIRouter
from fastapi.params import Query

from dependencies import tg_parser, interfax_parser, vector_store
from models.news_filter import NewsFilter
from models.news_item import NewsItem, Source

from models.parsing_source_schema import ParsingSourceSchema

router = APIRouter(prefix="/news")

@router.get("/{id}", response_model=NewsItem | None)
async def get_news_item_by_id():
    return NewsItem(
        id="1",
        title="Test",
        content="Вечером город окутан мягким светом фонарей, отражающихся в лужах после недавнего дождя. Люди спешат по тротуарам, спрятавшись под зонтиками, а запах свежей земли и мокрого асфальта смешивается с ароматом свежесваренного кофе из маленьких уличных кафешек. Кажется, что время замедлилось, и каждый звук — шаг, смех, скрип двери — становится особенным.",
        sources=Source(url="http://t.me/tikhonmakeev", addedAt=datetime.now()),
        createdAt=datetime.now(),
        hotnessScore=80,
    )
    # return vector_store.get_news_item_by_id()

@router.get("/", response_model=list[NewsItem])
async def get_news_items_by_filters(news_filter: NewsFilter = Query(None)):
    base_sentences = [
        "Вечером город окутан мягким светом фонарей, отражающихся в лужах после дождя.",
        "Люди спешат по тротуарам, спрятавшись под разноцветными зонтиками.",
        "Запах свежей земли смешивается с ароматом свежесваренного кофе из маленьких кафе.",
        "Кажется, что время замедлилось, и каждый звук — шаг, смех, скрип двери — становится особенным.",
        "На улицах тихо, слышны только далёкие голоса и шум машин, проезжающих мимо.",
        "Небо окрашено мягкими оттенками заката, отражающимися на мокрой мостовой.",
        "Ветер играет с листьями деревьев, шурша под ногами прохожих.",
        "В кафе мерцают лампы, а посетители тихо разговаривают за столиками.",
        "Город дышит спокойствием, редкие прохожие спешат домой после работы.",
        "Фонари отражаются в витринах магазинов, создавая атмосферу уюта и покоя."
    ]
    news_items = [
        NewsItem(
            id=str(i),
            title=f"Test {i}",
            content=base_sentences[i - 1],
            sources=[Source(url="http://t.me/tikhonmakeev", addedAt=datetime.now())],
            createdAt=datetime.now(),
            hotnessScore=80,
        )
        for i in range(1, 11)  # 10 элементов
    ]
    return news_items
    # return vector_store.get_news_by_filters(news_filter)

@router.post("/", status_code=HTTPStatus.CREATED)
async def parse_period(parsing_source_schema: ParsingSourceSchema):
    news = []
    if parsing_source_schema.tg_schema:
        news.extend(
            await tg_parser.parse(
                parsing_source_schema.tg_schema.from_date,
                parsing_source_schema.tg_schema.to_date
            )
        )
    if parsing_source_schema.interfax_schema:
        news.extend(
            await interfax_parser.parse(
                parsing_source_schema.interfax_schema.from_date,
                parsing_source_schema.interfax_schema.to_date
            )
        )
    return news
