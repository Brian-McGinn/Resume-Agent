from langchain_ollama.chat_models import ChatOllama
from prompts.prompts import system_prompt, generate_job_score_prompt
# from services.rag_service import log_to_langsmith
from langchain_core.prompts import ChatPromptTemplate
from services import models
import json
LLM_MODEL = "nvidia/llama-3.3-nemotron-super-49b-v1"

class ComparisonAgent:
    # Send the job description to the LLM and load the previously uploaded resume from the vectorstore into the context
    def generate_job_score(self, resume, description):   
        """Handle message sending request."""
        try:
            print("------------- generate job score")
            prompt = ChatPromptTemplate.from_messages([system_prompt, generate_job_score_prompt]).format_messages(context=resume, question=description)
            print("------------- we have a prompt")
            response = ""

            llm = ChatOllama(model="llama3.1", base_url="http://host.docker.internal:11434")
            response = llm.invoke(prompt)

            return ' '.join(response.content)

        except Exception as e:
            print(f"Failed to call the llm {str(e)}")
            raise RuntimeError(f"Error getting AI response: {str(e)}")