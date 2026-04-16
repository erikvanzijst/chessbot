#!/usr/bin/env python3
import os
import sys
import argparse
from openai import OpenAI
from chessbot.log import setup_logging


def main():
    parser = argparse.ArgumentParser(description="Query the LLM via OpenAI-compatible API")
    parser.add_argument("prompt", help="The prompt to send to the LLM")
    parser.add_argument("--no-reasoning", action="store_true", help="Do not show reasoning in logs")
    args = parser.parse_args()

    logger = setup_logging("ai")

    base_url = os.environ.get("OPENAI_BASE_URL")
    api_key = os.environ.get("OPENAI_API_KEY")
    model = os.environ.get("MODEL")

    if not all([base_url, api_key, model]):
        logger.error("Missing environment variables OPENAI_BASE_URL, OPENAI_API_KEY, or MODEL")
        sys.exit(1)

    client = OpenAI(base_url=base_url, api_key=api_key)

    response = client.chat.completions.create(model=model, messages=[{"role": "user", "content": args.prompt}])
    full_content = response.choices[0].message.content
    if reasoning := response.choices[0].message.reasoning_content:
        if not args.no_reasoning:
            logger.info(f"Reasoning: {reasoning}")

    print(full_content)


if __name__ == "__main__":
    main()
