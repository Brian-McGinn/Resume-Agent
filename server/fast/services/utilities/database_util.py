import psycopg2
from services import models
import os

def get_postgres_connection():
    """
    Establish and return a connection to the PostgreSQL database.
    """
    try:
        conn = psycopg2.connect(
            dbname=os.environ.get("POSTGRES_DB", "resume_agent"),
            user=os.environ.get("POSTGRES_USER", "vector_admin"),
            password=os.environ.get("POSTGRES_PASSWORD", "Resume_Pass"), 
            host="pgvector-db",
            port=5432
        )
        return conn
    except Exception as e:
        print(f"Error connecting to postgres: {e}")
        raise

def get_all_jobs():
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

def update_job_score(jobs_with_scores: models.job_comparisons):
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
            content = ' '.join(job.content.split())
            if job_url is not None and score is not None:
                cur.execute(
                    "UPDATE jobs SET score = %s, recommendations = %s WHERE job_url = %s;",
                    (score, content, job_url)
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

def get_job_description(min_job_score: int = 60) -> list[models.job]:
    """
    Retrieve job records from the PostgreSQL jobs table that are not curated and return as a JSON array.

    Returns:
        list: List of job dicts that are not curated and returns the title, job_url, description, and recommendations.
    """
    conn = None
    try:
        conn = get_postgres_connection()
        cur = conn.cursor()
        cur.execute("SELECT title, job_url, score, description, recommendations, curated FROM jobs WHERE curated = FALSE AND score > %s;", (min_job_score,))
        rows = cur.fetchall()
        jobs = []
        for row in rows:
            jobs.append(
                models.job(
                    title=row[0],
                    job_url=row[1],
                    score=row[2],
                    description=row[3],
                    recommendations=row[4],
                    curated=row[5]
                )
            )
        return jobs
    except Exception as e:
        print(f"Error retrieving jobs from postgres: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

def update_job_curated_resume(updated_job: models.job):
    """
    Update the curated_resume field in the jobs table using job_url as the unique identifier.

    Args:
        updated_job: job class, each containing at least 'job_url' and 'curated_resume'.
    """
    conn = None
    try:
        conn = get_postgres_connection()
        cur = conn.cursor()
        job_url = updated_job.job_url
        curated_resume = updated_job.curated_resume
        
        if job_url is not None and curated_resume is not None:
            cur.execute(
                "UPDATE jobs SET curated_resume = %s, curated = TRUE WHERE job_url = %s;",
                (curated_resume, job_url)
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

def get_jobs_table(limit: int=10):
    """
    Retrieve all job records from the PostgreSQL jobs table and return as a JSON array.

    Returns:
        list: List of job dicts with all fields from the jobs table.
    """
    conn = None
    try:
        conn = get_postgres_connection()
        cur = conn.cursor()
        # The parameter for LIMIT must be a tuple, even if it's a single value
        cur.execute("SELECT title, company, job_url, location, is_remote, curated, score FROM jobs ORDER BY score DESC LIMIT %s;", (limit,))
        rows = cur.fetchall()
        jobs = []
        for row in rows:
            jobs.append({
                "title": row[0],
                "company": row[1],
                "job_url": row[2],
                "location": row[3],
                "is_remote": row[4],
                "curated": row[5],
                "score": row[6]
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

def get_curated_resume(job_url: str):
    """
    Retrieve the curated resume string for a specific job from the PostgreSQL jobs table.

    Args:
        job_url (str): The unique URL identifier for the job.

    Returns:
        str or None: The curated_resume string for the specified job, or None if not found.
    """
    conn = None
    try:
        if not job_url or job_url == "":
            raise ValueError("job_url must not be empty or None")
        conn = get_postgres_connection()
        cur = conn.cursor()
        cur.execute("SELECT title, curated_resume FROM jobs WHERE job_url=%s;", (job_url,))
        row = cur.fetchone()
        if row is not None:
            return row[0], row[1]
        else:
            return None
    except Exception as e:
        print(f"Error retrieving jobs from postgres: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()