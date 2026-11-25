"""Optional local MCP server for Syntyr's published CSS API.

Install the official MCP Python SDK separately; the @syntyr/css npm package,
CSS assets, website, and build never import this adapter.
"""
from __future__ import annotations

from typing import Any

from mcp.server import MCPServer
from mcp.types import ToolAnnotations
from mcp.server.mcpserver.exceptions import ToolError

from .catalog import CatalogError, SyntyrCatalog, PUBLISHED

catalog = SyntyrCatalog()
READ_ONLY = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False)


def checked(method, *args):
    try:
        return method(*args)
    except CatalogError as error:
        # Expected invalid release/component input is a client-visible tool
        # error, not a hidden stack trace or a fabricated result.
        raise ToolError(str(error)) from None
server = MCPServer("Syntyr CSS", instructions=(
    "Read-only CSS component reference. Pin release explicitly. "
    "Default release is published 0.3.0-alpha.4. "
    "Release 0.3.0-alpha.5 is an unreleased source candidate. "
    "Never fabricate selectors, runtime behavior, or payment entitlements."
))


@server.tool(annotations=READ_ONLY, structured_output=True)
def search_components(query: str = "", release: str = PUBLISHED) -> dict[str, Any]:
    """Search curated, verified Syntyr components and required CSS files."""
    return checked(catalog.search_components, query, release)


@server.tool(annotations=READ_ONLY, structured_output=True)
def get_component(name: str, release: str = PUBLISHED) -> dict[str, Any]:
    """Retrieve a verified component's classes and native HTML guidance."""
    return checked(catalog.get_component, name, release)


@server.tool(annotations=READ_ONLY, structured_output=True)
def get_interaction_contracts(name: str = "", release: str = PUBLISHED) -> dict[str, Any]:
    """List or inspect candidate-only UI anatomy, state hooks and behavior ownership."""
    return checked(catalog.get_interaction_contracts, name, release)


@server.tool(annotations=READ_ONLY, structured_output=True)
def lookup_api(name: str, release: str = PUBLISHED) -> dict[str, Any]:
    """Look up a concrete syn-* class or --syn-* token in the chosen release."""
    return checked(catalog.lookup_api, name, release)


@server.tool(annotations=READ_ONLY, structured_output=True)
def get_theme_tokens(query: str = "", release: str = PUBLISHED) -> dict[str, Any]:
    """List verified CSS theme properties; not computed or invented values."""
    return checked(catalog.get_theme_tokens, query, release)


@server.tool(annotations=READ_ONLY, structured_output=True)
def validate_markup(html: str, release: str = PUBLISHED,
                    stylesheets: list[str] | None = None) -> dict[str, Any]:
    """Validate literal markup; return pinned-release diagnostics and repair hints, not WCAG."""
    return checked(catalog.validate_markup, html, release, stylesheets)


if __name__ == "__main__":
    server.run()
