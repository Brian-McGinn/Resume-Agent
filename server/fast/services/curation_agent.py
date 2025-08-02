
from langchain_ollama.chat_models import ChatOllama
from langgraph.graph import StateGraph, START, END
from services.rag_service import get_context
from services import models
from services.database_service import get_job_description, update_job_curated_resume
from typing_extensions import TypedDict
from langchain.schema.runnable import RunnableLambda
from langchain.prompts import ChatPromptTemplate
from prompts.prompts import (
    system_prompt,
    curate_resume_step_1_compare,
    curate_resume_step_2_highlight,
    curate_resume_step_3_proofread,
    curate_resume_step_4_cross_check_original,
    curate_resume_step_5_format,
)

class CurationAgent:
    def create_graph(self, min_job_score: int = 60):
        try:
            print("Creating Ollama LLM...")
            # Create Ollama-based LLM (using llama3)
            llm = ChatOllama(model="llama3.1", base_url="http://host.docker.internal:11434")

            # State Management
            class State(TypedDict):
                resume: str
                jobs: list[models.job]

            def get_resume(state: State) -> State:
                print("Get latest resume from vector store.")
                state['resume'] = get_context()
                return state

            def get_job_data(state: State) -> State:
                print("Get list of non curated jobs.")
                state["jobs"] = get_job_description(min_job_score)
                return state
            
            def curate(state: State) -> State:
                jobs = state["jobs"]
                if jobs and len(jobs) > 0:
                    curated_resumes = []
                    for job in jobs:
                        response = curate_resume_llm(llm, state["resume"], job.description, job.recommendations)
                        job.curated_resume = response.content
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

    def curate_resume(self):
        """Handle job curation agent orchestration request."""
        try:
            agent = self.create_graph()

            print("Call resume curation agent")
            print("------------------------------------")           
            final_state = agent.invoke({})
            print("------------------------------------")  
            print("finished curation call")
            return final_state
        except Exception  as e:
            print(f"Error while running the curation resume agent: {e}")
            return False

def curate_resume_llm(llm: ChatOllama, resume: str, job_description: str, recommendations: str):
    # Chain with system_prompt at the start
    curation_chain_pipe = (
        ChatPromptTemplate.from_messages([system_prompt, curate_resume_step_1_compare]) 
        | llm 
        | RunnableLambda(lambda output1: {"resume": resume, "job_description": job_description, "curated_resume": output1.content}) 
        | ChatPromptTemplate.from_messages([system_prompt, curate_resume_step_2_highlight]) 
        | llm 
        | RunnableLambda(lambda output2: {"curated_resume": output2.content}) 
        | ChatPromptTemplate.from_messages([system_prompt, curate_resume_step_3_proofread]) 
        | llm 
        | RunnableLambda(lambda output3: {"curated_resume": output3.content, "resume": resume}) 
        | ChatPromptTemplate.from_messages([system_prompt, curate_resume_step_4_cross_check_original]) 
        | llm 
        | RunnableLambda(lambda output4: {}) 
        | ChatPromptTemplate.from_messages([system_prompt, curate_resume_step_5_format]) 
        | llm
    )

    return curation_chain_pipe.invoke({"resume": resume, "job_description": job_description, "recommendations": recommendations})