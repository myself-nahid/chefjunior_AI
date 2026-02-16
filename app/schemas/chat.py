from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatBase(BaseModel):
    user_id: int
    title: Optional[str] = None
    messages: List[ChatMessage] = []


class ChatCreate(ChatBase):
    pass


class Chat(ChatBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
