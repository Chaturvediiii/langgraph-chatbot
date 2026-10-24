from langgraph.graph import START, END, StateGraph
from langchain_cohere import ChatCohere
from dotenv import load_dotenv
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from langchain.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()
llm = ChatCohere(model="command-r7b-12-2024")

class ChatState(TypedDict):
    messages : Annotated[list[BaseMessage],add_messages]

def chat_node(state : ChatState):
    question = state['messages']

    answer = llm.invoke(question).content

    return {'messages': [answer]}

checkpointer = MemorySaver()
graph = StateGraph(ChatState)

graph.add_node('chat_node',chat_node)

graph.add_edge(START, 'chat_node')
graph.add_edge('chat_node', END)

chatbot = graph.compile(checkpointer=checkpointer)