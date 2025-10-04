from pydantic import BaseModel


class NewsFilter(BaseModel):
    tags: list[str] = []
    mustBeConfirmed: bool = False
