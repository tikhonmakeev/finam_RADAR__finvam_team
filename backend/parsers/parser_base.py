from abc import ABC
from datetime import datetime

from models.news_item import NewsItem


class ParserBase(ABC):
    def parse(self, start_date: datetime, end_date: datetime) -> list[NewsItem]:
        """
        Parse news items from start_date to end_date.

        :param start_date: datetime object representing the start date
        :param end_date: datetime object representing the end date
        :return: A list of dictionaries, where each dictionary is a news item
        """
        raise NotImplementedError