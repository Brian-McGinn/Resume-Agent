from langchain_nvidia_ai_endpoints import ChatNVIDIA
from prompts.prompts import resume_revise_prompt, system_prompt, resume_review_prompt
from typing import Generator
from services.rag_service import log_to_langsmith
from services.rag_service import get_context
from langchain_core.prompts import ChatPromptTemplate
LLM_MODEL = "google/gemma-3n-e4b-it"

class LLMService:
    def __init__(self):
        # self.history = []
        self.job_description = ""
        self.improvements = ""

    
    def send_message(self, message) -> Generator[str, None, None]:   
        """Handle message sending request."""
        try:
            # Truncate the input message to prevent token limit issues
            context = get_context()
            prompt = ChatPromptTemplate.from_messages([system_prompt, resume_review_prompt]).format_messages(context=context, question=message)
            # self.history.append(prompt)
            self.job_description = message
            response = ""
            log_to_langsmith(f"Sending job description to LLM.")
            llm = ChatNVIDIA(model=LLM_MODEL, streaming=True) # mistralai/mixtral-8x22b-instruct-v0.1 or google/gemma-3n-e4b-it or nvidia/llama-3.3-nemotron-super-49b-v1
            for chunk in llm.stream(prompt):
                if chunk.content:
                    response += chunk.content
                    yield chunk.content 
            # self.history.append({"role": "user", "content": message})
            # self.history.append({"role": "assistant", "content": response})
            self.improvements = response
            log_to_langsmith(f"Job comparison completed.")
            return response if response else None

        except Exception as e:
            print(f"Failed to llm {str(e)}")
            raise RuntimeError(f"Error getting AI response: {str(e)}")

    def revise_resume(self) -> Generator[str, None, None]:
        """Handle resume revision request."""
        try:
            context = get_context()
            prompt = ChatPromptTemplate.from_messages([system_prompt, resume_revise_prompt]).format_messages(resume=context, improvements = self.improvements, job_description=self.job_description)
            response = ""
            log_to_langsmith(f"Revising resume.")
            llm = ChatNVIDIA(model=LLM_MODEL, streaming=True) # mistralai/mixtral-8x22b-instruct-v0.1 or google/gemma-3n-e4b-it or nvidia/llama-3.3-nemotron-super-49b-v1
            for chunk in llm.stream(prompt):
                if chunk.content:
                    response += chunk.content
                    yield chunk.content 
            # self.history.append({"role": "user", "content": "Revise the resume based on the chat history and job description."})
            # self.history.append({"role": "assistant", "content": response})
            log_to_langsmith(f"Resume revised.")
            return response if response else None

        except Exception as e:
            print(f"Failed to llm {str(e)}")
            raise RuntimeError(f"Error getting AI response: {str(e)}")