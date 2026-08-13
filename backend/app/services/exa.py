import os
# pyrefly: ignore [missing-import]
from exa_py import Exa
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

load_dotenv()

exa = Exa(api_key=os.getenv("EXA_API_KEY"))

def search_sources(query: str, k: int = 5):
    results = exa.search(query, num_results=k)
    return results.results
