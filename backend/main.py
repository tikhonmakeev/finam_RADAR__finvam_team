from fastapi import FastAPI
import logging
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

from db.vector_store import VectorStore
from parsers.interfax_parser.run import InterfaxParser
from routers.news_router import router as news_router
from config import settings

logger = logging.getLogger(__name__)
logger.info("Starting application...")

vector_store = VectorStore()
parser = InterfaxParser()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.1",
    root_path=settings.API_V1_STR
)

routers = [
    news_router
]

for router in routers:
    app.include_router(router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )
