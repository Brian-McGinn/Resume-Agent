from prompts.prompts import automate_prompt
from services.rag_service import log_to_langsmith
from services.comparison_agent import ComparisonAgent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.messages import ToolMessage
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
            except Exception as e:
                print(f"Failed to connect to MCP server: {e}")
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
                parsed_jobs: dict

            # Nodes
            def chat_node(state: State) -> State:
                print("Running chat!")
                state["messages"] = chat_llm.invoke({"messages": state["messages"]})
                print("Completed llm call")
                return state

            def parse_tool_json(state: State) -> State:
                """
                LangGraph node function to parse ToolMessage JSON content and attach parsed results to state.
                """
                tool_messages = [
                    msg for msg in state["messages"]
                    if isinstance(msg, ToolMessage)
                ]

                parsed_results = []
                for msg in tool_messages:
                    try:
                        raw_list = json.loads(msg.content)
                        # In case each item is still a stringified JSON object
                        job_list = [
                            json.loads(item) if isinstance(item, str) else item
                            for item in raw_list
                        ]
                        parsed_results.extend(job_list)
                    except json.JSONDecodeError as e:
                        parsed_results.append({"error": f"Failed to decode tool message: {str(e)}"})

                # Store in state for downstream usage
                state["parsed_jobs"] = parsed_results
                return state

            # Custom conditional function for parse_jobs_node
            def parse_jobs_condition(state: State):
                """
                If parsed_jobs is empty, go back to tool_node, else end.
                """
                parsed_jobs = state.get("parsed_jobs", [])
                if not parsed_jobs:
                    print("No parsed jobs found, returning to tool_node.")
                    return "tool_node"
                return "score_jobs_node"

            # Define a new node for scoring jobs after parse_jobs_node
            def score_jobs_node(state: State):
                """
                Node to score jobs using the ComparisonAgent after jobs have been parsed.
                """
                try:
                    comparison_agent = ComparisonAgent()
                    sort_by_score = comparison_agent.generate_job_scores()
                    # Optionally, update the state with scores if needed
                    for score in sort_by_score:
                        print("************************",score.title, score.score)
                    state["job_scores"] = sort_by_score
                    return state
                except Exception as e:
                    print(f"Error in score_jobs_node: {e}")
                    import traceback
                    traceback.print_exc()
                    return state

            print("Building graph...")
            # Building the graph
            graph_builder = StateGraph(State)
            #Create graph nodes
            graph_builder.add_node("chat_node", chat_node)
            graph_builder.add_node("tool_node", ToolNode(tools=tools))
            graph_builder.add_node("parse_jobs_node", parse_tool_json)
            graph_builder.add_node("score_jobs_node", score_jobs_node)
            #Create graph edges
            graph_builder.add_edge(START, "chat_node")
            # If tools are needed, go to tool_node; otherwise, end.
            graph_builder.add_conditional_edges("chat_node", tools_condition, {"tools": "tool_node", "__end__": END})
            # After tool_node, go to parse_tool_output. If tool_node fails, end.
            graph_builder.add_edge("tool_node", "parse_jobs_node")
            # After parse_tool_output, if parsed_jobs is empty, go back to tool_node, else end.
            graph_builder.add_conditional_edges("parse_jobs_node", parse_jobs_condition, {"tool_node": "tool_node", "score_jobs_node": "score_jobs_node"})
            graph_builder.add_edge("score_jobs_node", END)
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

            print("Call resume agent")
            print("------------------------------------")           
            final_state = await agent.ainvoke({"messages": automate_prompt })
            print("------------------------------------")  
            print("finished call")
        except Exception  as e:
            print(f"Error while running the automated resume agent: {e}")
            return False
