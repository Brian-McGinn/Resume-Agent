from mcp.server.fastmcp import FastMCP
from services import job_scraper_service
from pydantic import BaseModel, Field

# Create the MCP server
mcp = FastMCP(
    name="Job Scraper",
    description="Provides support for getting the latest jobs posted by indeed and linkedin.",
    stateless_http=True, 
    port=3004
)

class job_scraper_request(BaseModel):
    search_term: str = Field(default="software engineer", description="Job title to search for")
    location: str = Field(default="Phoenix, AZ", description="Location of the job")
    results_wanted: int = Field(default=10, description="Number of job results to return")
    hours_old: int = Field(default=24, description="Maximum age of job postings in hours")
    country_indeed: str = Field(default="USA", description="Country for Indeed job search")

@mcp.tool()
def job_scraper_get_jobs(request: job_scraper_request = None) -> str:
    """
    Get a list of jobs from online job boards.

    Args:
      request (job_scraper_request): The request containing information needed to get the job list

    Returns:
      str: list of jobs in a json format
    """
    if request is None:
        # Call get_jobs with no parameters to use all defaults
        return job_scraper_service.get_jobs()
    else:
        return job_scraper_service.get_jobs(
            search_term=request.search_term,
            location=request.location,
            results_wanted=request.results_wanted,
            hours_old=request.hours_old,
            country_indeed=request.country_indeed
        )

@mcp.prompt()
def system_prompt() -> str:
    """System prompt description"""
    return """
    You are an AI assistant use the tools if needed.
    """

if __name__ == "__main__":
    mcp.run(transport="streamable-http")