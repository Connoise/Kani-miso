"""
Claude API Client for Second Brain
Handles communication with Anthropic's Claude API for processing captures.
Supports both text and image (Vision) processing.
"""

import os
import base64
import json
import mimetypes
from pathlib import Path
from typing import Optional, Dict, Any, List
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

    def _encode_image_to_base64(self, image_path: str) -> tuple[str, str]:
        """
        Encode an image file to base64.

        Args:
            image_path: Path to image file

        Returns:
            Tuple of (base64_data, media_type)
        """
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        # Determine media type
        mime_type, _ = mimetypes.guess_type(str(path))
        if mime_type is None:
            # Default based on extension
            ext = path.suffix.lower()
            mime_map = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.webp': 'image/webp',
            }
            mime_type = mime_map.get(ext, 'image/jpeg')

        with open(path, 'rb') as f:
            image_data = base64.standard_b64encode(f.read()).decode('utf-8')

        return image_data, mime_type

    def process_capture_with_images(
        self,
        capture: Dict[str, Any],
        image_paths: List[str],
        specs_dir: Path,
        notes_root: Path,
    ) -> str:
        """
        Process a capture that includes images using Vision.

        Args:
            capture: Capture dictionary from queue
            image_paths: List of paths to image files
            specs_dir: Path to specs directory
            notes_root: Path to notes root (for relative paths in output)

        Returns:
            Processed markdown content with embedded images
        """
        # Load the telegram processing prompt
        telegram_prompt_path = specs_dir / "telegram-processing-prompt.md"
        system_prompt = self.load_prompt_template(telegram_prompt_path)

        # Add image-specific instructions to system prompt
        image_instructions = """

## Image Processing Instructions

When processing captures with images:
1. Analyze each image carefully and describe its content
2. Connect the image content to any associated text
3. In the output markdown, include Obsidian-compatible image embeds using the format: ![[relative/path/to/image.jpg]]
4. Create a cohesive note that integrates both the visual and textual content
5. Identify themes and concepts from both the images and text
6. Suggest relevant hubs based on the combined content
"""
        system_prompt += image_instructions

        # Build the content array with images and text
        content = []

        # Add images first
        for image_path in image_paths:
            try:
                image_data, media_type = self._encode_image_to_base64(image_path)

                # Calculate relative path for the markdown output
                try:
                    rel_path = Path(image_path).relative_to(notes_root)
                    rel_path_str = str(rel_path).replace("\\", "/")
                except ValueError:
                    rel_path_str = Path(image_path).name

                content.append({
                    "type": "text",
                    "text": f"[Image: {rel_path_str}]"
                })
                content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": image_data,
                    }
                })
                logger.debug(f"Added image to request: {image_path}")

            except Exception as e:
                logger.error(f"Failed to encode image {image_path}: {e}")
                content.append({
                    "type": "text",
                    "text": f"[Image could not be loaded: {image_path}]"
                })

        # Add the text content
        text_message = self._build_telegram_user_message_with_images(capture, image_paths, notes_root)
        content.append({
            "type": "text",
            "text": text_message
        })

        # Call Claude API with vision
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=system_prompt,
            messages=[
                {"role": "user", "content": content}
            ]
        )

        # Extract the text content
        markdown_content = response.content[0].text

        logger.info(
            f"Processed capture {capture['id']} with {len(image_paths)} images "
            f"(tokens: {response.usage.input_tokens} in, {response.usage.output_tokens} out)"
        )

        return markdown_content

    def _build_telegram_user_message_with_images(
        self,
        capture: Dict[str, Any],
        image_paths: List[str],
        notes_root: Path,
    ) -> str:
        """
        Build the user message for captures with images.

        Args:
            capture: Capture dictionary
            image_paths: List of image paths
            notes_root: Path to notes root

        Returns:
            Formatted user message
        """
        lines = [
            "Process this Telegram capture that includes images.",
            "Use claude-master-prompt.md and telegram-processing-prompt.md",
            "Output markdown only. Do not write files yet.",
            "",
            f"Number of images: {len(image_paths)}",
            "",
            "Image paths for embedding in the note:",
        ]

        # Add relative paths for each image
        for image_path in image_paths:
            try:
                rel_path = Path(image_path).relative_to(notes_root)
                rel_path_str = str(rel_path).replace("\\", "/")
            except ValueError:
                rel_path_str = Path(image_path).name
            lines.append(f"  - {rel_path_str}")

        lines.append("")
        lines.append(f"Type: {capture['type']}")
        lines.append("")
        lines.append("Associated text:")
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

        lines.append("")
        lines.append("Create a single cohesive note that:")
        lines.append("1. Describes what is shown in the image(s)")
        lines.append("2. Integrates the associated text")
        lines.append("3. Includes Obsidian image embeds: ![[path/to/image.jpg]]")
        lines.append("4. Identifies themes from both visual and text content")

        return "\n".join(lines)

    def process_source_capture(
        self,
        capture: Dict[str, Any],
        web_content: Dict[str, Any],
        specs_dir: Path,
    ) -> str:
        """
        Process a source capture (webpage/article) into structured markdown.

        Args:
            capture: Capture dictionary from queue (includes user context)
            web_content: Dictionary from WebFetcher with:
                - url: original URL
                - metadata: extracted metadata (title, author, date, etc.)
                - markdown_content: converted webpage content
            specs_dir: Path to specs directory

        Returns:
            Processed markdown content
        """
        # Load the source processing prompt
        source_prompt_path = specs_dir / "source-processing-prompt.md"
        system_prompt = self.load_prompt_template(source_prompt_path)

        # Build the user message with source data
        user_message = self._build_source_user_message(capture, web_content)

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
            f"Processed source capture {capture['id']} "
            f"(tokens: {response.usage.input_tokens} in, {response.usage.output_tokens} out)"
        )

        return markdown_content

    def _build_source_user_message(
        self,
        capture: Dict[str, Any],
        web_content: Dict[str, Any],
    ) -> str:
        """
        Build the user message for source capture processing.

        Args:
            capture: Capture dictionary
            web_content: Web content dictionary from WebFetcher

        Returns:
            Formatted user message
        """
        metadata = web_content.get('metadata', {})

        lines = [
            "Process the following webpage source for the archive.",
            "Use source-processing-prompt.md to format the output.",
            "Output markdown only.",
            "",
            "## Source URL",
            web_content.get('url', 'Unknown'),
            "",
            "## Extracted Metadata",
            f"- Title: {metadata.get('title', 'Unknown')}",
            f"- Author: {metadata.get('author', 'Unknown')}",
            f"- Published Date: {metadata.get('date', 'Unknown')}",
            f"- Site Name: {metadata.get('site_name', metadata.get('domain', 'Unknown'))}",
            f"- Description: {metadata.get('description', 'N/A')}",
            "",
            f"## Captured At",
            capture.get('captured_at', 'Unknown'),
            "",
        ]

        # Add user context if provided
        user_body = capture.get('body', '').strip()
        # Extract URL from body if present (user might have included just URL or URL + context)
        # We want to capture any additional context the user provided beyond just the URL
        url = web_content.get('url', '')
        user_context = user_body.replace(url, '').strip()

        if user_context:
            lines.extend([
                "## User Context (Why This Was Captured)",
                user_context,
                "",
            ])
        else:
            lines.extend([
                "## User Context (Why This Was Captured)",
                "No context provided by user.",
                "",
            ])

        # Add the converted webpage content
        markdown_content = web_content.get('markdown_content', '')
        if markdown_content:
            # Limit content length for API (keep under ~100k chars)
            max_content_length = 80000
            if len(markdown_content) > max_content_length:
                truncated = markdown_content[:max_content_length]
                lines.extend([
                    "## Webpage Content (Converted to Markdown)",
                    "Note: Content was truncated due to length.",
                    "",
                    truncated,
                    "",
                    "[Content truncated - original was significantly longer]",
                ])
            else:
                lines.extend([
                    "## Webpage Content (Converted to Markdown)",
                    markdown_content,
                ])
        else:
            lines.extend([
                "## Webpage Content",
                "Content could not be extracted from the webpage.",
            ])

        return "\n".join(lines)

    def process_pdf_capture(
        self,
        capture: Dict[str, Any],
        pdf_content: Dict[str, Any],
        specs_dir: Path,
    ) -> str:
        """
        Process a PDF capture into structured markdown.

        Args:
            capture: Capture dictionary from queue (includes user context)
            pdf_content: Dictionary from PDFProcessor with:
                - text: extracted text content
                - metadata: PDF metadata (title, author, etc.)
                - page_count: total pages
                - pages_processed: pages actually processed
                - file_path: path to PDF file
                - file_name: PDF filename
            specs_dir: Path to specs directory

        Returns:
            Processed markdown content
        """
        # Load the PDF processing prompt
        pdf_prompt_path = specs_dir / "pdf-processing-prompt.md"
        system_prompt = self.load_prompt_template(pdf_prompt_path)

        # Build the user message with PDF data
        user_message = self._build_pdf_user_message(capture, pdf_content)

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
            f"Processed PDF capture {capture['id']} "
            f"(tokens: {response.usage.input_tokens} in, {response.usage.output_tokens} out)"
        )

        return markdown_content

    def _build_pdf_user_message(
        self,
        capture: Dict[str, Any],
        pdf_content: Dict[str, Any],
    ) -> str:
        """
        Build the user message for PDF capture processing.

        Args:
            capture: Capture dictionary
            pdf_content: PDF content dictionary from PDFProcessor

        Returns:
            Formatted user message
        """
        metadata = pdf_content.get('metadata', {})

        lines = [
            "Process the following PDF document for the archive.",
            "Use pdf-processing-prompt.md to format the output.",
            "Output markdown only.",
            "",
            "## PDF Information",
            f"- File Name: {pdf_content.get('file_name', 'Unknown')}",
            f"- File Path: {pdf_content.get('file_path', 'Unknown')}",
            f"- Page Count: {pdf_content.get('page_count', 'Unknown')}",
            f"- Pages Processed: {pdf_content.get('pages_processed', 'Unknown')}",
            "",
            "## PDF Metadata",
            f"- Title: {metadata.get('title', 'Unknown')}",
            f"- Author: {metadata.get('author', 'Unknown')}",
            f"- Subject: {metadata.get('subject', 'Unknown')}",
            f"- Creator: {metadata.get('creator', 'Unknown')}",
            f"- Creation Date: {metadata.get('creation_date', 'Unknown')}",
            "",
            "## Captured At",
            capture.get('captured_at', 'Unknown'),
            "",
        ]

        # Add user context if provided
        user_body = capture.get('body', '').strip()
        # Remove "PDF: filename" if that's all there is
        file_name = pdf_content.get('file_name', '')
        if user_body.startswith(f"PDF: {file_name}"):
            user_context = user_body[len(f"PDF: {file_name}"):].strip()
        else:
            user_context = user_body

        if user_context:
            lines.extend([
                "## User Context (Why This Was Captured)",
                user_context,
                "",
            ])
        else:
            lines.extend([
                "## User Context (Why This Was Captured)",
                "No context provided by user.",
                "",
            ])

        # Add the extracted PDF text
        pdf_text = pdf_content.get('text', '')
        if pdf_text:
            # Limit content length for API (keep under ~100k chars)
            max_content_length = 80000
            if len(pdf_text) > max_content_length:
                truncated = pdf_text[:max_content_length]
                lines.extend([
                    "## Extracted PDF Text",
                    "Note: Content was truncated due to length.",
                    "",
                    truncated,
                    "",
                    "[Content truncated - original was significantly longer]",
                ])
            else:
                lines.extend([
                    "## Extracted PDF Text",
                    pdf_text,
                ])
        else:
            lines.extend([
                "## Extracted PDF Text",
                "Text could not be extracted from the PDF.",
            ])

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
