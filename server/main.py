"""
# File: server/main.py
# A simple example of running a FastMCP server
#
"""

from mcp.server.fastmcp import FastMCP

from .script import register_script


def main():
    """Main function to run the FastMCP server with the weather example."""
    mcp = FastMCP("weather")

    register_script(mcp)

    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
