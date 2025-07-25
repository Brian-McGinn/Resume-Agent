# simple_agent.py

from langchain_community.llms import Ollama
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode
from typing import TypedDict, Annotated
from langchain_core.messages import HumanMessage, AIMessage
from langchain_mcp_adapters import MultiServerMCPClient

client = MultiServerMCPClient(
    {
        "my_weather_server": {
            "url": "http://localhost:3004/sse",
            "transport": "streamable_http",
        },
    }
)

tools = client.get_tools()

# Define the state for the graph
class AgentState(TypedDict):
    messages: Annotated[list, HumanMessage | AIMessage]

# Create Ollama-based LLM (using llama3)
llm = Ollama(model="llama3.1")

# Define the node that calls the model
def call_model(state: AgentState) -> AgentState:
    messages = state["messages"]
    response = llm.invoke(messages)
    return {"messages": messages + [AIMessage(content=response)]}

# Build the LangGraph
graph = StateGraph(AgentState)

# Add the model node
graph.add_node("llama3", call_model)
graph.add_node("tool_executor", ToolNode(tools))

# Define the edge: after model call, we end
graph.set_entry_point("llama3")
graph.add_edge("llama3", END)

# Compile the graph into an executable app
app = graph.compile()

# Example usage
if __name__ == "__main__":
    user_input = "Hello"
    result = app.invoke({"messages": [HumanMessage(content=user_input)]})
    response = result["messages"][-1].content
    print(f"\nResponse:\n{response}")
