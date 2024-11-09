from pydantic import BaseModel


class CreateChatIn(BaseModel):
    session_id: str
    message: str


class CreateContextIn(BaseModel):
    title: str
    content: str
