# ashari-bot/github_utils.py

import base64
import requests
import os

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = "adgedenkers/mythos-scroll-library"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/contents/"

def commit_file_to_github(filename, local_path):
    with open(local_path, "rb") as f:
        content = f.read()
    b64_content = base64.b64encode(content).decode()

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    # Check if the file already exists
    get_url = GITHUB_API_URL + filename
    get_resp = requests.get(get_url, headers=headers)
    sha = get_resp.json().get("sha") if get_resp.status_code == 200 else None

    commit_message = f"Add/update {filename}"
    payload = {
        "message": commit_message,
        "content": b64_content,
        "branch": "main"
    }

    if sha:
        payload["sha"] = sha

    put_resp = requests.put(get_url, headers=headers, json=payload)

    if not put_resp.ok:
        print("❌ GitHub upload failed:", put_resp.text)
        raise Exception(f"GitHub upload failed: {put_resp.text}")

