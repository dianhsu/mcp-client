"""
a simple example of using FastAgent with multiple servers
"""

import asyncio

from mcp_agent.core.fastagent import FastAgent

# Create the application
fast = FastAgent("fast-agent example")


# Define the agent
@fast.agent(
    instruction="You are a helpful AI Agent", servers=["fetch", "filesystem", "weather"]
)
async def main():
    """Main function for the FastAgent example."""
    async with fast.run() as agent:
        await agent.interactive()


if __name__ == "__main__":
    asyncio.run(main())
