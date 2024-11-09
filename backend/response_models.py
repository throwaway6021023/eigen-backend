from typing import Literal

from pydantic import BaseModel


class SsePayload(BaseModel):
    data: str
    event: Literal["data", "end"]
