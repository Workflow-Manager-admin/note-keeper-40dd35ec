from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, func
from sqlalchemy.orm import relationship
from src.api.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    notes = relationship("Note", back_populates="owner")

class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(128))
    content = Column(Text)
    last_edited = Column(DateTime, server_default=func.now(), onupdate=func.now(), index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="notes")
