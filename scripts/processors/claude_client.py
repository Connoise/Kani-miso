"""
Claude API Client for Second Brain
Handles communication with Anthropic's Claude API for processing captures.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
import anthropic

import sys
sys.path.append(str(Path(__file__).parent.parent))
from utils.logger import setup_logger

logger = setup_logger(__name__)


class ClaudeClient:
    """Client for processing captures using Claude API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ):
        """
        Initialize Claude API client.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Claude model to use
            max_tokens: Maximum tokens in response
            temperature: Response temperature (0-1)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Anthropic API key required. Set ANTHROPIC_API_KEY environment variable "
                "or pass api_key parameter."
            )

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

        logger.info(f"Initialized Claude client (model: {model})")

    def load_prompt_template(self, prompt_file: Path) -> str:
        """
        Load a prompt template from the specs directory.

        Args:
            prompt_file: Path to the prompt markdown file

        Returns:
            Prompt template content
        """
        if not prompt_file.exists():
            raise FileNotFoundError(f"Prompt template not found: {prompt_file}")

        with open(prompt_file, 'r', encoding='utf-8') as f:
            content = f.read()

        logger.debug(f"Loaded prompt template: {prompt_file.name}")
        return content

    def process_telegram_capture(
        self,
        capture: Dict[str, Any],
        specs_dir: Path,
    ) -> str:
        """
        Process a Telegram capture into structured markdown.

        Args:
            capture: Capture dictionary from queue
            specs_dir: Path to specs directory

        Returns:
            Processed markdown content
        """
        # Load the telegram processing prompt
        telegram_prompt_path = specs_dir / "telegram-processing-prompt.md"
        system_prompt = self.load_prompt_template(telegram_prompt_path)

        # Build the user message with capture data
        user_message = self._build_telegram_user_message(capture)

        # Call Claude API
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )

        # Extract the text content
        markdown_content = response.content[0].text

        logger.info(
            f"Processed capture {capture['id']} "
            f"(tokens: {response.usage.input_tokens} in, {response.usage.output_tokens} out)"
        )

        return markdown_content

    def _build_telegram_user_message(self, capture: Dict[str, Any]) -> str:
        """
        Build the user message for Telegram capture processing.

        Args:
            capture: Capture dictionary

        Returns:
            Formatted user message
        """
        lines = [
            "Process the following Telegram capture using",
            "claude-master-prompt.md and",
            "telegram-processing-prompt.md",
            "output markdown only",
            "do not write files yet",
            "",
            f"Type: {capture['type']}",
        ]

        # Add the main body
        lines.append(capture['body'])

        # Add context fields if present
        if capture.get('surface'):
            lines.append(f"Surface: {capture['surface']}")

        if capture.get('mood'):
            lines.append(f"Mood: {capture['mood']}")

        if capture.get('energy'):
            lines.append(f"Energy: {capture['energy']}")

        if capture.get('confidence'):
            lines.append(f"Confidence: {capture['confidence']}")

        if capture.get('trigger'):
            lines.append(f"Trigger: {capture['trigger']}")

        if capture.get('context'):
            lines.append(f"Context: {capture['context']}")

        return "\n".join(lines)

    def test_connection(self) -> bool:
        """
        Test the API connection with a simple request.

        Returns:
            True if connection successful
        """
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=50,
                messages=[
                    {"role": "user", "content": "Reply with 'OK' if you can read this."}
                ]
            )
            logger.info("API connection test successful")
            return True
        except Exception as e:
            logger.error(f"API connection test failed: {e}")
            return False
