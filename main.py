import asyncio

from agents.mcp import MCPServerStdio

from my_agent import MyAgent


async def main():
    """
    Main function to run the agent.
    """
    # Load configuration from a file or environment variables

    servers = [
        MCPServerStdio(
            params={
                "command": "python",
                "args": ["-m", "server.main"],
                "env": {"PYTHONPATH": "."},
            }
        ),
    ]

    request_message = "find all python files in the current directory and subdirectories"
    agent = MyAgent(mcp_servers=servers)
    response = await agent.run(request_message)
    print(f"Response from agent: \n {response.final_output}")


if __name__ == "__main__":
    asyncio.run(main())
