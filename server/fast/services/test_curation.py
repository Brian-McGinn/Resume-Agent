# import asyncio
# import sys
# import os

# # Add the project root to the path
# project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# sys.path.insert(0, project_root)

# from .curation_agent import CurationAgent

# if __name__ == "__main__":
#     agent = CurationAgent()
#     response = agent.curate_resume(59)
#     # print(response)
#     # print("!!!!!!!!!!!!!!!")
#     # print(response.get("resume"))


import sys
import os
import asyncio

# Add the parent directory to the path so that 'services' can be imported as a top-level module
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from .utilities.mcp_util import MCPService

async def main():
    mcp_server = MCPService()
    prompt = mcp_server.get_prompt("system_prompt")
    if asyncio.iscoroutine(prompt):
        prompt = await prompt
    print(prompt)

if __name__ == "__main__":
    asyncio.run(main())