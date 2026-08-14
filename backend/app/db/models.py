# pyrefly: ignore [missing-import]
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime
# pyrefly: ignore [missing-import]
from app.schemas.common import ChatMode

class Session(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    mode: ChatMode
    file_search_store_name: Optional[str] = None
    file_name: Optional[str] = None
    file_storage_path: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    messages: List["Message"] = Relationship(
        back_populates="session",
        cascade_delete=True
    )

class Message(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="session.id")
    role: str
    content: str
    sources: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    session: Session = Relationship(back_populates="messages")
