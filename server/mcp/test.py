from mcp import ClientSession
import asyncio
from mcp.client.streamable_http import streamablehttp_client

# Math server
math_server_url = "http://localhost:3004/mcp"

async def main():
    async with streamablehttp_client(math_server_url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            # List available tools
            response = await session.list_tools()
            print("\n/////////////////tools//////////////////")
            for tool in response.tools:
                print(tool)

if __name__ == "__main__":
    asyncio.run(main())