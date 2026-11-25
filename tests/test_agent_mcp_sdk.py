"""Real MCP SDK discovery and tool calls, not a mocked JSON-RPC interface."""
import asyncio
import os
import unittest

try:
    from mcp import Client
    from agent_mcp import server as adapter
except ImportError:
    Client = None
    adapter = None


@unittest.skipUnless(Client is not None, "Install optional MCP SDK to run integration")
class AgentMcpSdkTests(unittest.TestCase):
    def test_mcp_tools_are_discoverable_and_use_published_api(self):
        self.assertTrue(hasattr(adapter, "server"))
        async def run():
            async with Client(adapter.server) as client:
                listing = await client.list_tools()
                names = {tool.name for tool in listing.tools}
                self.assertGreaterEqual(names, {
                    "search_components", "get_component", "lookup_api",
                    "get_theme_tokens", "validate_markup", "get_interaction_contracts",
                    "get_interaction_recipes", "inspect_markup", "plan_variant_changes",
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
                published_inspect = await client.call_tool("inspect_markup", {
                    "html": "<p>Hi</p>", "release": "0.3.0-alpha.4",
                })
                self.assertTrue(published_inspect.is_error)
                if os.environ.get("SYNTYR_HTML_INSPECTOR"):
                    inspected = await client.call_tool("inspect_markup", {
                        "html": '<button class="syn-button">Go</button>',
                        "release": "0.3.0-alpha.5", "selector": "button",
                    })
                    self.assertFalse(inspected.is_error)
                    self.assertEqual(inspected.structured_content["elements"][0]["components"], ["Button"])
                    html = '<button class="syn-button syn-button--primary">Go</button>'
                    snapshot = await client.call_tool("inspect_markup", {
                        "html": html, "release": "0.3.0-alpha.5", "selector": "button",
                    })
                    report = snapshot.structured_content
                    request = {"html": html, "release": "0.3.0-alpha.5",
                               "document_sha256": report["document_sha256"],
                               "operations": [{"element_id": report["elements"][0]["element_id"],
                                               "selector": "button", "from": "syn-button--primary",
                                               "to": "syn-button--outline"}]}
                    plan = await client.call_tool("plan_variant_changes", request)
                    self.assertFalse(plan.is_error)
                    self.assertTrue(plan.structured_content["preview_only"])
                    self.assertEqual(plan.structured_content["changes"][0]["after"], "syn-button syn-button--outline")
                    request["operations"] *= 2
                    duplicate = await client.call_tool("plan_variant_changes", request)
                    self.assertTrue(duplicate.is_error)
                for tool in listing.tools:
                    self.assertIs(tool.annotations.read_only_hint, True)
        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
