from db.vector_store import VectorStore
from parsers.interfax_parser.interfax_parser import InterfaxParser
from parsers.telegram_parser.telegram_parser import TgParser

vector_store = VectorStore()
interfax_parser = InterfaxParser()
tg_parser = TgParser()
