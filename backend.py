from langgraph.graph import START, END, StateGraph
from langchain_cohere import ChatCohere
from dotenv import load_dotenv
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, AIMessage
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3

from langchain_community.tools import DuckDuckGoSearchRun 
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode, tools_condition
import requests

load_dotenv()
llm = ChatCohere(model="command-r7b-12-2024", streaming=False)

search_tool = DuckDuckGoSearchRun(region="us-en")

@tool
def web_search(query: str) -> str:
    """Search the web for information about a topic.
    Always provide a non-empty query."""
    return search_tool.invoke({"query": query})

@tool
def calculator(first_num : float, second_num : float, operator:str)-> dict:
    """ 
    Perform basic arithmetic operations on two numbers.
    supported operators : add, sub, mul, and div
    """
    try:
        if operator in ("add", "+"):
            res = first_num + second_num
        elif operator in ("sub", "-"):
            res = first_num - second_num
        elif operator in ("mul", "*"):
            res = first_num * second_num
        elif operator in ("div", "/"):
            if second_num == 0:
                return {"error": "division by zero"}
            res = first_num / second_num
        else:
            return {"error": f"Unsupported operator: {operator}"}
    except Exception as e:
        return {"error":str(e)}

@tool
def get_stock_price(symbol : str)->dict:
    """
    Fetch latest stock for a given symbol  ( e.g. 'AAPL', 'TSLA')
    using Alpha vantage with api key in the url
    """
    url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey=31YBL7ZTCMVFAXTX'
    res = requests.get(url)
    return res.json()

tools = [get_stock_price,web_search,calculator]
llm_with_tools = llm.bind_tools(tools)

class ChatState(TypedDict):
    messages : Annotated[list[BaseMessage],add_messages]

def chat_node(state: ChatState):
    """LLM node that may answer or request a tool call."""
    messages = state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

conn = sqlite3.connect(database="chatDB.db",check_same_thread=False)

checkpointer = SqliteSaver(conn=conn)
graph = StateGraph(ChatState)
tool_node = ToolNode(tools)

graph.add_node('chat_node',chat_node)
graph.add_node('tools',tool_node)

graph.add_edge(START, 'chat_node')
graph.add_conditional_edges('chat_node',tools_condition)
graph.add_edge('tools','chat_node')

chatbot = graph.compile(checkpointer=checkpointer)

def retrieve_threads():
    all_threads = set()
    for checkpoint in checkpointer.list(None):
        all_threads.add(checkpoint.config['configurable']['thread_id'])
    return list(all_threads)