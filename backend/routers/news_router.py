from datetime import datetime
from http import HTTPStatus

from fastapi import APIRouter
from fastapi.params import Query

from dependencies import tg_parser, interfax_parser, vector_store
from models.news_filter import NewsFilter
from models.news_item import NewsItem, Source

from models.parsing_source_schema import ParsingSourceSchema

router = APIRouter(prefix="/api/news")

# Выносим список новостей в глобальную переменную
news_items = [
    # Существующие новости
    NewsItem(
        id=1,
        title="ЦБ снизил ключевую ставку — пришло время пересмотреть и ставки по нашим продуктам",
        isConfirmed=True,
        content="""Ставки по кредитам снизились. Вы также можете оформить рефинансирование и закрыть старый кредит, открытый под более высокие проценты. Условия в данном случае индивидуальны, они зависят от кредитной истории заемщиков и других факторов.

➡ Оставить заявку на кредит или рефинансирование с учетом сниженной ставки: https://u.tbank.ru/loan-low

Ставки по вкладам на один месяц мы повысили до ключевой — 17%. Новые условия по депозитам начинают действовать уже с сегодняшнего дня. Одновременно ставка по накопительным счетам снизилась на один процент.

➡ Открыть вклад: https://u.tbank.ru/deposit17""",
        sources=[Source(url="t.me/tbank", addedAt=datetime(2024, 9, 16, 12, 0))],
        createdAt=datetime(2024, 9, 16, 12, 0),
        hotnessScore=79.5,
    ),
    NewsItem(
        id=2,
        title="Центробанк снова снизил ставку — с 18% до 17% ☄",
        isConfirmed=True,
        content="""Обошлось без сюрпризов — такое решение ЦБ ждали эксперты. Ставку снизили не сильно, потому что инфляционные риски всё ещё сохраняются.

Эксперты прогнозируют постепенное снижение ключевой ставки и дальше, а значит, проценты по вкладам тоже будут меньше. Но вы ещё успеваете заработать на Альфа-Вкладах.""",
        sources=[Source(url="t.me/alfabank", addedAt=datetime(2024, 9, 12, 13, 30))],
        createdAt=datetime(2024, 9, 12, 13, 30),
        hotnessScore=85.0,
    ),
    
    # Новые сгенерированные новости
    NewsItem(
        id=3,
        title="Сбер запускает ипотеку с господдержкой под 6% 🏠",
        isConfirmed=True,
        content="""Сбербанк объявил о старте новой программы ипотечного кредитования с государственной поддержкой. Ставка начинается от 6% годовых для первичного рынка недвижимости.

Основные условия:
• Срок кредита — до 30 лет
• Первоначальный взнос — от 15%
• Максимальная сумма — 12 млн рублей

Программа действует до конца года. Успейте подать заявку!""",
        sources=[Source(url="t.me/sberbank", addedAt=datetime(2024, 9, 18, 10, 15))],
        createdAt=datetime(2024, 9, 18, 10, 15),
        hotnessScore=92.3,
    ),
    
    NewsItem(
        id=4,
        title="ВТБ: инфляция замедлилась до 5.8% в годовом выражении 📉",
        isConfirmed=True,
        content="""По данным Росстата, годовая инфляция в России продолжает замедляться. В сентябре показатель составил 5.8% против 6.1% в августе.

Аналитики ВТБ ожидают дальнейшего снижения инфляции до 5.5% к концу года, что создает предпосылки для смягчения денежно-кредитной политики ЦБ.

Основной вклад в замедление инфляции внесли укрепление рубля и снижение цен на продовольственные товары.""",
        sources=[Source(url="t.me/bankvtb", addedAt=datetime(2024, 9, 19, 11, 45))],
        createdAt=datetime(2024, 9, 19, 11, 45),
        hotnessScore=78.9,
    ),
    
    NewsItem(
        id=5,
        title="ЦБ предупредил о новых кибератаках на банки 🛡️",
        isConfirmed=True,
        content="""Банк России распространил предупреждение о новой волне фишинговых атак на клиентов финансовых организаций. Злоумышленники рассылают SMS с просьбой перейти по ссылке для подтверждения операций.

Рекомендации ЦБ:
• Не переходить по подозрительным ссылкам
• Проверять отправителя SMS
• Использовать официальные приложения банков
• Включать двухфакторную аутентификацию

При подозрениях на мошенничество немедленно блокировать карту через приложение банка.""",
        sources=[Source(url="t.me/centralbank_russia", addedAt=datetime(2024, 9, 20, 9, 30))],
        createdAt=datetime(2024, 9, 20, 9, 30),
        hotnessScore=86.7,
    ),
    
    NewsItem(
        id=6,
        title="MOEX обновил исторический максимум 📈",
        isConfirmed=True,
        content="""Индекс МосБиржи впервые в истории превысил отметку 4200 пунктов. Рост сопровождался увеличением торгового оборота до рекордных 350 млрд рублей.

Лидерами роста стали акции:
• Сбербанк +3.2%
• Газпром +2.8%  
• Лукойл +2.5%
• Норникель +4.1%

Эксперты связывают рост с укреплением рубля и снижением ключевой ставки ЦБ.""",
        sources=[Source(url="t.me/MoscowExchangeOfficial", addedAt=datetime(2024, 9, 23, 18, 20))],
        createdAt=datetime(2024, 9, 23, 18, 20),
        hotnessScore=95.1,
    ),
    
    NewsItem(
        id=7,
        title="Ключевая ставка может снизиться до 15% к концу года - прогноз",
        isConfirmed=True,
        content="""Аналитики Альфа-Инвестиций ожидают дальнейшего снижения ключевой ставки ЦБ до 15-16% к декабрю 2024 года. Такая динамика станет возможной при сохранении текущих темпов замедления инфляции.

"Мы видим пространство для смягчения денежно-кредитной политики, - отмечает главный экономист Альфа-Банка. - Инфляционные риски постепенно отступают."

Инвесторы могут рассмотреть облигации федерального займа с плавающей ставкой для защиты от волатильности.""",
        sources=[Source(url="t.me/alfa_investments", addedAt=datetime(2024, 9, 25, 14, 10))],
        createdAt=datetime(2024, 9, 25, 14, 10),
        hotnessScore=82.4,
    ),
    
    NewsItem(
        id=8,
        title="Газпромбанк запускает ESG-облигации для зеленых проектов 🌱",
        isConfirmed=True,
        content="""Газпромбанк разместит первые ESG-облигации объемом 15 млрд рублей. Средства будут направлены на финансирование экологически чистых проектов, включая возобновляемую энергетику и энергоэффективные технологии.

Особенности выпуска:
• Срок обращения — 5 лет
• Ставка купона — 9.5% годовых
• Листинг на Московской бирже

Размещение пройдет в октябре, биржевые торги начнутся с 15 ноября.""",
        sources=[Source(url="t.me/gazprombank", addedAt=datetime(2024, 9, 26, 16, 0))],
        createdAt=datetime(2024, 9, 26, 16, 0),
        hotnessScore=73.8,
    ),
    
    NewsItem(
        id=9,
        title="ОЗОН Банк увеличил кэшбэк до 10% на маркетплейсе 🛒",
        isConfirmed=True,
        content="""ОЗОН Банк анонсировал увеличение кэшбэка по картам до 10% при покупках на маркетплейсе Ozon. Акция действует до 31 декабря для всех держателей карт.

Условия повышенного кэшбэка:
• 10% — на категории "Электроника" и "Бытовая техника"
• 7% — на все остальные покупки на Ozon
• 1% — при оплате в других магазинах

Лимит повышенного кэшбэка — 5000 рублей в месяц.""",
        sources=[Source(url="t.me/ozon_bank_official", addedAt=datetime(2024, 9, 27, 12, 30))],
        createdAt=datetime(2024, 9, 27, 12, 30),
        hotnessScore=88.2,
    ),
    
    NewsItem(
        id=10,
        title="Т-Инвестиции: дивидендные акции могут принести до 15% доходности 💰",
        isConfirmed=True,
        content="""Аналитики Т-Инвестиций рекомендуют обратить внимание на дивидендные акции российских компании. В условиях снижения ключевой ставки дивидендная доходность становится более привлекательной.

Топ-5 рекомендаций:
1. Татнефть — дивдоходность 12.5%
2. Норникель — 11.8%  
3. Сургутнефтегаз — 15.2%
4. МТС — 9.7%
5. ФСК ЕЭС — 8.9%

"В ближайшие месяцы ожидаем рост интереса к акциям с высокой дивидендной историей", - отмечают аналитики.""",
        sources=[Source(url="t.me/tb_invest_official", addedAt=datetime(2024, 9, 28, 15, 45))],
        createdAt=datetime(2024, 9, 28, 15, 45),
        hotnessScore=84.6,
    )
]

