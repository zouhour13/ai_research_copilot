from langchain_core.tools import tool
from app.services.exa import search_sources

@tool
def exa_web_search(query: str) -> str:
    """Search the web for information using the Exa search engine.
    Always use this to look up current events, facts, or external knowledge.
    Returns a formatted string of results including titles and URLs.
    """
    try:
        results = search_sources(query, k=5)
        if not results:
            return "No relevant information found on the web."
            
        formatted_results = []
        for i, res in enumerate(results):
            formatted_results.append(f"Source [{i+1}]: {res.title}\nURL: {res.url}")
        
        return "\n\n".join(formatted_results)
    except Exception as e:
        return f"Error performing web search: {str(e)}"
