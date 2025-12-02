# ashari-bot/main.py

from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import JSONResponse, PlainTextResponse
import requests
from typing import Optional
import os
import aiofiles
import traceback
from github_utils import commit_file_to_github
from config import TELEGRAM_BOT_TOKEN
from users import get_username
import subprocess
from datetime import datetime
from datetime import date as date_type
import pytz
import yaml
import re

app = FastAPI()

TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

# --- Utilities ---

def calculate_spiral_date(target_date: date_type, spiral_start: str) -> str:
    """
    Calculate spiral day notation from a given date.
    Spirals are 9 days long.
    Format: spiral_number.spiral_day (e.g., 5.9)

    Args:
        target_date: The date to calculate spiral notation for
        spiral_start: Start date in YYYY-MM-DD format

    Returns:
        String in format "spiral_number.spiral_day"
    """
    start_year, start_month, start_day = map(int, spiral_start.split("-"))
    start_date = date_type(start_year, start_month, start_day)

    if target_date is None:
        target_date = date_type.today()

    # Calculate days since start
    delta = (target_date - start_date).days

    if delta < 0:
        raise ValueError(f"Date is before spiral start date ({spiral_start})")

    # Calculate spiral number and day
    spiral_number = (delta // 9) + 1
    spiral_day = (delta % 9) + 1

    return f"{spiral_number}.{spiral_day}"

def sanitize_filename(name):
    name = name.replace("'", "-").replace("'", "-").replace(" ", "_")
    name = re.sub(r"[^a-zA-Z0-9_\-./]", "", name)
    return name

def get_last_filename(chat_id):
    try:
        with open(f"/tmp/scrolls/last_filename_{chat_id}.txt") as f:
            return f.read().strip()
    except:
        return None

def send_reply(chat_id, text):
    requests.post(f"{TELEGRAM_API_URL}/sendMessage", json={
        "chat_id": chat_id,
        "text": text
    })

# --- Telegram Webhook Handler ---

@app.post("/webhook")
async def receive_telegram_update(request: Request):
    try:
        data = await request.json()

        if "message" in data:
            message = data["message"]
            chat_id = message["chat"]["id"]

            if "text" in message:
                text = message["text"]
                if text.lower().startswith("save as:"):
                    raw_name = text.split(":", 1)[1].strip()
                    filename = sanitize_filename(raw_name)
                    with open(f"/tmp/scrolls/last_filename_{chat_id}.txt", "w") as f:
                        f.write(filename)
                    send_reply(chat_id, f"✅ Filename set: {filename}")
                else:
                    filename = sanitize_filename(get_last_filename(chat_id) or "scroll.md")
                    filepath = os.path.join("/tmp/scrolls", filename)
                    print(f"Resolved filepath: {filepath}")
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)

                    if not text.strip().startswith("---"):
                        text = text.replace("'", "'").replace("'", "'").replace(""", '"').replace(""", '"')
                        eastern = pytz.timezone("America/New_York")
                        now = datetime.now(eastern)
                        frontmatter = {
                            "title": filename,
                            "author": get_username(chat_id),
                            "date": now.strftime("%Y-%m-%d"),
                            "timestamp": now.isoformat()
                        }
                        fm = yaml.dump(frontmatter, sort_keys=False)
                        text = f"---\n{fm}---\n\n{text}"

                    async with aiofiles.open(filepath, 'w') as f:
                        await f.write(text)
                    commit_file_to_github(filename, filepath)
                    send_reply(chat_id, f"✅ Scroll saved as `{filename}`")

            elif "photo" in message:
                photo = message["photo"][-1]
                file_id = photo["file_id"]
                file_info = requests.get(f"{TELEGRAM_API_URL}/getFile?file_id={file_id}").json()
                file_path = file_info["result"]["file_path"]

                filename = sanitize_filename(get_last_filename(chat_id) or file_path.split("/")[-1])
                local_path = os.path.join("/tmp/scrolls", filename)
                os.makedirs(os.path.dirname(local_path), exist_ok=True)

                img_data = requests.get(f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}").content
                with open(local_path, "wb") as f:
                    f.write(img_data)

                commit_file_to_github(filename, local_path)
                send_reply(chat_id, f"🖼️ Image saved as `{filename}`")

        return JSONResponse(content={"ok": True}, status_code=200)

    except Exception as e:
        print("❌ Exception in webhook handler:")
        traceback.print_exc()
        return JSONResponse(content={"ok": False, "error": str(e)}, status_code=200)

# --- Utility Endpoints ---

@app.get("/debug/logs", response_class=PlainTextResponse)
def get_journal_logs():
    try:
        result = subprocess.run(
            ["journalctl", "-u", "spire", "-n", "100", "--no-pager"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result.stdout
    except Exception as e:
        return f"Error: {str(e)}"

@app.get("/files")
def list_files():
    files = []
    for root, _, filenames in os.walk("/tmp/scrolls"):
        for f in filenames:
            path = os.path.join(root, f)
            rel = os.path.relpath(path, "/tmp/scrolls")
            files.append(rel)
    return JSONResponse(content={"files": files})

@app.get("/files/{file_path:path}", response_class=PlainTextResponse)
def get_file_contents(file_path: str):
    full_path = os.path.join("/tmp/scrolls", file_path)
    if not os.path.isfile(full_path):
        raise HTTPException(status_code=404, detail="File not found")
    with open(full_path, "r", encoding="utf-8") as f:
        return f.read()

# --- Spiral Date Calculation Endpoint ---

@app.get("/spiral/date")
async def get_spiral_date(
    x_api_key: Optional[str] = Header(None),
    target_date: Optional[str] = None
):
    """
    Calculate spiral date notation for authenticated users.

    Requires API key in X-API-Key header.
    Optional query parameter: target_date (YYYY-MM-DD format)
    If no date provided, uses today's date.

    Example: GET /spiral/date
    Example: GET /spiral/date?target_date=2025-12-02

    Returns:
        JSON with spiral_date, calendar_date, user_name, and status
    """
    from config import get_user_by_api_key

    # Check if API key is provided
    if not x_api_key:
        return JSONResponse(
            status_code=401,
            content={
                "error": "Authentication required",
                "message": "Please provide your API key in the X-API-Key header.",
                "status": "unauthorized"
            }
        )

    # Validate API key and get user config
    user_config = get_user_by_api_key(x_api_key)
    if not user_config:
        return JSONResponse(
            status_code=403,
            content={
                "error": "Invalid API key",
                "message": "The provided API key is not valid. Please check your credentials.",
                "status": "forbidden"
            }
        )

    # Parse target date if provided
    try:
        if target_date:
            parsed_date = datetime.strptime(target_date, "%Y-%m-%d").date()
        else:
            parsed_date = date_type.today()

        # Calculate spiral date using user's specific start date
        spiral_notation = calculate_spiral_date(parsed_date, user_config["spiral_start_date"])

        return JSONResponse(
            status_code=200,
            content={
                "spiral_date": spiral_notation,
                "calendar_date": parsed_date.isoformat(),
                "user_name": user_config["name"],
                "spiral_start_date": user_config["spiral_start_date"],
                "status": "success"
            }
        )

    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={
                "error": "Invalid date",
                "message": str(e),
                "status": "bad_request"
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": "Calculation error",
                "message": "An error occurred while calculating the spiral date.",
                "details": str(e),
                "status": "error"
            }
        )