from pyexpat import model
from langchain_ollama.chat_models import ChatOllama
from prompts.prompts import system_prompt, generate_job_score_prompt
# from services.rag_service import log_to_langsmith
from langchain_core.prompts import ChatPromptTemplate
from services import models
from services.rag_service import get_context
from services.database_service import get_all_jobs, update_job_score
import psycopg2
import json

LLM_MODEL = "nvidia/llama-3.3-nemotron-super-49b-v1"

class ComparisonAgent:
    # Send the job description to the LLM and load the previously uploaded resume from the vectorstore into the context
    def generate_job_scores(self):
        scores = []
        recommendations = []
        jobs = get_all_jobs()
        resume = get_context()
        for job in jobs:
            description = job.get("description", "")
            if description != "":
                max_attempts = 5
                attempt = 0
                while attempt < max_attempts:
                    job_score = self.job_score(' '.join(resume.split()), description)
                    try:
                        # Parse the job_score as JSON
                        print(job_score)
                        job_score_json = json.loads(job_score)
                        score_val = job_score_json.get("score", 0)
                        content_val = job_score_json.get("content", "")
                        print(f"Job: {job.get('title')}")
                        print(f"Score: {score_val}")
                        print(f"Explanation: {content_val}")
                        scores.append(models.job(title=job.get("title"), job_url=job.get("job_url"), score=score_val))
                        # Append a new job_comparisons entry using models.job_comparisons and job_score/job fields
                        recommendations.append(
                            models.job_comparisons(
                                job_url=job.get("job_url"),
                                score=score_val,
                                content=content_val
                            )
                        )
                        break
                    except (ValueError, json.JSONDecodeError, TypeError) as e:
                        print(f"Failed to parse job_score or convert score to int: {e}")
                        attempt += 1
        sort_by_score = sorted(scores, key=lambda x: x.score, reverse=True)
        update_job_score(recommendations)
        return sort_by_score

    def job_score(self, resume, description):   
        """Handle message sending request."""
        try:
            print("------------- generate job score")
            prompt = ChatPromptTemplate.from_messages([system_prompt, generate_job_score_prompt]).format_messages(context=resume, question=description)
            print("------------- we have a prompt")
            response = ""

            llm = ChatOllama(model="llama3.1", base_url="http://host.docker.internal:11434")
            response = llm.invoke(prompt)

            return response.content

        except Exception as e:
            print(f"Failed to call the llm {str(e)}")
