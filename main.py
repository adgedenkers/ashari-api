# ashari-bot/main.py

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
import requests
import os
import aiofiles
import traceback
from github_utils import commit_file_to_github
from config import TELEGRAM_BOT_TOKEN
from users import get_username
import subprocess
from datetime import datetime
import pytz
import yaml
import re

app = FastAPI()

TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

# --- Utilities ---

def sanitize_filename(name):
    name = name.replace("’", "-").replace("'", "-").replace(" ", "_")
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
                        text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
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
