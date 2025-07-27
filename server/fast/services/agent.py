# simple_agent.py

from prompts.prompts import automate_prompt
from services.rag_service import log_to_langsmith
from services.rag_service import get_context
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_mcp_adapters.client import MultiServerMCPClient
import json
from langchain_ollama.chat_models import ChatOllama
from typing import List, Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import AnyMessage, add_messages


client = MultiServerMCPClient(
    {
        "job_scraper": {
            "url": "http://mcp-server:3004/mcp",
            "transport": "streamable_http",
        },
    }
)

class AgentService:
    async def create_graph(self):
        try:
            print("Creating Ollama LLM...")
            # Create Ollama-based LLM (using llama3)
            llm = ChatOllama(model="llama3.1", base_url="http://host.docker.internal:11434")
            
            print("Getting tools from MCP client...")
            try:
                tools = await client.get_tools()
                print(f"Successfully got {len(tools)} tools from MCP server")
                for tool in tools:
                    print("!!!!!!!!!!!")
                    print(tool)
            except Exception as e:
                print(f"Failed to connect to MCP server: {e}")
                print("Available MCP server URLs to try:")
                print("- http://mcp-server:3004/mcp (Docker network)")
                print("- http://localhost:3004/mcp (Local development)")
                print("- http://host.docker.internal:3004/mcp (Docker to host)")
                raise
            
            print("Binding tools to LLM...")
            llm_with_tool = llm.bind_tools(tools)
            
            print("Getting system prompt from MCP client...")
            system_prompt = await client.get_prompt(server_name="job_scraper", prompt_name="system_prompt")
            
            print("Creating prompt template...")
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

            print("Building graph...")
            # Building the graph
            graph_builder = StateGraph(State)
            graph_builder.add_node("chat_node", chat_node)
            graph_builder.add_node("tool_node", ToolNode(tools=tools))
            graph_builder.add_edge(START, "chat_node")
            graph_builder.add_conditional_edges("chat_node", tools_condition, {"tools": "tool_node", "__end__": END})
            graph_builder.add_edge("tool_node", "chat_node")
            graph = graph_builder.compile()
            print("Graph created successfully")
            return graph
        except Exception as e:
            print(f"Error in create_graph: {str(e)}")
            import traceback
            traceback.print_exc()
            raise

    async def automate(self):
        """Handle automated agent orchestration request."""
        try:
            agent = await self.create_graph()
            # prompt = ChatPromptTemplate.from_messages([automate_system_prompt, automate_prompt]).format_messages()

            print("Call resume agent")
            print("------------------------------------")           
            response = await agent.ainvoke({"messages": automate_prompt })
            # Check for tool outputs in the response and print them if present
            # Print the content of the ToolMessage from Ollama ChatOllama
            print("------------------------------------")  
            print("finished call")
            tool_message_content = response["messages"][-1].content  # or wherever the ToolMessage is
            
            # If it's a list of strings that are actually JSON objects, parse each one
            try:
                raw_list = json.loads(tool_message_content)  # Parses outer list
                job_list = [json.loads(job_str) if isinstance(job_str, str) else job_str for job_str in raw_list]

                # Now pretty-print the actual JSON structure
                print(json.dumps(job_list, indent=4))
                return True
            except json.JSONDecodeError as e:
                print(f"Error decoding tool message content: {e}")
        except json.JSONDecodeError as e:
            print(f"Error while running the automated resume agent: {e}")
            return False

