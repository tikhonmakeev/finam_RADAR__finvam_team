from telethon import TelegramClient
from datetime import datetime

from models.news_item import NewsItem
from parsers.parser_base import ParserBase


class TgParser(ParserBase):
    def __init__(self):
        self.api_id = 123456
        self.api_hash = "your_api_hash"

        self.client = TelegramClient("session", self.api_id, self.api_hash)
        self.client.start()

    async def parse(self, start_date: datetime, end_date: datetime, **kwargs) -> dict[str, NewsItem] | None:
        if "channels_usernames" in kwargs:
            channels_usernames: list[str] = kwargs["channels_usernames"]
        else:
            return


        # задаём дату, начиная с которой хотим сообщения
        start_date = datetime(2024, 9, 1)  # например, с 1 сентября 2024
        res=dict()
        # выгружаем все сообщения от start_date до сегодня
        for channel in channels_usernames:
            l = []
            async for message in self.client.iter_messages(channel, offset_date=start_date, reverse=True):
                l.append(message.id, message.date, message.text)
                NewsItem(id=None,title=None,content=message.text,tags=None,createdAt=message.date,sources=message.id)

            res[channel] = l
        return res
