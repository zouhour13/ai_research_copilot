from typing import List
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from sqlmodel import Session as DBSession, select
from datetime import datetime

from app.db.models import Message, Session
from app.db.database import engine

class SQLModelChatMessageHistory(BaseChatMessageHistory):
    """Chat message history that uses SQLModel to store messages."""
    
    def __init__(self, session_id: int):
        self.session_id = session_id
        
        # Verify session exists
        with DBSession(engine) as db:
            session = db.get(Session, self.session_id)
            if not session:
                raise ValueError(f"Session {session_id} does not exist.")

    @property
    def messages(self) -> List[BaseMessage]:
        with DBSession(engine) as db:
            db_messages = db.exec(
                select(Message)
                .where(Message.session_id == self.session_id)
                .order_by(Message.created_at)
            ).all()
            
            langchain_messages = []
            for msg in db_messages:
                if msg.role == "user":
                    langchain_messages.append(HumanMessage(content=msg.content))
                elif msg.role == "assistant":
                    langchain_messages.append(AIMessage(content=msg.content))
                    
            return langchain_messages

    def add_messages(self, messages: List[BaseMessage]) -> None:
        with DBSession(engine) as db:
            for message in messages:
                role = "user" if isinstance(message, HumanMessage) else "assistant"
                sources = None
                if hasattr(message, "additional_kwargs") and "sources" in message.additional_kwargs:
                    sources = str(message.additional_kwargs["sources"])
                    
                msg = Message(
                    session_id=self.session_id,
                    role=role,
                    content=message.content,
                    sources=sources
                )
                db.add(msg)
                
            session = db.get(Session, self.session_id)
            if session:
                session.updated_at = datetime.utcnow()
                
            db.commit()

    def clear(self) -> None:
        with DBSession(engine) as db:
            messages = db.exec(
                select(Message).where(Message.session_id == self.session_id)
            ).all()
            for msg in messages:
                db.delete(msg)
            db.commit()

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    return SQLModelChatMessageHistory(session_id=int(session_id))
