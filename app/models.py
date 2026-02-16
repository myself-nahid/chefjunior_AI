from pydantic import BaseModel
from typing import Literal, List

class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str

class ConversationHistory(BaseModel):
    messages: List[ChatMessage] = []