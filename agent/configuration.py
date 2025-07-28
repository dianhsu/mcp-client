from typing import Optional

from pydantic import BaseModel

from .llm.azure_ai import AzureAIConfig


class StdioServerConfiguration(BaseModel):
    """
    Configuration for the stdio server connection.
    """

    name: str
    command: str
    args: list[str] = []
    working_directory: Optional[str] = None
    env: Optional[dict] = None


class HttpServerConfiguration(BaseModel):
    """
    Configuration for the HTTP server connection.
    """

    name: str
    url: str
    headers: Optional[dict] = None


class AgentConfiguration(BaseModel):
    """
    Configuration for the client connection.
    """

    llm: AzureAIConfig
    servers: list[StdioServerConfiguration | HttpServerConfiguration]
