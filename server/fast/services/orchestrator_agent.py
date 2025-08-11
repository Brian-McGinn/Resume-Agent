from prompts.prompts import automate_prompt, system_prompt
from services.utilities.mcp_util import MCPUtil
from services.comparison_agent import ComparisonAgent
from services.curation_agent import CurationAgent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import ToolMessage
import json
from typing import List, Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import AnyMessage, add_messages
from .utilities.database_util import get_jobs_table
from langchain_nvidia_ai_endpoints import ChatNVIDIA
LLM_MODEL = "nvidia/llama-3.3-nemotron-super-49b-v1"

class AgentService:
    async def create_graph(self):
        try:
            print("Creating LLM...")
            llm = ChatNVIDIA(model=LLM_MODEL)
            mcp_client = MCPUtil()
            await mcp_client.get_tools()

            print("Binding tools to LLM...")
            llm_with_tool = llm.bind_tools(mcp_client.tools)

            print("Creating prompt template...")
            prompt_template = ChatPromptTemplate.from_messages([
                system_prompt,
                MessagesPlaceholder("messages")
            ])
            chat_llm = prompt_template | llm_with_tool

            # State Management
            class State(TypedDict):
                messages: Annotated[List[AnyMessage], add_messages]
                parsed_jobs: dict
                job_scores: dict
                curated_resume: dict
                min_job_score: int

            # Nodes
            def chat_node(state: State) -> State:
                print("Use the job scraper service to get the latest jobs.")
                state["messages"] = chat_llm.invoke({"messages": state["messages"]})
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
                    state["job_scores"] = sort_by_score
                    return state
                except Exception as e:
                    print(f"Error in score_jobs_node: {e}")
                    import traceback
                    traceback.print_exc()
                    return state
                
            def curate_resume_node(state: State):
                """
                Node to curate the resume using the CurationAgent.
                """
                try:
                    print("curate Agent")
                    curation_agent = CurationAgent()
                    curated_resume = curation_agent.curate_resume(state["min_job_score"])
                    state["curated_resume"] = curated_resume
                    return state
                except Exception as e:
                    print(f"Error in curate_resume_node: {e}")
                    import traceback
                    traceback.print_exc()
                    return state

            print("Building graph...")
            # Building the graph
            graph_builder = StateGraph(State)
            #Create graph nodes
            graph_builder.add_node("chat_node", chat_node)
            graph_builder.add_node("tool_node", ToolNode(tools=mcp_client.tools))
            graph_builder.add_node("parse_jobs_node", parse_tool_json)
            graph_builder.add_node("score_jobs_node", score_jobs_node)
            graph_builder.add_node("curate_resume_node", curate_resume_node)
            #Create graph edges
            graph_builder.add_edge(START, "chat_node")
            # If tools are needed, go to tool_node; otherwise, end.
            graph_builder.add_conditional_edges("chat_node", tools_condition, {"tools": "tool_node", "__end__": END})
            # After tool_node, go to parse_tool_output. If tool_node fails, end.
            graph_builder.add_edge("tool_node", "parse_jobs_node")
            # After parse_tool_output, if parsed_jobs is empty, go back to tool_node, else end.
            graph_builder.add_conditional_edges("parse_jobs_node", parse_jobs_condition, {"tool_node": "tool_node", "score_jobs_node": "score_jobs_node"})
            graph_builder.add_edge("score_jobs_node", "curate_resume_node")
            graph_builder.add_edge("curate_resume_node", END)
            graph = graph_builder.compile()
            print("Graph created successfully")
            return graph
        except Exception as e:
            print(f"Error in create_graph: {str(e)}")
            import traceback
            traceback.print_exc()
            raise

    async def automate(self, search_term: str = "software engineer", location: str = "", results_wanted: int = 10, hours_old: int = 24, country_indeed: str = "USA", min_job_score: int = 60):
        """Handle automated agent orchestration request."""
        try:
            agent = await self.create_graph()

            print("Call resume agent")
            print("------------------------------------")           
            final_state = await agent.ainvoke({"min_job_score": min_job_score, "messages": [automate_prompt.format(search_term=search_term, 
                                                                                    location=location, 
                                                                                    results_wanted=results_wanted, 
                                                                                    hours_old=hours_old, 
                                                                                    country_indeed=country_indeed)],})
            print("------------------------------------")  
            print("finished call")
            return get_jobs_table()
        except Exception  as e:
            print(f"Error while running the automated resume agent: {e}")
            return []
