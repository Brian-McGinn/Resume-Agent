from langchain_mcp_adapters.client import MultiServerMCPClient

class MCPUtil():
    def __init__(self):
        self.mcp_client = MultiServerMCPClient({
                            "job_scraper": {
                                "url": "http://mcp-server:3004/mcp",
                                "transport": "streamable_http",
                            },})
        self.tools = None

    async def get_tools(self):
        try:
            self.tools = await self.mcp_client.get_tools()
        except Exception as e:
            print(f"Failed to connect to MCP server: {e}")
            raise
