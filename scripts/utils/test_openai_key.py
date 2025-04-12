"""
Test script for OpenAI service.
"""
import asyncio
import os

from src.llm.openai_service import OpenAIService


async def test_openai_service():
    """Test OpenAI service functionality."""
    try:
        # Initialize service
        service = OpenAIService()
        print(f"Successfully loaded API key: {service.api_key[:8]}...")

        # Test API call
        messages = [{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": "Hello! Can you hear me?"}]

        response = await service.chat_completion(messages)

        # Print response details
        print("\nAPI Response Details:")
        print(f"Model: {response.model}")
        print(f"Response: {response.choices[0].message.content}")
        print(f"Usage - Prompt tokens: {response.usage.prompt_tokens}")
        print(f"Usage - Completion tokens: {response.usage.completion_tokens}")
        print(f"Usage - Total tokens: {response.usage.total_tokens}")

        print("\nTest completed successfully!")

    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(test_openai_service())
