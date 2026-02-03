"""
User verification interface for personal background.

Provides interactive CLI verification of background information.
"""

import sys
from datetime import datetime
from typing import Optional

from .models import PersonalBackground, ALL_FIELD_SECTIONS, FieldDef


class UserVerifier:
    """
    Interactive verification of background information.

    Presents extracted/missing information and allows user to confirm/edit.
    """

    def verify(self, background: PersonalBackground) -> PersonalBackground:
        """
        Interactive verification loop.

        Args:
            background: PersonalBackground with extracted values

        Returns:
            Updated PersonalBackground with verified values
        """
        self._print_header()

        # Verify each section
        for section_key, (section_name, fields) in ALL_FIELD_SECTIONS.items():
            current_data = background.get_section(section_key)
            verified_data = self._verify_section(section_name, current_data, fields, background.extracted_fields)
            background.set_section(section_key, verified_data)

        # Calculate age if date_of_birth is provided
        background = self._calculate_derived_fields(background)

        # Mark as verified
        background.verification_status = "verified"
        background.last_verified = datetime.now()

        self._print_summary(background)
        return background

    def _print_header(self) -> None:
        """Print the verification header."""
        print("\n" + "=" * 60)
        print("             PERSONAL BACKGROUND VERIFICATION")
        print("=" * 60)
        print("\nPlease verify or provide the following information.")
        print("Press Enter to accept extracted values, or type to correct.")
        print("Type 'skip' to leave a field as 'Not provided'.")
        print("Type 'quit' to cancel verification.\n")

    def _verify_section(
        self,
        section_name: str,
        current: dict,
        field_definitions: list,
        extracted_fields: list,
    ) -> dict:
        """
        Verify a single section interactively.

        Args:
            section_name: Display name of the section
            current: Current values for this section
            field_definitions: List of FieldDef for this section
            extracted_fields: List of fields that were extracted

        Returns:
            Dictionary of verified values
        """
        print(f"\n--- {section_name} ---\n")

        verified = {}
        for field_def in field_definitions:
            if field_def.derived:
                continue  # Skip derived fields, calculated later

            current_value = current.get(field_def.key)
            was_extracted = any(field_def.key in f for f in extracted_fields if f.endswith(field_def.key))

            verified_value = self._verify_field(field_def, current_value, was_extracted)

            if verified_value == "__QUIT__":
                print("\nVerification cancelled.")
                sys.exit(0)

            verified[field_def.key] = verified_value

        return verified

    def _verify_field(
        self,
        field_def: FieldDef,
        current_value: Optional[str],
        was_extracted: bool,
    ) -> Optional[str]:
        """
        Verify a single field.

        Args:
            field_def: Field definition
            current_value: Current value (may be None)
            was_extracted: Whether this value was extracted from analysis

        Returns:
            Verified value, or None if skipped
        """
        # Build the prompt
        status = "(extracted)" if was_extracted and current_value else "(missing)"
        required_marker = "*" if not field_def.optional else ""

        prompt_parts = [f"{required_marker}{field_def.label} {status}"]

        if current_value:
            prompt_parts.append(f" [{current_value}]")

        if field_def.example and not current_value:
            prompt_parts.append(f" (e.g., {field_def.example})")

        prompt = "".join(prompt_parts) + ": "

        # Handle multiline input
        if field_def.multiline:
            return self._get_multiline_input(prompt, current_value)

        # Single line input
        try:
            user_input = input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            return "__QUIT__"

        if user_input.lower() == "quit":
            return "__QUIT__"

        if user_input.lower() == "skip":
            return "Not provided"

        if user_input:
            return user_input
        elif current_value:
            return current_value
        else:
            return "Not provided"

    def _get_multiline_input(self, prompt: str, current_value: Optional[str]) -> Optional[str]:
        """
        Get multiline input from user.

        Args:
            prompt: The prompt to display
            current_value: Current value

        Returns:
            User input or current value
        """
        print(prompt)
        if current_value:
            print(f"  Current value:\n  {current_value}")
        print("  (Enter text, then press Enter twice to finish, or 'skip' to skip)")

        lines = []
        empty_count = 0

        while True:
            try:
                line = input("  > ").strip()
            except (EOFError, KeyboardInterrupt):
                return "__QUIT__"

            if line.lower() == "quit":
                return "__QUIT__"

            if line.lower() == "skip":
                return "Not provided"

            if not line:
                empty_count += 1
                if empty_count >= 2:
                    break
            else:
                empty_count = 0
                lines.append(line)

        if lines:
            return "\n".join(lines)
        elif current_value:
            return current_value
        else:
            return "Not provided"

    def _calculate_derived_fields(self, background: PersonalBackground) -> PersonalBackground:
        """
        Calculate derived fields like age from date of birth.

        Args:
            background: PersonalBackground with verified values

        Returns:
            Updated PersonalBackground with derived fields
        """
        basic_identity = background.get_section("basic_identity")

        # Calculate age from date of birth
        dob_str = basic_identity.get("date_of_birth")
        if dob_str and dob_str != "Not provided":
            try:
                # Try parsing various date formats
                for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%m/%d/%Y"]:
                    try:
                        dob = datetime.strptime(dob_str, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    dob = None

                if dob:
                    today = datetime.now()
                    age = today.year - dob.year
                    if (today.month, today.day) < (dob.month, dob.day):
                        age -= 1
                    basic_identity["age"] = str(age)
            except Exception:
                pass

        background.set_section("basic_identity", basic_identity)
        return background

    def _print_summary(self, background: PersonalBackground) -> None:
        """
        Print a summary of the verification.

        Args:
            background: Verified PersonalBackground
        """
        filled, total = background.count_filled_fields()

        print("\n" + "=" * 60)
        print("             VERIFICATION COMPLETE")
        print("=" * 60)
        print(f"\nFields filled: {filled}/{total}")
        print(f"Verification status: {background.verification_status}")
        print(f"Verified at: {background.last_verified.strftime('%Y-%m-%d %H:%M')}")
