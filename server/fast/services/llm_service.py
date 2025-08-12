from prompts.prompts import resume_revise_prompt, system_prompt, resume_review_prompt
from typing import Generator
from services.rag_service import get_context
from langchain_core.prompts import ChatPromptTemplate
from langchain_nvidia_ai_endpoints import ChatNVIDIA
LLM_MODEL = "nvidia/llama-3.3-nemotron-super-49b-v1"

class LLMService:
    def __init__(self):
        self.job_description = ""
        self.improvements = ""

    # Send the job description to the LLM and load the previously uploaded resume from the vectorstore into the context
    def send_message(self, message) -> Generator[str, None, None]:   
        """Handle message sending request."""
        try:
            context = get_context()
            prompt = ChatPromptTemplate.from_messages([system_prompt, resume_review_prompt]).format_messages(context=context, question=message)
            self.job_description = message
            response = ""
            print(f"Sending job description to LLM.")
            llm = ChatNVIDIA(model=LLM_MODEL, streaming=True) 
            for chunk in llm.stream(prompt):
                if chunk.content:
                    response += chunk.content
                    yield chunk.content 
            self.improvements = response
            print(f"Job comparison completed.")
            return response if response else None

        except Exception as e:
            print(f"Failed to llm {str(e)}")
            raise RuntimeError(f"Error getting AI response: {str(e)}")

    # Revise the resume based on the job description and the improvements from the LLM
    def revise_resume(self) -> Generator[str, None, None]:
        """Handle resume revision request."""
        try:
            context = get_context()
            prompt = ChatPromptTemplate.from_messages([system_prompt, resume_revise_prompt]).format_messages(resume=context, improvements = self.improvements, job_description=self.job_description)
            response = ""
            print(f"Revising resume.")
            llm = ChatNVIDIA(model=LLM_MODEL, streaming=True) 
            for chunk in llm.stream(prompt):
                if chunk.content:
                    response += chunk.content
                    yield chunk.content 
            print(f"Resume revised.")
            return response if response else None

        except Exception as e:
            print(f"Failed to llm {str(e)}")
            raise RuntimeError(f"Error getting AI response: {str(e)}")