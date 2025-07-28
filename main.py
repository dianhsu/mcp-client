import asyncio

from agent import Agent, AgentConfiguration, AzureAIConfig, StdioServerConfiguration


async def request(msg: str, agent_config: AgentConfiguration) -> str:
    """
    Sends a message to the agent and returns the response.
    """
    agent = Agent(agent_config)
    response = await agent.send(msg)
    return response


async def main():
    """
    Main function to run the agent.
    """
    # Load configuration from a file or environment variables
    config = AgentConfiguration(
        llm=AzureAIConfig(
            endpoint="https://stdzn360model.openai.azure.com/",
        ),
        servers=[
            StdioServerConfiguration(
                name="stdio_server",
                command="python",
                args=["-m", "server.main"],
                env={"PYTHONPATH": "."},
            )
        ],
    )

    request_message = "find all python files in the current directory and subdirectories"
    response = await request(request_message, config)
    print(f"Response from agent: \n {response}")


if __name__ == "__main__":
    asyncio.run(main())
