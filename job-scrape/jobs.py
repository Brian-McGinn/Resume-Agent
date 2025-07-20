from mcp.server.fastmcp import FastMCP

from jobspy import scrape_jobs
import pandas as pd
import io

mcp = FastMCP(
    name="Get Jobs MCP Server",
    description="An MCP server running with SSE transport to get a list of jobs based on parameters.",
    port=3002
)

@mcp.tool
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
    first_row_df = pd.read_csv(io.StringIO(csv_string), nrows=1)
    first_row = first_row_df.iloc[0]

    return first_row


# def main():
#     jobs = get_jobs("solution architect" )
#     print(f"id: {jobs['id']}")
#     print(f"job_url: {jobs['job_url']}")
#     print(f"title: {jobs['title']}")
#     print(f"location: {jobs['location']}")
#     print(f"description: {jobs['description']}")

if __name__ == "__main__":
    mcp.run(transport="sse")