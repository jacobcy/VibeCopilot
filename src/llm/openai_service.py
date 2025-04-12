"""
OpenAI service for interacting with OpenAI API.
"""
import asyncio
import logging
import os
from typing import Any, Dict, List, Optional

import openai
from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat import ChatCompletion

logger = logging.getLogger(__name__)


class OpenAIService:
    """OpenAI service class for making API calls."""

    def __init__(self):
        """Initialize OpenAI service."""
        load_dotenv()
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        self.client = OpenAI(api_key=self.api_key)
        self.model = "gpt-3.5-turbo"

    async def chat_completion(
        self, messages: List[Dict[str, str]], temperature: float = 0.7, max_tokens: Optional[int] = None, **kwargs: Any
    ) -> ChatCompletion:
        """
        Make an asynchronous chat completion request to OpenAI API.

        Args:
            messages: List of message dictionaries with role and content
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum number of tokens to generate
            **kwargs: Additional parameters to pass to the API

        Returns:
            ChatCompletion object containing the API response

        Raises:
            Exception: If the API call fails
        """
        try:
            logger.debug(f"Making chat completion request with {len(messages)} messages")
            # Run the synchronous API call in a thread pool
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model=self.model, messages=messages, temperature=temperature, max_tokens=max_tokens, **kwargs
                ),
            )
            logger.debug("Chat completion request successful")
            return response
        except openai.RateLimitError as e:
            logger.error(f"Rate limit exceeded: {str(e)}")
            raise
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in chat completion: {str(e)}")
            raise Exception(f"OpenAI API call failed: {str(e)}")
