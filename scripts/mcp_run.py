"""Run a local Python script in the open Blender through the MCP protocol."""
import asyncio
import json
import pathlib
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    code = pathlib.Path(sys.argv[1]).read_text()
    params = StdioServerParameters(
        command='/home/shohjahon/.venvs/blender-mcp/bin/blender-mcp',
        env={'BLENDER_MCP_HOST': '127.0.0.1', 'BLENDER_MCP_PORT': '9876'},
    )
    async with stdio_client(params) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            response = await session.call_tool('execute_blender_code', {'code': code})
            for block in response.content:
                if block.type == 'text':
                    print(block.text)
                    payload = json.loads(block.text)
                    if payload.get('status') == 'error':
                        raise RuntimeError(payload.get('message'))
            if response.isError:
                raise RuntimeError('MCP tool failed')


asyncio.run(main())
