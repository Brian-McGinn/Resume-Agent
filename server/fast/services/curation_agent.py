
from langgraph.graph import StateGraph, START, END
from services.rag_service import get_context
from services import models
from services.utilities.database_util import get_job_description, update_job_curated_resume
from typing_extensions import TypedDict
from langchain.schema.runnable import RunnableLambda
from langchain.prompts import ChatPromptTemplate
from prompts.prompts import (
    curate_system_prompt,
    curate_resume_step_1_compare,
    curate_resume_step_2_proofread,
    curate_resume_step_3_cross_check_original,
    curate_resume_step_4_format,
)
from langchain_nvidia_ai_endpoints import ChatNVIDIA
LLM_MODEL = "nvidia/llama-3.3-nemotron-super-49b-v1"

class CurationAgent:
    def create_graph(self):
        try:
            print("Creating LLM...")
            llm = ChatNVIDIA(model=LLM_MODEL, temperature=0.7, max_tokens=2048)

            # State Management
            class State(TypedDict):
                resume: str
                jobs: list[models.job]
                min_job_score: int

            def get_resume(state: State) -> State:
                print("Get latest resume from vector store.")
                state['resume'] = get_context()
                return state

            def get_job_data(state: State) -> State:
                print("Get list of non curated jobs.")
                state["jobs"] = get_job_description(state["min_job_score"])
                return state
            
            def curate(state: State) -> State:
                jobs = state["jobs"]
                if jobs and len(jobs) > 0:
                    curated_resumes = []
                    for job in jobs:
                        print(job.title)
                        content = self.curate_resume_llm(llm, state["resume"], job.description, job.recommendations)
                        job.curated_resume = content
                        update_job_curated_resume(job)
                        curated_resumes.append({
                            "job_url": job.job_url,
                            "curated_resume": job.curated_resume
                        })
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

    def curate_resume(self, min_job_score):
        """Handle job curation agent orchestration request."""
        try:
            agent = self.create_graph()

            print("Call resume curation agent")
            print("------------------------------------")           
            final_state = agent.invoke({"min_job_score": min_job_score})
            print("------------------------------------")  
            print("finished curation call")
            return final_state
        except Exception  as e:
            print(f"Error while running the curation resume agent: {e}")
            return False

    def curate_resume_llm(self, llm: ChatNVIDIA, resume: str, job_description: str, recommendations: str):
        # Chain with system_prompt at the start
        print(f"Begin the curation chain.")
        curation_chain_pipe = (
            ChatPromptTemplate.from_messages([curate_system_prompt, curate_resume_step_1_compare])
            | llm
            | RunnableLambda(lambda output1: {"curated_resume": output1.content})
            | ChatPromptTemplate.from_messages([curate_system_prompt, curate_resume_step_2_proofread])
            | llm
            | RunnableLambda(lambda output2: {"resume": resume, "curated_resume": output2.content})
            | ChatPromptTemplate.from_messages([curate_system_prompt, curate_resume_step_3_cross_check_original])
            | llm
            | RunnableLambda(lambda output3: {"curated_resume": output3.content})
            | ChatPromptTemplate.from_messages([curate_system_prompt, curate_resume_step_4_format])
            | llm
        )

        result = curation_chain_pipe.invoke({"resume": resume, "job_description": job_description, "recommendations": recommendations})
        content = result.content if hasattr(result, "content") else result
        return content
