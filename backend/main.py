from fastapi import FastAPI
import logging
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from routers.session_handler import router as session_router
from routers.stock_item_handler import router as stock_item_router
from routers.session_moment_handler import router as session_moment_handler
from routers.user_handler import router as user_management_router
from parser_of_news.news_router import router as news_router
from routers.trade_handler import router as trade_router
from routers.portfolio_item_handler import router as portfolio_item_router
from routers.operation_history_handler import router as operation_history_router
from auth.auth_handler import router as auth_router
from middelwares.ExceptionFetcherMiddleware import ExceptionHandlingMiddleware

logger = logging.getLogger(__name__)
logger.info("Starting application...")

app = FastAPI(
    title="Trading simulator",
    version="1.0.1",
    root_path="/api"
)

routers = [
    session_router,
    trade_router,
    stock_item_router,
    portfolio_item_router,
    session_moment_handler,
    user_management_router,
    auth_router,
    news_router,
    operation_history_router,
]

for router in routers:
    app.include_router(router)
app.add_middleware(ExceptionHandlingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    uvicorn.run(app)
