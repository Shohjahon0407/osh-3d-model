import asyncio,json
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
async def main():
 p=StdioServerParameters(command='/home/shohjahon/.venvs/blender-mcp/bin/blender-mcp',env={'BLENDER_MCP_HOST':'127.0.0.1','BLENDER_MCP_PORT':'9876'})
 async with stdio_client(p) as (r,w):
  async with ClientSession(r,w) as s:
   await s.initialize();result=await s.list_tools()
   for t in result.tools:
    if 'screenshot' in t.name:print(t.name,json.dumps(t.inputSchema))
asyncio.run(main())
