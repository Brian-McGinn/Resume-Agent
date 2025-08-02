import psycopg2
from services import models

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

def get_job_description() -> list[models.job]:
    """
    Retrieve job records from the PostgreSQL jobs table that are not curated and return as a JSON array.

    Returns:
        list: List of job dicts that are not curated and returns the title, job_url, description, and recommendations.
    """
    conn = None
    try:
        conn = get_postgres_connection()
        cur = conn.cursor()
        cur.execute("SELECT title, job_url, description, recommendations, curated FROM jobs WHERE curated = FALSE;")
        rows = cur.fetchall()
        jobs = []
        for row in rows:
            jobs.append(
                models.job(
                    title=row[0],
                    job_url=row[1],
                    description=row[2],
                    recommendations=row[3],
                    curated=row[4]
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