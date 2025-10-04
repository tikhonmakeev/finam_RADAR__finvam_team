import os

from telethon import TelegramClient
from datetime import datetime

from models.news_item import NewsItem
from parsers.parser_base import ParserBase


class TgParser(ParserBase):
    def __init__(self):
        self.api_id = os.environ.get("tg_api_id")
        self.api_hash = os.environ.get("tg_api_hash")

        self.client = TelegramClient("session", self.api_id, self.api_hash)

    async def connect(self):
        if not self.client.is_connected():
            await self.client.start(bot_token=os.getenv("TG_BOT_TOKEN"))

    async def disconnect(self):
        if self.client.is_connected():
            await self.client.disconnect()

    async def parse(self, start_date: datetime, end_date: datetime, **kwargs) -> dict[str, NewsItem] | None:
        if "channels_usernames" in kwargs:
            channels_usernames: list[str] = kwargs["channels_usernames"]
        else:
            return


        # задаём дату, начиная с которой хотим сообщения
        res={}
        # выгружаем все сообщения от start_date до сегодня
        for channel in channels_usernames:
            items: list[NewsItem] = []
            async for message in self.client.iter_messages(channel, offset_date=start_date, reverse=True):
                news_item = NewsItem(
                    id=None,
                    title=None,
                    content=message.text,
                    tags=None,
                    createdAt=message.date,
                    sources=str(message.id),
                )
                items.append(news_item)

            res[channel] = items

            return res
