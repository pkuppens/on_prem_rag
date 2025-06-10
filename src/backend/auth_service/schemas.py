from datetime import datetime

from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str
    email: str | None = None
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    email: str | None
    roles: str

    class Config:
        from_attributes = True


class TokenOut(BaseModel):
    token: str


class OAuthRedirect(BaseModel):
    url: str
