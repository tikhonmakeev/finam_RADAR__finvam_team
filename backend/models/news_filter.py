from pydantic import BaseModel
from dataclasses import dataclass

@dataclass
class NewsFilter(BaseModel):
    tags: list[str] | None = None
    mustBeConfirmed: bool | None = False
