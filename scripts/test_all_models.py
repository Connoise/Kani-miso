"""
Test all possible Claude model name variations.
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv
import anthropic

sys.path.append(str(Path(__file__).parent))
from utils.logger import setup_logger

logger = setup_logger(__name__)
load_dotenv(Path(__file__).parent.parent / "config" / ".env")


def test_model(client, model_name):
    """Quick test if a model works."""
    try:
        response = client.messages.create(
            model=model_name,
            max_tokens=10,
            messages=[{"role": "user", "content": "test"}]
        )
        return True
    except:
        return False


def main():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    client = anthropic.Anthropic(api_key=api_key)

    # All possible model variations to try
    models = [
        # Claude 3.5 Sonnet variants
        "claude-3-5-sonnet-20241022",
        "claude-3-5-sonnet-20240620",
        "claude-3.5-sonnet",
        "claude-3.5-sonnet-20241022",
        "claude-3.5-sonnet-20240620",

        # Claude 3 Opus variants
        "claude-3-opus-20240229",
        "claude-3-opus",

        # Claude 3 Sonnet variants
        "claude-3-sonnet-20240229",
        "claude-3-sonnet",

        # Claude 3 Haiku variants
        "claude-3-haiku-20240307",
        "claude-3-haiku",

        # Newer versions
        "claude-3-5-sonnet-latest",
        "claude-3-opus-latest",
        "claude-3-sonnet-latest",

        # Legacy
        "claude-2.1",
        "claude-2",
        "claude-instant-1.2",
    ]

    print("\n" + "=" * 60)
    print("Testing All Model Variations")
    print("=" * 60 + "\n")

    working = []
    for model in models:
        sys.stdout.write(f"Testing {model:<40} ")
        sys.stdout.flush()

        if test_model(client, model):
            print("✓ WORKS")
            working.append(model)
        else:
            print("✗")

    print("\n" + "=" * 60)
    if working:
        print(f"✓ Found {len(working)} working model(s):\n")
        for model in working:
            print(f"  {model}")
        print(f"\nRecommended: {working[0]}")
    else:
        print("✗ No models found beyond Haiku")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
