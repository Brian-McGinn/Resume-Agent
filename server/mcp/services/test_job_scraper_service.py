import unittest
from job_scraper_service import get_jobs

class TestJobScraperService(unittest.TestCase):
    def test_get_jobs_returns_dataframe_row(self):
        # Call the get_jobs method with test parameters
        result = get_jobs(
            search_term="software engineer",
            location="Phoenix, AZ",
            results_wanted=1,
            hours_old=24,
            country_indeed="USA"
        )
        # The result should be a pandas Series (row of DataFrame)
        self.assertIsInstance(result, list)
        self.assertTrue(len(result) > 0, "Result should not be empty")
        # Check that some expected columns exist
        for row in result:
            print(row["title"])
            self.assertNotEqual(row["title"], "", "Job title should not be an empty string")
            self.assertNotEqual(row["company"], "", "Company should not be an empty string")
            self.assertNotEqual(row["job_url"], "", "Job url should not be an empty string")
            # self.assertNotEqual(row["location"], "", "Job location should not be an empty string")
            # self.assertNotEqual(row["is_remote"], "", "Is remote should not be an empty string")
            # self.assertNotEqual(row["description"], "", "Job description should not be an empty string")

if __name__ == "__main__":
    unittest.main()
