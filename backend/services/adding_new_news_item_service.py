from ai_model.summarizer import summarize_text
from dependencies import vector_store
from models.news_item import NewsItem
from services.rag_service import compare_news


class AddingNewNewsItemService:
    def __init__(self):
        pass

    async def add_news_item(self, news_item: NewsItem):
        summarize = summarize_text(news_item.content)
        closest_news_item = vector_store.find_similar_news(summarize, top_k=1)
        if closest_news_item:
            await self._update_closest_news_item(news_item, closest_news_item)
            await compare_news(news_item.content, closest_news_item.content)
        else:
            vector_store.index_news(news_item.id, news_item.content, news_item)

    async def _update_closest_news_item(self, news_item: NewsItem, closest_news_item: NewsItem):
        closest_news_item.sources.extend(news_item.source)
        # TODO обновить текст новости с помощью ЛЛМ