from pydantic import BaseModel


class CreateChatIn(BaseModel):
    message: str
    session_id: str
