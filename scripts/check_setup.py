"""
Setup verification script.
Checks that all requirements are met before running the processor.
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'


def check_item(name, condition, required=True):
    """Check a single requirement and print result."""
    if condition:
        print(f"{GREEN}✓{RESET} {name}")
        return True
    else:
        marker = f"{RED}✗{RESET}" if required else f"{YELLOW}!{RESET}"
        print(f"{marker} {name}")
        return False if required else True


def main():
    """Run all setup checks."""
    print("\n" + "=" * 60)
    print("Second Brain Setup Verification")
    print("=" * 60 + "\n")

    all_good = True
    repo_root = Path(__file__).parent.parent

    # Check Python version
    print("Python Environment:")
    python_version = sys.version_info
    all_good &= check_item(
        f"Python 3.11+ (found {python_version.major}.{python_version.minor})",
        python_version >= (3, 11),
    )

    # Check required packages
    print("\nRequired Packages:")
    packages = {
        'anthropic': 'Anthropic Claude API',
        'telegram': 'Telegram Bot API',
        'git': 'GitPython',
        'yaml': 'PyYAML',
        'slugify': 'python-slugify',
        'dotenv': 'python-dotenv',
    }

    for module, name in packages.items():
        try:
            __import__(module)
            check_item(name, True)
        except ImportError:
            all_good &= check_item(name, False)

    # Check directory structure
    print("\nDirectory Structure:")
    required_dirs = ['config', 'scripts', 'specs', 'notes', 'reflections', 'sources', 'hubs']
    for dir_name in required_dirs:
        dir_path = repo_root / dir_name
        check_item(f"{dir_name}/ directory", dir_path.exists())

    # Check configuration files
    print("\nConfiguration Files:")
    check_item(
        "config/config.yaml",
        (repo_root / "config" / "config.yaml").exists(),
    )

    env_file = repo_root / "config" / ".env"
    env_exists = env_file.exists()
    check_item("config/.env", env_exists)

    if not env_exists:
        print(f"  {YELLOW}→{RESET} Copy config/.env.example to config/.env")

    # Check environment variables
    print("\nEnvironment Variables:")
    if env_exists:
        load_dotenv(env_file)

        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        telegram_chat = os.getenv("TELEGRAM_CHAT_ID")

        all_good &= check_item(
            "ANTHROPIC_API_KEY",
            anthropic_key and anthropic_key != "your_anthropic_api_key_here",
        )

        check_item(
            "TELEGRAM_BOT_TOKEN",
            telegram_token and telegram_token != "your_bot_token_here",
            required=False,
        )

        check_item(
            "TELEGRAM_CHAT_ID",
            telegram_chat and telegram_chat != "your_chat_id_here",
            required=False,
        )
    else:
        all_good = False

    # Check Git repository
    print("\nGit Repository:")
    try:
        import git
        repo = git.Repo(repo_root)
        check_item("Git repository initialized", True)
        check_item(f"Current branch: {repo.active_branch.name}", True)

        # Check for uncommitted changes
        if repo.is_dirty():
            print(f"  {YELLOW}→{RESET} Repository has uncommitted changes")
    except:
        all_good &= check_item("Git repository initialized", False)

    # Summary
    print("\n" + "=" * 60)
    if all_good:
        print(f"{GREEN}All critical checks passed!{RESET}")
        print("\nYou can now run:")
        print("  python scripts/test_add_capture.py  - Add a test capture")
        print("  python scripts/processor.py         - Process captures")
    else:
        print(f"{RED}Some critical checks failed.{RESET}")
        print("\nPlease fix the issues above and run this script again.")
        print("\nSee SETUP.md for detailed instructions.")

    print("=" * 60 + "\n")

    return 0 if all_good else 1


if __name__ == "__main__":
    sys.exit(main())
