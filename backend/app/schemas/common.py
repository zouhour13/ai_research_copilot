from enum import Enum

class ChatMode(str, Enum):
    CHAT = "chat"
    RESEARCH = "research"
    FILE = "file"
    HYBRID = "hybrid"
