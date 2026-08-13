"""
Research Agent — built with LangChain 1.3.0's new create_agent API.

LangChain 1.3.0 uses a graph-based agent (LangGraph under the hood).
`create_agent` returns a compiled StateGraph.
Invoke with: {"messages": [HumanMessage(content=...), ...]}
The result is an AddableValuesDict with key "messages"; the last message is the AI reply.
"""
# pyrefly: ignore [missing-import]
from langchain.agents import create_agent
# pyrefly: ignore [missing-import]
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from app.langchain.core.llm import llm
from app.langchain.tools.exa_search import exa_web_search
from app.langchain.tools.visualizer import generate_chart_from_data

SYSTEM_PROMPT = """You are an expert AI Research Copilot with access to powerful tools.

## Your capabilities
- **Web Search** (exa_web_search): Use this to look up current events, facts, statistics, or any real-world information.
- **Data Visualization** (generate_chart_from_data): Generate interactive charts from uploaded CSV/Excel files.

## Instructions
- Always search the web before answering factual questions about current events or recent data.
- Provide comprehensive, well-cited answers using Markdown.
- Cite sources inline using [1], [2], etc. and list sources at the end.
- Format code, tables, and lists using proper Markdown syntax.
- Be thorough but concise.
"""


def get_research_agent():
    """
    Returns a LangChain 1.3.0 compiled graph agent.

    Usage:
        agent = get_research_agent()
        result = agent.invoke({"messages": [HumanMessage(content=user_input)]})
        ai_response = result["messages"][-1].content
    """
    tools = [exa_web_search, generate_chart_from_data]

    graph = create_agent(
        model=llm,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
    )
    return graph


def invoke_research_agent(user_input: str, history: list) -> str:
    """
    High-level helper to invoke the research agent and return just the string response.
    Converts LangChain history messages to the format create_agent expects.
    
    Args:
        user_input: The user's latest message.
        history: List of LangChain BaseMessage objects (HumanMessage / AIMessage).
    
    Returns:
        The AI's response as a string.
    """
    agent = get_research_agent()

    # Build message list: history + new user message
    messages = list(history) + [HumanMessage(content=user_input)]

    result = agent.invoke({"messages": messages})
    
    # The last message in the result is the final AI response
    all_messages = result.get("messages", [])
    if all_messages:
        last_msg = all_messages[-1]
        return last_msg.content if hasattr(last_msg, "content") else str(last_msg)
    
    return "I was unable to generate a response. Please try again."


async def astream_research_agent(user_input: str, history: list):
    """
    Async generator that streams chunks from the research agent.
    Yields string chunks as they arrive.
    
    Args:
        user_input: The user's latest message.
        history: List of LangChain BaseMessage objects.
    
    Yields:
        String chunks of the response.
    """
    agent = get_research_agent()
    messages = list(history) + [HumanMessage(content=user_input)]

    async for event in agent.astream_events({"messages": messages}, version="v2"):
        event_type = event.get("event", "")
        if event_type == "on_chat_model_stream":
            chunk = event.get("data", {}).get("chunk")
            if chunk and hasattr(chunk, "content") and chunk.content:
                yield chunk.content
