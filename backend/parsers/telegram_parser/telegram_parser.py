import os

from telethon import TelegramClient
from telethon.tl.custom.message import Message
from datetime import datetime

from models.news_item import NewsItem, Source


SESSION_FILE = "user_session"

class TgParser:
    def __init__(self):
        self.api_id = os.environ.get("tg_api_id")
        self.api_hash = os.environ.get("tg_api_hash")

        self.client = TelegramClient(SESSION_FILE, self.api_id, self.api_hash)

    async def connect(self):
        if not self.client.is_connected():
            await self.client.start()

    async def disconnect(self):
        if self.client.is_connected():
            await self.client.disconnect()

    async def parse(self, start_date: datetime, channels_usernames: list[str]) -> dict[str, NewsItem] | None:
        if not channels_usernames:
            return None
        res={}
        for channel in channels_usernames:
            items: list[NewsItem] = []
            async for message in self.client.iter_messages(
                    channel, offset_date=start_date, reverse=True
            ):
                title = message.text.split("\n")[0].split(".")[0]
                news_item = NewsItem(
                    title=title,
                    content=message.text,
                    createdAt=message.date,
                    updatedAt=message.date,
                    sources=[Source(
                        url=await self._get_telegram_link(message=message, username=channel),
                        addedAt=datetime.now()
                    )],
                )
                items.append(news_item)

            res[channel] = items

        return res

    async def _get_telegram_link(self, message: Message, username: str):
        if not message.post:
            return None  # Только для постов в канале
        if not self.client:
            return None  # Нужен клиент для получения сущности канала

        return f"https://t.me/{username}/{message.id}"
