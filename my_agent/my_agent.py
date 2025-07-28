from agents import Agent, Runner, set_default_openai_api, set_default_openai_client, set_tracing_disabled
from agents.mcp import MCPServerSse, MCPServerStdio, MCPServerStreamableHttp
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AsyncAzureOpenAI


class MyAgent:
    def __init__(
        self,
        name="Assistant",
        instructions="You are a helpful assistant",
        azure_endpoint="https://stdzn360model.openai.azure.com/",
        model="gpt-4.1",
        api_version="2025-03-01-preview",
        mcp_servers: list[MCPServerStdio | MCPServerStreamableHttp | MCPServerSse] = None,
    ):
        self.name = name
        self.instructions = instructions
        self.model = model
        self.azure_endpoint = azure_endpoint
        self.api_version = api_version
        self.token_provider = get_bearer_token_provider(
            DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
        )
        self.client = AsyncAzureOpenAI(
            azure_endpoint=self.azure_endpoint,
            api_version=self.api_version,
            azure_ad_token_provider=self.token_provider,
            api_key=None,  # No API key needed when using Azure AD token
        )

        set_default_openai_client(self.client, use_for_tracing=False)
        set_default_openai_api("chat_completions")
        set_tracing_disabled(disabled=True)
        self.mcp_servers = [] if mcp_servers is None else mcp_servers

    async def run(self, msg: str):
        try:
            for mcp_server in self.mcp_servers:
                await mcp_server.connect()
            agent = Agent(
                name=self.name,
                instructions=self.instructions,
                model=self.model,
                mcp_servers=self.mcp_servers,
            )
            return await Runner.run(
                agent,
                msg,
            )
        except Exception as e:
            print(f"Error running agent: {e}")
            return None
        finally:
            for mcp_server in self.mcp_servers:
                await mcp_server.cleanup()
