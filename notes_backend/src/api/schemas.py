from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

# User
class UserBase(BaseModel):
    username: str = Field(..., description="Unique username")
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

class UserRead(UserBase):
    id: int

    class Config:
        orm_mode = True

# Auth
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

# Notes
class NoteBase(BaseModel):
    title: str
    content: str

class NoteCreate(NoteBase):
    pass

class NoteUpdate(BaseModel):
    title: Optional[str]
    content: Optional[str]

class NoteRead(NoteBase):
    id: int
    last_edited: datetime

    class Config:
        orm_mode = True

# Search
class NoteList(BaseModel):
    notes: List[NoteRead]
