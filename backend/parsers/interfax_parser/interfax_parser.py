import os
from datetime import datetime

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrapy.signalmanager import dispatcher
from scrapy import signals

from models.news_item import NewsItem


class InterfaxParser:
    def parse(self, start_date: datetime, end_date: datetime) -> list[NewsItem]:
        """
        Parse news items from start_date to end_date.

        :param start_date: The start date in 'YYYY/MM/DD' format.
        :param end_date: The end date in 'YYYY/MM/DD' format.
        :return: A list of dictionaries, where each dictionary is a news item
        """
        print(f"Scraping data from {start_date} to {end_date}...")

        # Set the project base directory to the one containing scrapy.cfg
        project_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(project_dir)

        settings = get_project_settings()
        scraped_data = []

        def item_scraped(item, response, spider):
            scraped_data.append(dict(item))

        dispatcher.connect(item_scraped, signal=signals.item_scraped)

        process = CrawlerProcess(settings)
        process.crawl('jobs', start_date=start_date, end_date=end_date)
        process.start()  # The script will block here until the crawling is finished

        # Disconnect the signal to avoid multiple connections if scrape is called again
        dispatcher.disconnect(item_scraped, signal=signals.item_scraped)

        return scraped_data
