"""
Test Claude 4.5 models specifically.
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


def test_model(client, model_name, description):
    """Test if a model works and show details."""
    try:
        logger.info(f"Testing: {description}")
        logger.info(f"  Model ID: {model_name}")

        response = client.messages.create(
            model=model_name,
            max_tokens=50,
            messages=[{"role": "user", "content": "Reply with just 'OK' if you can read this."}]
        )

        logger.info(f"  ✓ SUCCESS!")
        logger.info(f"  Response: {response.content[0].text}")
        logger.info(f"  Input tokens: {response.usage.input_tokens}")
        logger.info(f"  Output tokens: {response.usage.output_tokens}")
        return True

    except anthropic.NotFoundError as e:
        logger.error(f"  ✗ Model not found")
        return False
    except anthropic.AuthenticationError as e:
        logger.error(f"  ✗ Authentication error")
        logger.error(f"  Your API key may not have access to this model")
        return False
    except Exception as e:
        logger.error(f"  ✗ Error: {e}")
        return False


def main():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    client = anthropic.Anthropic(api_key=api_key)

    print("\n" + "=" * 60)
    print("Testing Claude 4.5 Models")
    print("=" * 60 + "\n")

    # Claude 4.5 models (newest generation)
    models_to_test = [
        ("claude-sonnet-4-5-20250929", "Claude Sonnet 4.5 (September 2025)"),
        ("claude-opus-4-5-20251101", "Claude Opus 4.5 (November 2025)"),
        ("claude-4-sonnet", "Claude 4 Sonnet (generic)"),
        ("claude-4-opus", "Claude 4 Opus (generic)"),
        ("claude-sonnet-4.5", "Claude Sonnet 4.5 (dot notation)"),
        ("claude-opus-4.5", "Claude Opus 4.5 (dot notation)"),
    ]

    working_models = []

    for model_id, description in models_to_test:
        if test_model(client, model_id, description):
            working_models.append((model_id, description))
        print()

    # Summary
    print("=" * 60)
    if working_models:
        print(f"✓ Found {len(working_models)} working Claude 4.5 model(s):\n")
        for model_id, description in working_models:
            print(f"  {description}")
            print(f"    Model ID: {model_id}\n")

        print("Recommended for config.yaml:")
        print(f'  model: "{working_models[0][0]}"')
    else:
        print("✗ No Claude 4.5 models available with your API key")
        print("\nYour account may need:")
        print("  1. Higher tier/plan")
        print("  2. Beta access enrollment")
        print("  3. Billing verification")
        print("\nCheck: https://console.anthropic.com/")

    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
