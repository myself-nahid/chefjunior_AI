from pydantic import BaseModel
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    user_role: str

class TokenData(BaseModel):
    email: Optional[str] = None

class TokenPayload(BaseModel):
    sub: Optional[str] = None