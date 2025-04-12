"""
Ollama service for interacting with the Ollama API.
"""
import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class OllamaService:
    """Ollama service class for making API calls."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Ollama service."""
        self.config = config or {}
        self.base_url = self.config.get("base_url", "http://localhost:11434")
        self.model = self.config.get("model", "llama3")
        self.api_client = httpx.AsyncClient(base_url=self.base_url, timeout=60.0)

    async def chat_completion(
        self, messages: List[Dict[str, str]], temperature: float = 0.7, max_tokens: Optional[int] = None, **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Make an asynchronous chat completion request to Ollama API.

        Args:
            messages: List of message dictionaries with role and content
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum number of tokens to generate
            **kwargs: Additional parameters to pass to the API

        Returns:
            Dict containing the API response

        Raises:
            Exception: If the API call fails
        """
        try:
            # Prepare the request payload
            payload = {
                "model": kwargs.get("model", self.model),
                "messages": messages,
                "temperature": temperature,
                "max_length": max_tokens,
                "stream": False,
            }

            # Remove None values
            payload = {k: v for k, v in payload.items() if v is not None}

            # Add any additional parameters
            for key, value in kwargs.items():
                if key not in payload and value is not None:
                    payload[key] = value

            # Make the API call
            response = await self.api_client.post("/api/chat", json=payload)
            response.raise_for_status()

            result = response.json()

            # Format response to match the expected structure
            return {"choices": [{"message": {"role": "assistant", "content": result.get("response", "")}}], "model": result.get("model", self.model)}

        except httpx.HTTPStatusError as e:
            raise Exception(f"Ollama API HTTP error: {str(e)}")
        except httpx.RequestError as e:
            raise Exception(f"Ollama API request error: {str(e)}")
        except Exception as e:
            raise Exception(f"Ollama API call failed: {str(e)}")
