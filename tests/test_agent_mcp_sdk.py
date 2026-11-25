"""Real MCP SDK discovery and tool calls, not a mocked JSON-RPC interface."""
import asyncio
import shutil
from unittest.mock import patch
import unittest

try:
    from mcp import Client
    from agent_mcp import server as adapter
except ImportError:
    Client = None
    adapter = None


@unittest.skipUnless(Client is not None, "Install optional MCP SDK to run integration")
class AgentMcpSdkTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "Optional Node authoring tool")
    def test_generation_uses_canonical_engine_and_bounded_results(self):
        from scripts.generate_ui import generate
        request = {"release": "0.3.0-alpha.5", "title": "CRM",
                   "theme": "noir", "requirements": ["pipeline", "metrics"]}
        async def run():
            async with Client(adapter.server) as client:
                listing = await client.list_tools()
                tool = next((t for t in listing.tools if t.name == "generate_ui"), None)
                self.assertIsNotNone(tool)
                self.assertIs(tool.annotations.read_only_hint, True)
                result = await client.call_tool("generate_ui", {"request": request})
                self.assertFalse(result.is_error)
                self.assertEqual(result.structured_content, generate(request))
                self.assertEqual(result.structured_content["validation"]["diagnostics"], [])
                blocked = await client.call_tool("generate_ui", {"request":
                    {**request, "requirements": ["pipeline", "live-map"]}})
                self.assertFalse(blocked.is_error)
                self.assertEqual(blocked.structured_content["status"], "blocked")
                self.assertNotIn("output", blocked.structured_content)
                invalid = await client.call_tool("generate_ui", {"request":
                    {**request, "release": "0.3.0-alpha.4"}})
                self.assertTrue(invalid.is_error)
                oversized = await client.call_tool("generate_ui", {"request":
                    {**request, "description": "x" * (256 * 1024 + 1)}})
                self.assertTrue(oversized.is_error)
                with patch.object(adapter, "MAX_GENERATION_RESPONSE_BYTES", 1):
                    limited = await client.call_tool("generate_ui", {"request": request})
                    self.assertTrue(limited.is_error)
                    self.assertNotIn("<!doctype html>", str(limited.content).lower())
        asyncio.run(run())

    def test_mcp_tools_are_discoverable_and_use_published_api(self):
        self.assertTrue(hasattr(adapter, "server"))
        async def run():
            async with Client(adapter.server) as client:
                listing = await client.list_tools()
                names = {tool.name for tool in listing.tools}
                self.assertGreaterEqual(names, {
                    "search_components", "get_component", "lookup_api",
                    "get_theme_tokens", "validate_markup", "get_interaction_contracts",
                    "get_interaction_recipes", "validate_composition",
                })
                contracts = await client.call_tool("get_interaction_contracts", {
                    "name": "dialog", "release": "0.3.0-alpha.5",
                })
                self.assertFalse(contracts.is_error)
                self.assertEqual(contracts.structured_content["contracts"][0]["id"], "dialog")
                recipes = await client.call_tool("get_interaction_recipes", {
                    "contract": "combobox", "release": "0.3.0-alpha.5",
                })
                self.assertFalse(recipes.is_error)
                self.assertEqual({r["id"] for r in recipes.structured_content["recipes"]},
                                 {"native-select", "react-aria-combobox"})
                plan = await client.call_tool("validate_composition", {
                    "section_ids": ["hero-product"], "interactions": [],
                    "stylesheets": ["syntyr.core.css"], "release": "0.3.0-alpha.5",
                })
                self.assertFalse(plan.is_error)
                self.assertFalse(plan.structured_content["valid"])
                self.assertEqual(plan.structured_content["missing_stylesheets"], ["syntyr.recipes.css"])
                plan_valid = await client.call_tool("validate_composition", {
                    "section_ids": ["hero-product"], "interactions": [],
                    "stylesheets": ["syntyr.core.css", "syntyr.recipes.css"],
                    "release": "0.3.0-alpha.5",
                })
                self.assertFalse(plan_valid.is_error)
                self.assertTrue(plan_valid.structured_content["valid"])
                unavailable_recipes = await client.call_tool("get_interaction_recipes", {})
                self.assertTrue(unavailable_recipes.is_error)
                unavailable = await client.call_tool("get_interaction_contracts", {})
                self.assertTrue(unavailable.is_error)
                result = await client.call_tool("lookup_api", {
                    "name": "syn-button--primary", "release": "0.3.0-alpha.4",
                })
                self.assertFalse(result.is_error)
                structured = result.structured_content
                self.assertEqual(structured["release_status"], "published")
                self.assertEqual(structured["entry"]["stylesheet"], "syntyr.core.css")
                invalid = await client.call_tool("get_component", {
                    "name": "Form compositions", "release": "0.3.0-alpha.4",
                })
                self.assertTrue(invalid.is_error)
                self.assertIn("unavailable", str(invalid.content).lower())
                check = await client.call_tool("validate_markup", {
                    "html": '<button class="syn-buttn" data-syn-theme="industrial">Go</button>',
                    "release": "0.3.0-alpha.4", "stylesheets": ["syntyr.core.css"],
                })
                self.assertFalse(check.is_error)
                result = check.structured_content
                self.assertEqual(result["unknown_classes"], ["syn-buttn"])
                self.assertEqual({d["code"] for d in result["diagnostics"]},
                                 {"unknown-class", "invalid-attribute-value"})
                typo = next(d for d in result["diagnostics"] if d["code"] == "unknown-class")
                self.assertIn("syn-button", [s["name"] for s in typo["suggestions"]])
                for tool in listing.tools:
                    self.assertIs(tool.annotations.read_only_hint, True)
        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
