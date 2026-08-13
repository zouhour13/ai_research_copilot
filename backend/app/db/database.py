# pyrefly: ignore [missing-import]
from sqlmodel import SQLModel, create_engine

DATABASE_URL = "sqlite:///./research.db"

engine = create_engine(
    DATABASE_URL,
    echo=True
)

def init_db():
    SQLModel.metadata.create_all(engine)
