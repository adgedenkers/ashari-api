# ashari-bot/users.py

USERS = {
    # Telegram user ID: Display name
    7811548479: "Ka'tuar'el",
    987654321: "Seraphe",
    # Add more users as needed
}

DEFAULT_USER_NAME = "Unknown Scribe"

def get_username(user_id: int) -> str:
    return USERS.get(user_id, DEFAULT_USER_NAME)
