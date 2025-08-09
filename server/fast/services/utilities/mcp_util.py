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
    
    async def get_prompt(self, prompt_name: str):
        prompt = await self.mcp_client.get_prompt(server_name="job_scraper", prompt_name=prompt_name)
        return prompt