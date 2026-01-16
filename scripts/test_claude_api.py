"""
Test Claude API connection and check available models.
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv
import anthropic

sys.path.append(str(Path(__file__).parent))
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Load environment
load_dotenv(Path(__file__).parent.parent / "config" / ".env")


def test_api_key():
    """Test if API key is configured correctly."""
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        logger.error("ANTHROPIC_API_KEY not found in config/.env")
        return False

    if api_key == "your_anthropic_api_key_here":
        logger.error("ANTHROPIC_API_KEY is still the placeholder value")
        return False

    logger.info(f"API Key found (starts with: {api_key[:10]}...)")
    return True


def test_connection(model_name):
    """Test API connection with a specific model."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    client = anthropic.Anthropic(api_key=api_key)

    try:
        logger.info(f"Testing model: {model_name}")
        response = client.messages.create(
            model=model_name,
            max_tokens=50,
            messages=[
                {"role": "user", "content": "Reply with just 'OK' if you can read this."}
            ]
        )
        logger.info(f"✓ {model_name} works!")
        logger.info(f"  Response: {response.content[0].text}")
        return True
    except anthropic.NotFoundError as e:
        logger.error(f"✗ {model_name} not found")
        logger.error(f"  Error: {e}")
        return False
    except anthropic.AuthenticationError as e:
        logger.error(f"✗ Authentication failed")
        logger.error(f"  Error: {e}")
        logger.error(f"  Check your API key in config/.env")
        return False
    except Exception as e:
        logger.error(f"✗ {model_name} failed")
        logger.error(f"  Error: {e}")
        return False


def main():
    """Test various Claude models to find which ones work."""
    print("\n" + "=" * 60)
    print("Claude API Diagnostics")
    print("=" * 60 + "\n")

    # Check API key
    if not test_api_key():
        return

    print()

    # Test models in order of preference
    models_to_test = [
        ("claude-3-5-sonnet-20241022", "Claude 3.5 Sonnet (Latest)"),
        ("claude-3-5-sonnet-20240620", "Claude 3.5 Sonnet (June)"),
        ("claude-3-sonnet-20240229", "Claude 3 Sonnet"),
        ("claude-3-opus-20240229", "Claude 3 Opus (Highest Quality)"),
        ("claude-3-haiku-20240307", "Claude 3 Haiku (Fastest)"),
    ]

    working_models = []

    for model_id, model_name in models_to_test:
        if test_connection(model_id):
            working_models.append((model_id, model_name))
        print()

    # Summary
    print("=" * 60)
    if working_models:
        print(f"✓ Found {len(working_models)} working model(s):")
        for model_id, model_name in working_models:
            print(f"  - {model_name}: {model_id}")

        print("\nRecommended for config.yaml:")
        print(f'  model: "{working_models[0][0]}"')
    else:
        print("✗ No working models found")
        print("\nPossible issues:")
        print("  1. API key is invalid or expired")
        print("  2. Account doesn't have API access enabled")
        print("  3. API credits/billing not set up")
        print("\nCheck: https://console.anthropic.com/")

    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
