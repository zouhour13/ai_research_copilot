# pyrefly: ignore [missing-import]
# Backwards-compatibility shim — existing code that does:
#   from app.langchain.core.llm import llm
# continues to work unchanged.
from app.llm.factory import get_llm

llm = get_llm()
