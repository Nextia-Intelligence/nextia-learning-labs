"""python -m orders_mcp: the order systems' MCP server on stdio (the tool gateway starts it)."""

from orders_mcp.server import build_server

if __name__ == "__main__":
    build_server().run("stdio")
