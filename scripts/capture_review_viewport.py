import asyncio,base64,pathlib,sys
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
async def main():
 p=StdioServerParameters(command='/home/shohjahon/.venvs/blender-mcp/bin/blender-mcp',env={'BLENDER_MCP_HOST':'127.0.0.1','BLENDER_MCP_PORT':'9876'})
 async with stdio_client(p) as (r,w):
  async with ClientSession(r,w) as s:
   await s.initialize();result=await s.call_tool('get_screenshot_of_area_as_image',{'area_ui_type':'VIEW_3D','size_limit_in_bytes':1800000})
   for block in result.content:
    if block.type=='image':
     path=pathlib.Path(sys.argv[1]);path.write_bytes(base64.b64decode(block.data));print('VIEWPORT_SAVED',path)
    elif block.type=='text': print(block.text[:1500])
asyncio.run(main())
