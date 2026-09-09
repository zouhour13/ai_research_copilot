from pydantic import BaseModel
from app.schemas.common import ChatMode

class ChatRequest(BaseModel):
    content: str
    # The composer sends its effective mode with every message.  This keeps the
    # request route correct even if a previous session-mode update was delayed
    # or the client restored stale session state.
    mode: ChatMode | None = None
