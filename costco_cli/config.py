"""Configuration management for Costco CLI."""

import os
import json
from pathlib import Path

# Config directory and file
CONFIG_DIR = Path.home() / ".costco-cli"
CONFIG_FILE = CONFIG_DIR / "config.json"


def ensure_config_dir():
    """Ensure the config directory exists."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    """Load configuration from file."""
    ensure_config_dir()
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_config(config: dict):
    """Save configuration to file."""
    ensure_config_dir()
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def get_api_key() -> str | None:
    """Get the Anthropic API key from env var or config file."""
    # First check environment variable
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        return api_key

    # Fall back to config file
    config = load_config()
    return config.get("api_key")


def set_api_key(api_key: str):
    """Save the API key to config file."""
    config = load_config()
    config["api_key"] = api_key
    save_config(config)


def get_chrome_profile_path() -> str:
    """Get the Chrome profile path."""
    config = load_config()
    return config.get("chrome_profile", str(CONFIG_DIR / "chrome-profile"))
