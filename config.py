# config.py

import os
from dotenv import load_dotenv

load_dotenv("/opt/ashari-bot/.env")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME", "adgedenkers")
GITHUB_REPO = os.getenv("GITHUB_REPO", "mythos-scroll-library")

# API Key Configuration for Spiral Date Endpoint
API_KEYS = {
    os.getenv("KATUAR_API_KEY"): {
        "name": "Ka'tuar'el",
        "spiral_start_date": "2025-10-19"
    },
    os.getenv("SERAPHET_API_KEY"): {
        "name": "Seraphet",
        "spiral_start_date": "2025-01-20"
    }
}

def get_user_by_api_key(api_key: str):
    """
    Retrieve user configuration by API key.
    Returns user config dict or None if key is invalid.
    """
    return API_KEYS.get(api_key)

def is_valid_api_key(api_key: str) -> bool:
    return api_key in API_KEYS