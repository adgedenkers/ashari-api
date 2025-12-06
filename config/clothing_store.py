# config/clothing_store.py

import os
from dotenv import load_dotenv

load_dotenv("/opt/ashari-bot/.env")

# Clothing Store Configuration
CLOTHING_STORE_CONFIG = {
    "DATABASE": os.getenv("CLOTHING_DATABASE", "clothing_store.db"),
    "UPLOAD_FOLDER": os.getenv("UPLOAD_FOLDER", "uploads"),
    "GITHUB_REPO": os.getenv("GITHUB_CLOTHING_REPO", "mythos-clothing-store"),
    "GITHUB_USERNAME": os.getenv("GITHUB_USERNAME", "adgedenkers"),
    "GITHUB_TOKEN": os.getenv("GITHUB_TOKEN"),
    "DEFAULT_PRICE_MULTIPLIER": float(os.getenv("DEFAULT_PRICE_MULTIPLIER", "1.0")),
    "DEFAULT_GENDER": os.getenv("DEFAULT_GENDER", "Unisex"),
    "DEFAULT_SIZE": os.getenv("DEFAULT_SIZE", "XL")
}

def get_clothing_config():
    return CLOTHING_STORE_CONFIG
