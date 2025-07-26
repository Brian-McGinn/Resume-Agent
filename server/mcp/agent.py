# simple_agent.py

from langchain_ollama.chat_models import ChatOllama
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from typing import List, Annotated
from typing_extensions import TypedDict
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph.message import AnyMessage, add_messages
from langgraph.checkpoint.memory import MemorySaver
import asyncio

client = MultiServerMCPClient(
    {
        "job_scraper": {
            "url": "http://localhost:3004/mcp",
            "transport": "streamable_http",
        },
    }
)

async def create_graph():
    # Create Ollama-based LLM (using llama3)
    llm = ChatOllama(model="llama3.1")
    tools = await client.get_tools()
    llm_with_tool = llm.bind_tools(tools)
    system_prompt = await client.get_prompt(server_name="job_scraper", prompt_name="system_prompt")
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_prompt[0].content),
        MessagesPlaceholder("messages")
    ])
    chat_llm = prompt_template | llm_with_tool

    # State Management
    class State(TypedDict):
        messages: Annotated[List[AnyMessage], add_messages]

    # Nodes
    def chat_node(state: State) -> State:
        state["messages"] = chat_llm.invoke({"messages": state["messages"]})
        return state

    # Building the graph
    graph_builder = StateGraph(State)
    graph_builder.add_node("chat_node", chat_node)
    graph_builder.add_node("tool_node", ToolNode(tools=tools))
    graph_builder.add_edge(START, "chat_node")
    graph_builder.add_conditional_edges("chat_node", tools_condition, {"tools": "tool_node", "__end__": END})
    graph_builder.add_edge("tool_node", "chat_node")
    graph = graph_builder.compile(checkpointer=MemorySaver())
    return graph

async def main():
    config = {"configurable": {"thread_id": 1234}}
    agent = await create_graph()
    format_msg = """Use the job_scraper_get_jobs tool to get 2 results_wanted. You will receive the output from the job_scraper tool. 
Return ONLY the tool output, exactly as it was returned, in the following JSON format:
[
    {
        "title": "string",
        "company": "string",
        "job_url": "string",
        "description": "string",
        "location": "string",
        "is_remote": "string"
    }
]
If there are multiple jobs, return a list of such objects. Do not add any extra text or explanation."""

    while True:
        msg = input("user input")
        response = await agent.ainvoke({"messages": format_msg }, config=config)
        # Check for tool outputs in the response and print them if present
        # Print the content of the ToolMessage from Ollama ChatOllama
        import json
        tool_message_content = response["messages"][-1].content  # or wherever the ToolMessage is

        # If it's a list of strings that are actually JSON objects, parse each one
        try:
            raw_list = json.loads(tool_message_content)  # Parses outer list
            job_list = [json.loads(job_str) if isinstance(job_str, str) else job_str for job_str in raw_list]

            # Now pretty-print the actual JSON structure
            print(json.dumps(job_list, indent=4))
        except json.JSONDecodeError as e:
            print(f"Error decoding tool message content: {e}")

if __name__ == "__main__":
    asyncio.run(main())
