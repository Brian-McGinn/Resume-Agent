from jobspy import scrape_jobs
import pandas as pd
import io

class job_scraper_service:
    def get_jobs(search_term: str ="software engineer", location: str = "Phoenix, AZ", results_wanted: int = 10, hours_old: int = 24, country_indeed: str = 'USA'):
        jobs = scrape_jobs(
            site_name=["indeed", "linkedin"],
            search_term=search_term,
            location=location,
            results_wanted=results_wanted,
            hours_old=hours_old,
            country_indeed=country_indeed,
        )
        print(f"Found {len(jobs)} jobs")

        csv_buffer = io.StringIO()
        jobs.to_csv(csv_buffer, index=False) # index=False prevents writing the DataFrame index
        csv_string = csv_buffer.getvalue()
        job_df = pd.read_csv(io.StringIO(csv_string))

        return job_df
