# config.py

import os
from dotenv import load_dotenv

load_dotenv("/opt/ashari-bot/.env")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME", "adgedenkers")
GITHUB_REPO = os.getenv("GITHUB_REPO", "mythos-scroll-library")
