
from langchain_ollama.chat_models import ChatOllama
from langgraph.graph import StateGraph, START, END
from langchain_core.prompts import ChatPromptTemplate
from prompts.prompts import resume_revise_prompt, system_prompt
from services.rag_service import get_context
from services import models
from services.database_service import get_job_description, update_job_curated_resume
from typing_extensions import TypedDict

class CurationAgent:
    async def create_graph(self):
        try:
            print("Creating Ollama LLM...")
            # Create Ollama-based LLM (using llama3)
            llm = ChatOllama(model="llama3.1", base_url="http://host.docker.internal:11434")

            # State Management
            class State(TypedDict):
                resume: str
                jobs: list[models.job]

            def get_resume(state: State) -> State:
                state['resume'] = get_context()
                return state

            def get_job_data(state: State) -> State:
                state["jobs"] = get_job_description()
                return state
            
            def curate(state: State) -> State:
                jobs = state["jobs"]
                if jobs and len(jobs) > 0:
                    curated_resumes = []
                    for job in jobs:
                        if job and job.recommendations:
                            prompt = ChatPromptTemplate.from_messages([system_prompt, resume_revise_prompt]).format_messages(
                                resume=state["resume"],
                                improvements=job.recommendations,
                                job_description=job.description
                            )
                            response = llm.invoke(prompt)
                            job.curated_resume = response.content
                            update_job_curated_resume(job)
                            curated_resumes.append({
                                "job_url": job.job_url,
                                "curated_resume": response.content
                            })
                        else:
                            print(f"No recommendations found for job: {getattr(job, 'title', 'Unknown')}")
                    state["curated_resumes"] = curated_resumes
                else:
                    print("No jobs found for curation")
                return state

            print("Building graph...")
            # Building the graph
            graph = StateGraph(State)

            # Create graph nodes
            graph.add_node("get_resume_node", get_resume)
            graph.add_node("get_job_data_node", get_job_data)
            graph.add_node("curate_node", curate)

            # Create graph edges
            graph.add_edge(START, "get_resume_node")
            graph.add_edge("get_resume_node", "get_job_data_node")
            graph.add_edge("get_job_data_node", "curate_node")
            graph.add_edge("curate_node", END)

            # Compile graph
            graph = graph.compile()
            print("Graph created successfully")
            return graph
        except Exception as e:
            print(f"Error in create_graph: {str(e)}")
            import traceback
            traceback.print_exc()
            raise

    async def curate_resume(self):
        """Handle job curation agent orchestration request."""
        try:
            agent = await self.create_graph()

            print("Call resume curation agent")
            print("------------------------------------")           
            final_state = await agent.ainvoke({})
            print("------------------------------------")  
            print("finished curation call")
            return final_state
        except Exception  as e:
            print(f"Error while running the curation resume agent: {e}")
            return False

