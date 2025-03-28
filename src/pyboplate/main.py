"""Main module for pyboplate using DeepSeek API."""

import logging
import sys
import time

from openai import OpenAI

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_deepseek_response_stream(
    prompt: str, system_message: str = "You are a helpful Python assistant."
):
    """Get a streaming response from the DeepSeek API.

    Args:
        prompt: The user prompt to send to the model
        system_message: The system message to set the behavior of the assistant
    """
    try:
        logger.info("Initializing DeepSeek API client...")

        client = OpenAI(
            api_key="sk-63bd9603728549a49039e0018b471d30",
            base_url="https://api.deepseek.com",
            timeout=10.0,  # Shorter timeout
        )

        logger.info("Sending streaming request to DeepSeek API...")
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt},
            ],
            stream=True,  # Enable streaming
            temperature=0.7,
            max_tokens=512,
        )

        # Stream the response content
        full_content = ""
        print("\nStreaming response:\n" + "-" * 50)

        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                content_piece = chunk.choices[0].delta.content
                print(content_piece, end="", flush=True)
                full_content += content_piece

        print("\n" + "-" * 50)
        return full_content

    except Exception as e:
        logger.error(f"Error while calling DeepSeek API: {str(e)}")
        return None


def get_deepseek_response(
    prompt: str, system_message: str = "You are a helpful Python assistant."
):
    """Get a non-streaming response from the DeepSeek API.

    Args:
        prompt: The user prompt to send to the model
        system_message: The system message to set the behavior of the assistant
    """
    try:
        logger.info("Initializing DeepSeek API client...")

        client = OpenAI(
            api_key="sk-63bd9603728549a49039e0018b471d30",
            base_url="https://api.deepseek.com",
            timeout=15.0,  # Shorter timeout
        )

        logger.info("Sending request to DeepSeek API...")
        start_time = time.time()
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt},
            ],
            stream=False,
            temperature=0.7,
            max_tokens=512,
        )
        end_time = time.time()
        logger.info(f"Response received in {end_time - start_time:.2f} seconds")

        return response
    except Exception as e:
        logger.error(f"Error while calling DeepSeek API: {str(e)}")
        return None


def main():
    """Run a test of the DeepSeek API."""
    query = "What are the key features of Python 3.12? Keep it brief."

    print(f"Querying DeepSeek AI: '{query}'")
    print("-" * 50)

    # Try streaming approach first
    print("Using streaming API...")
    content = get_deepseek_response_stream(query)

    if not content:
        print("\nStreaming failed, trying non-streaming API...")
        response = get_deepseek_response(query)

        if response:
            print("\nResponse from DeepSeek API:")
            print("-" * 50)
            print(response.choices[0].message.content)
            print("-" * 50)

            # Store model usage information
            usage = response.usage
            logger.info(
                f"Tokens used - Prompt: {usage.prompt_tokens}, "
                f"Completion: {usage.completion_tokens}, Total: {usage.total_tokens}"
            )
        else:
            print("Failed to get a response from DeepSeek API.")
            sys.exit(1)


if __name__ == "__main__":
    main()
