import unittest
from job_scraper_service import job_scraper_service
import pandas as pd

class TestJobScraperService(unittest.TestCase):
    def test_get_jobs_returns_dataframe_row(self):
        # Call the get_jobs method with test parameters
        result = job_scraper_service.get_jobs(
            search_term="software engineer",
            location="Phoenix, AZ",
            results_wanted=1,
            hours_old=24,
            country_indeed="USA"
        )
        # The result should be a pandas Series (row of DataFrame)
        self.assertIsInstance(result, pd.DataFrame)
        # Check that some expected columns exist
        for _, row in result.iterrows():
            print(f"Validating job: {row["title"]}")
            self.assertNotEqual(row["id"], "", "Job id should not be an empty string")
            self.assertNotEqual(row["job_url"], "", "Job url should not be an empty string")
            self.assertNotEqual(row["title"], "", "Job title should not be an empty string")
            self.assertNotEqual(row["location"], "", "Job location should not be an empty string")
            self.assertNotEqual(row["description"], "", "Job description should not be an empty string")

if __name__ == "__main__":
    unittest.main()
