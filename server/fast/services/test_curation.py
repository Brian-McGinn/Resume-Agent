import asyncio
import sys
import os

# Add the project root to the path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from services.curation_agent import CurationAgent

if __name__ == "__main__":
    agent = CurationAgent()
    response = agent.curate_resume()
    print(response)
