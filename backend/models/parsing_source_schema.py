from datetime import datetime

from pydantic import BaseModel


class TgSchema(BaseModel):
    from_date: datetime
    to_date: datetime
    channels_usernames: list[str]


class InterfaxSchema(BaseModel):
    from_date: datetime
    to_date: datetime


class ParsingSourceSchema(BaseModel):
    tg_schema: TgSchema | None
    interfax_schema: InterfaxSchema | None
