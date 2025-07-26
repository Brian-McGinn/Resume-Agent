from jobspy import scrape_jobs
import pandas as pd
import io

def get_jobs(search_term: str ="software engineer", location: str = "Phoenix, AZ", results_wanted: int = 10, hours_old: int = 24, country_indeed: str = 'USA'):
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
            "description": str(row.get("description", "")),
            "location": str(row.get("location", "")),
            "is_remote": str(row.get("is_remote", ""))
        })

    return jobs_json
