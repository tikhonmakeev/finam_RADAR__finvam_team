from datetime import datetime
from typing import NamedTuple

from pydantic import BaseModel, Field, HttpUrl


class Source(BaseModel):
    url: str
    addedAt: datetime

class NewsItem(BaseModel):
    id: int = Field(..., description="Уникальный идентификатор поста")
    title: str = Field(..., description="Заголовок поста")
    content: str = Field(..., description="Основное содержимое поста")
    tags: list[str] = Field(default_factory=list, description="Массив тегов, связанных с постом")
    createdAt: datetime = Field(..., description="Дата и время создания поста в формате ISO")
    timeline: list[datetime] = Field(default_factory=list, description="Хронологическая последовательность событий в формате ISO 8601")
    hotnessScore: float = Field(..., description="Оценка популярности поста")
    isConfirmed: bool = Field(..., description="Флаг, подтверждён ли пост официально")
    sources: list[Source] = Field(description="Источники информации, использованные для поста")
