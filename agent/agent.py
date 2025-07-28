"""
This module defines the Client class for connecting to a server.
"""

import asyncio
import json
import os
import shutil
from contextlib import AsyncExitStack
from typing import Any

from loguru import logger
from mcp import ClientSession, StdioServerParameters, Tool, stdio_client
from mcp.client.streamable_http import streamablehttp_client

from .configuration import AgentConfiguration, HttpServerConfiguration, StdioServerConfiguration
from .llm.azure_ai import AzureAIClient, AzureAIConfig


class Server:
    """Manages MCP server connections and tool execution."""

    def __init__(self, config: StdioServerConfiguration | HttpServerConfiguration) -> None:
        self.name: str = config.name
        self.config: StdioServerConfiguration | HttpServerConfiguration = config
        self.stdio_context: Any | None = None
        self.session: ClientSession | None = None
        self._cleanup_lock: asyncio.Lock = asyncio.Lock()
        self.exit_stack: AsyncExitStack = AsyncExitStack()

    async def initialize(self) -> None:
        """Initialize the server connection."""
        if isinstance(self.config, StdioServerConfiguration):
            command = shutil.which("npx") if self.config.command == "npx" else self.config.command
            if command is None:
                raise ValueError("The command must be a valid string and cannot be None.")

            server_params = StdioServerParameters(
                command=command,
                args=self.config.args,
                cwd=self.config.working_directory,
                env={**os.environ, **self.config.env} if self.config.env else os.environ,
            )
            try:
                stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
                read, write = stdio_transport
                session = await self.exit_stack.enter_async_context(ClientSession(read, write))
                await session.initialize()
                self.session = session
            except Exception as e:
                logger.error(f"Failed to initialize server {self.name}: {e}")
                await self.cleanup()
                raise
        elif isinstance(self.config, HttpServerConfiguration):
            try:
                session = await self.exit_stack.enter_async_context(
                    streamablehttp_client(self.config.url, headers=self.config.headers)
                )
                await session.initialize()
                self.session = session
            except Exception as e:
                logger.error(f"Failed to initialize HTTP server {self.name}: {e}")
                await self.cleanup()
                raise
        else:
            raise ValueError(
                "Unsupported server configuration type. Must be StdioServerConfiguration or HttpServerConfiguration."
            )

    async def list_tools(self) -> list[Tool]:
        """List available tools from the server.

        Returns:
            A list of available tools.

        Raises:
            RuntimeError: If the server is not initialized.
        """
        if not self.session:
            raise RuntimeError(f"Server {self.name} not initialized")

        tools_response = await self.session.list_tools()
        tools = []

        for item in tools_response:
            if isinstance(item, tuple) and item[0] == "tools":
                tools.extend(
                    Tool(name=tool.name, description=tool.description, inputSchema=tool.inputSchema, title=tool.title)
                    for tool in item[1]
                )

        return tools

    async def execute_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        retries: int = 2,
        delay: float = 1.0,
    ) -> Any:
        """Execute a tool with retry mechanism.

        Args:
            tool_name: Name of the tool to execute.
            arguments: Tool arguments.
            retries: Number of retry attempts.
            delay: Delay between retries in seconds.

        Returns:
            Tool execution result.

        Raises:
            RuntimeError: If server is not initialized.
            Exception: If tool execution fails after all retries.
        """
        if not self.session:
            raise RuntimeError(f"Server {self.name} not initialized")

        attempt = 0
        while attempt < retries:
            try:
                logger.info(f"Executing {tool_name}...")
                result = await self.session.call_tool(tool_name, arguments)

                return result

            except Exception as e:  # pylint: disable=broad-except
                attempt += 1
                logger.warning(f"Error executing tool: {e}. Attempt {attempt} of {retries}.")
                if attempt < retries:
                    logger.info(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                else:
                    logger.error("Max retries reached. Failing.")
                    raise

    async def cleanup(self) -> None:
        """Clean up server resources."""
        async with self._cleanup_lock:
            try:
                await self.exit_stack.aclose()
                self.session = None
                self.stdio_context = None
            except Exception as e:  # pylint: disable=broad-except
                logger.error(f"Error during cleanup of server {self.name}: {e}")


class Agent:
    """
    MCP Client class for managing connections to servers.
    """

    def __init__(self, config: AgentConfiguration):
        self.config: AgentConfiguration = config
        self.servers: list[Server] = [Server(config=server) for server in config.servers]
        self.llm_client: AzureAIClient = AzureAIClient(
            AzureAIConfig(
                api_version=self.config.llm.api_version,
                endpoint=self.config.llm.endpoint,
                api_key=self.config.llm.api_key,
                model=self.config.llm.model,
            )
        )

    async def cleanup_servers(self) -> None:
        """Clean up all servers properly."""
        for server in reversed(self.servers):
            try:
                await server.cleanup()
            except Exception as e:  # pylint: disable=broad-except
                logger.warning(f"Warning during final cleanup: {e}")

    async def _process_llm_response(self, llm_response: str) -> str:
        """Process the LLM response and execute tools if needed.

        Args:
            llm_response: The response from the LLM.

        Returns:
            The result of tool execution or the original response.
        """

        try:
            tool_call = json.loads(llm_response)
            if "tool" in tool_call and "arguments" in tool_call:
                logger.info(f"Executing tool: {tool_call['tool']}")
                logger.info(f"With arguments: {tool_call['arguments']}")

                for server in self.servers:
                    tools = await server.list_tools()
                    if any(tool.name == tool_call["tool"] for tool in tools):
                        try:
                            result = await server.execute_tool(tool_call["tool"], tool_call["arguments"])

                            if isinstance(result, dict) and "progress" in result:
                                progress = result["progress"]
                                total = result["total"]
                                percentage = (progress / total) * 100
                                logger.info(f"Progress: {progress}/{total} ({percentage:.1f}%)")

                            return f"Tool execution result: {result}"
                        except Exception as e:  # pylint: disable=broad-except
                            error_msg = f"Error executing tool: {str(e)}"
                            logger.error(error_msg)
                            return error_msg

                return f"No server found with tool: {tool_call['tool']}"
            return llm_response
        except json.JSONDecodeError:
            return llm_response

    async def send(self, msg: str) -> None:
        """Main chat session handler."""
        try:
            for server in self.servers:
                try:
                    await server.initialize()
                except Exception as e:  # pylint: disable=broad-except
                    logger.error(f"Failed to initialize server: {e}")
                    await self.cleanup_servers()
                    return

            all_tools: list[Tool] = []
            for server in self.servers:
                tools = await server.list_tools()
                all_tools.extend(tools)

            tools_description = "\n".join(tool.model_dump_json() for tool in all_tools)

            system_message = f"""You are a helpful assistant with access to these tools:

{tools_description}

Choose the appropriate tool based on the user's question. If no tool is needed, reply directly.

IMPORTANT: When you need to use a tool, you must ONLY respond with the exact JSON object format below, nothing else:
{{
    "tool": "tool-name",
    "arguments": {{
        "argument-name": "value"
    }}
}}


After receiving a tool's response:
1. Transform the raw data into a natural, conversational response
2. Keep responses concise but informative
3. Focus on the most relevant information
4. Use appropriate context from the user's question
5. Avoid simply repeating the raw data

Please use only the tools that are explicitly defined above.

If you want to terminate the conversation or need user confirmation or ask for user input, you must respond with a simple message of "end", don't reply anything else.
"""

            messages = [{"role": "system", "content": system_message}]
            messages.append({"role": "user", "content": msg})
            final_res = ""
            while True:
                llm_response = self.llm_client.get_response(messages)
                res = await self._process_llm_response(llm_response)

                if res == "end":
                    return final_res
                final_res = res
                logger.info(f"LLM response: {res}")
                messages.append({"role": "assistant", "content": res})
        finally:
            await self.cleanup_servers()
