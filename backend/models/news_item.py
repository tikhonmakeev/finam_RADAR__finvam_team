from datetime import datetime

from pydantic import BaseModel, Field


class Source(BaseModel):
    url: str
    addedAt: datetime


class NewsItem(BaseModel):
    id: int | None= Field(description="Уникальный идентификатор поста", default=None)
    title: str = Field(..., description="Заголовок поста")
    content: str = Field(..., description="Основное содержимое поста")
    tags: list[str]= Field(default_factory=list, description="Массив тегов, связанных с постом")
    createdAt: datetime = Field(..., description="Дата и время создания поста в формате ISO")
    updatedAt: datetime = Field(..., description="Дата и время последнего обновления поста в формате ISO", default=datetime.now())
    hotnessScore: float = Field(..., description="Оценка популярности поста", default=0)
    isConfirmed: bool | None = Field(description="Флаг, подтверждён ли пост официально", default=False)
    sources: list[Source] = Field(default_factory=list, description="Источники информации, использованные для поста")