@router.get("/{id}", response_model=NewsItem | None)
async def get_news_item_by_id(id: int):
    """Получить новость по ID"""
    # Ищем новость с указанным ID
    for item in news_items:
        if item.id == id:
            return item
    # Если не найдено, возвращаем None (будет 404)
    return None

@router.get("/", response_model=list[NewsItem])
async def get_news_items_by_filters(news_filter: NewsFilter = Query(None)):
    """Получить список всех новостей"""
    filtered_news = news_items
    if news_filter:
        # Фильтрация по тегам
        if news_filter.tags:
            filtered_news = [item for item in filtered_news 
                           if any(tag.lower() in item.content.lower() for tag in news_filter.tags)]
        
        # Фильтрация по подтвержденным новостям
        if news_filter.mustBeConfirmed:
            filtered_news = [item for item in filtered_news if item.isConfirmed]

    return filtered_news

@router.post("/", status_code=HTTPStatus.CREATED)
async def parse_period(parsing_source_schema: ParsingSourceSchema):
    news = []
    if parsing_source_schema.tg_schema:
        news.extend(
            await tg_parser.parse(
                parsing_source_schema.tg_schema.from_date,
                parsing_source_schema.tg_schema.channels_usernames
            )
        )
    if parsing_source_schema.interfax_schema:
        news.extend(
            interfax_parser.parse(
                parsing_source_schema.interfax_schema.from_date,
                parsing_source_schema.interfax_schema.to_date
            )
        )

    for news_item in news:
        vector_store.index_news(text=news_item.content, metadata=news_item)
    return news
