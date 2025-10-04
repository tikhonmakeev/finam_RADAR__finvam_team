from datetime import datetime, timedelta

from dependencies import vector_store, interfax_parser

if __name__ == "__main__":
    for new in interfax_parser.parse((datetime.now() - timedelta(days=10)).date().strftime("%Y/%m/%d"), datetime.now().date().strftime("%Y/%m/%d")):
        vector_store.index_news(new)