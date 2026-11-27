import json
import sys
import tempfile
import unittest
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class StdioTests(unittest.IsolatedAsyncioTestCase):
    async def test_read_only_session(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "d3d11_log.txt").write_text("[Hunting]\n  analyse_frame=F6\n")
            dump = root / "FrameAnalysis-2026-11-27-123456"
            dump.mkdir()
            (dump / "ib=00112233.txt").touch()

            server = Path(__file__).with_name("server.py")
            config = StdioServerParameters(
                command=sys.executable, args=[str(server), "--dll-root", temp],
            )
            async with stdio_client(config) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    self.assertIn("trigger_dump", {tool.name for tool in tools.tools})

                    bindings = await session.call_tool("get_bindings")
                    self.assertEqual(json.loads(bindings.content[0].text), {"analyse_frame": "F6"})

                    matches = await session.call_tool(
                        "search_hash", {"dump": dump.name, "query": "00112233"},
                    )
                    self.assertFalse(matches.isError)
                    self.assertIn("ib=00112233.txt", str(matches.content))

                    refused = await session.call_tool("trigger_dump", {"timeout_seconds": 0})
                    self.assertTrue(refused.isError)
                    self.assertIn("must have focus", str(refused.content))
