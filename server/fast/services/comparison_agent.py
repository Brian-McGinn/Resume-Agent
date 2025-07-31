from pyexpat import model
from langchain_ollama.chat_models import ChatOllama
from prompts.prompts import system_prompt, generate_job_score_prompt
# from services.rag_service import log_to_langsmith
from langchain_core.prompts import ChatPromptTemplate
from services import models
from services.rag_service import get_context
import psycopg2

LLM_MODEL = "nvidia/llama-3.3-nemotron-super-49b-v1"

class ComparisonAgent:
    # Send the job description to the LLM and load the previously uploaded resume from the vectorstore into the context
    def generate_job_scores(self):
        scores = []
        jobs = get_all_jobs_from_postgres()
        resume = get_context()
        for job in jobs:
            description = job.get("description", "")
            if description != "":
                max_attempts = 5
                attempt = 0
                int_score = None
                while attempt < max_attempts:
                    job_score = self.job_score(' '.join(resume.split()), description)
                    try:
                        int_score = int(job_score.replace(" ", ""))
                        break
                    except ValueError:
                        attempt += 1
                        if attempt == max_attempts:
                            int_score = 0
                scores.append(models.jobs(title=job.get("title"), job_url=job.get("job_url"), score=int_score))
        sort_by_score = sorted(scores, key=lambda x: x.score, reverse=True)
        update_job_score_in_postgres(sort_by_score)
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

            return ' '.join(response.content)

        except Exception as e:
            print(f"Failed to call the llm {str(e)}")

def get_postgres_connection():
    """
    Establish and return a connection to the PostgreSQL database.
    """
    try:
        conn = psycopg2.connect(
            dbname="resume_agent",
            user="vector_admin",
            password="Resume_Pass",  # Change as appropriate
            host="pgvector-db",
            port=5432
        )
        return conn
    except Exception as e:
        print(f"Error connecting to postgres: {e}")
        raise

def get_all_jobs_from_postgres():
    """
    Retrieve all job records from the PostgreSQL jobs table and return as a JSON array.

    Returns:
        list: List of job dicts with all fields from the jobs table.
    """
    conn = None
    try:
        conn = get_postgres_connection()
        cur = conn.cursor()
        cur.execute("SELECT title, company, job_url, description, location, is_remote FROM jobs;")
        rows = cur.fetchall()
        jobs = []
        for row in rows:
            jobs.append({
                "title": row[0],
                "company": row[1],
                "job_url": row[2],
                "description": row[3],
                "location": row[4],
                "is_remote": row[5]
            })
        return jobs
    except Exception as e:
        print(f"Error retrieving jobs from postgres: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

def update_job_score_in_postgres(jobs_with_scores: models.jobs):
    """
    Update the score field in the jobs table for each job using job_url as the unique identifier.

    Args:
        jobs_with_scores (list): List of dicts, each containing at least 'job_url' and 'score'.
    """
    conn = None
    try:
        conn = get_postgres_connection()
        cur = conn.cursor()
        for job in jobs_with_scores:
            job_url = job.job_url
            score = job.score
            if job_url is not None and score is not None:
                cur.execute(
                    "UPDATE jobs SET score = %s WHERE job_url = %s;",
                    (score, job_url)
                )
        conn.commit()
    except Exception as e:
        print(f"Error updating job scores in postgres: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()
