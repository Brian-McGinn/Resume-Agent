from jobspy import scrape_jobs
import pandas as pd
import io
import psycopg2

def get_jobs(search_term: str = "software engineer", location: str = "Phoenix, AZ", results_wanted: int = 10, hours_old: int = 24, country_indeed: str = 'USA'):
    jobs = scrape_jobs(
        site_name=["indeed"],
        search_term=search_term,
        location=location,
        results_wanted=results_wanted,
        hours_old=hours_old,
        country_indeed=country_indeed,
    )

    csv_buffer = io.StringIO()
    jobs.to_csv(csv_buffer, index=False) # index=False prevents writing the DataFrame index
    csv_string = csv_buffer.getvalue()
    job_df = pd.read_csv(io.StringIO(csv_string))
    jobs_json = []
    for _, row in job_df.iterrows():
        jobs_json.append({
            "title": str(row.get("title", "")),
            "company": str(row.get("company", "")),
            "job_url": str(row.get("job_url", "")),
        })
    
    save_jobs_to_postgres(job_df)
    
    return jobs_json

def save_jobs_to_postgres(job_df):
    """
    Save an array of job JSON objects to the PostgreSQL jobs table.

    Args:
        jobs_json (list): List of job dicts with keys: title, company, job_url, description, location, is_remote.
        db_conn_params (dict, optional): Dictionary with connection params (dbname, user, password, host, port).
                                         If None, uses default localhost connection.
    """
    conn = None
    try:
        conn = psycopg2.connect(
            dbname="resume_agent",
            user="vector_admin",
            password="Resume_Pass",  # Change as appropriate
            host="pgvector-db",
            port=5432
        )
        cur = conn.cursor()
        insert_query = """
            INSERT INTO jobs (title, company, job_url, description, location, is_remote)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (job_url) DO UPDATE
            SET title = EXCLUDED.title,
                company = EXCLUDED.company,
                description = EXCLUDED.description,
                location = EXCLUDED.location,
                is_remote = EXCLUDED.is_remote
        """
        for _, job in job_df.iterrows():
            raw_description = job.get("description", "")
            description = ' '.join(raw_description.split())
            cur.execute(
                insert_query,
                (
                    job.get("title", ""),
                    job.get("company", ""),
                    job.get("job_url", ""),
                    description,
                    job.get("location", ""),
                    job.get("is_remote", "False") in ["True", "true", True, 1]
                )
            )
        conn.commit()
        cur.close()
    except Exception as e:
        print(f"Error saving jobs to postgres: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()
