from telethon import TelegramClient
from datetime import datetime

# данные берутся с https://my.telegram.org
api_id = 123456
api_hash = "your_api_hash"

client = TelegramClient("session", api_id, api_hash)

async def main():
    await client.start()

    # указываем канал по @username или ссылке
    channel = "some_channel_username"

    # задаём дату, начиная с которой хотим сообщения
    start_date = datetime(2024, 9, 1)  # например, с 1 сентября 2024

    # выгружаем все сообщения от start_date до сегодня
    async for message in client.iter_messages(channel, offset_date=start_date, reverse=True):
        print(message.id, message.date, message.text)

with client:
    client.loop.run_until_complete(main())
