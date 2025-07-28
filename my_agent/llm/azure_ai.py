from typing import Optional

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AzureOpenAI
from pydantic import BaseModel, Field


class AzureAIConfig(BaseModel):
    api_version: str = Field(default="2025-03-01-preview")
    endpoint: str
    api_key: Optional[str] = Field(default=None, description="API key for Azure OpenAI.")
    model: str = Field(default="gpt-4.1", description="Model to use for Azure OpenAI requests.")


class AzureAIClient:
    def __init__(self, azure_ai_config: AzureAIConfig):
        token_provider = get_bearer_token_provider(
            DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
        )
        self.config = azure_ai_config
        self.client = AzureOpenAI(
            azure_endpoint=self.config.endpoint,
            api_key=self.config.api_key,
            api_version=self.config.api_version,
            azure_ad_token_provider=token_provider,
        )

    def get_response(self, messages: list[dict[str, any]], **kwargs):
        """
        Sends a request to the Azure OpenAI service.
        """
        llm_res = self.client.chat.completions.create(model=self.config.model, messages=messages, **kwargs)
        return llm_res.choices[0].message.content if llm_res.choices else None
