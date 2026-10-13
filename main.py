
import os
import requests
from flask import Flask, request

app = Flask(__name__)

TOKEN = os.environ.get("BOT_TOKEN", "")
API = f"https://api.telegram.org/bot{TOKEN}"

def send_message(chat_id, text):
    return requests.post(
        f"{API}/sendMessage",
        json={"chat_id": chat_id, "text": text},
        timeout=20
    )

def search_music(chat_id, query):
    try:
        response = requests.get(
            "https://itunes.apple.com/search",
            params={"term": query, "entity": "song", "limit": 3},
            timeout=20
        )
        response.raise_for_status()
        songs = response.json().get("results", [])

        if not songs:
            send_message(chat_id, "သီချင်းမတွေ့ပါ။ နာမည်ပြန်စမ်းပါ။")
            return

        for song in songs:
            name = song.get("trackName", "Unknown")
            artist = song.get("artistName", "Unknown")
            link = song.get("trackViewUrl", "")
            preview = song.get("previewUrl")

            caption = f"{name} - {artist}\n{link}"

            sent = False
            if preview:
                result = requests.post(
                    f"{API}/sendAudio",
                    json={
                        "chat_id": chat_id,
                        "audio": preview,
                        "caption": caption
                    },
                    timeout=30
                )
                sent = result.ok

            if not sent:
                send_message(chat_id, caption)

    except Exception:
        send_message(chat_id, "ရှာမရသေးပါ။ ခဏနားပြီး ပြန်စမ်းပါ။")

def handle_update(update):
    message = update.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "").strip()

    if not chat_id or not text:
        return

    if text.startswith("/start"):
        send_message(
            chat_id,
            "မင်္ဂလာပါ! သီချင်းနာမည် သို့မဟုတ် အဆိုတော်နာမည် ရိုက်ရှာပါ။"
        )
    elif text.startswith("/"):
        send_message(chat_id, "သီချင်းနာမည်ကို ရိုက်ပို့ပါ။")
    else:
        search_music(chat_id, text)

@app.route("/", methods=["GET"])
def home():
    return "Music Bot service is running."

@app.route("/telegram-webhook", methods=["POST"])
def telegram_webhook():
    update = request.get_json(silent=True) or {}
    try:
        handle_update(update)
    except Exception:
        app.logger.exception("Update processing failed")
    return "OK", 200

def setup_webhook():
    if not TOKEN:
        app.logger.error("BOT_TOKEN environment variable is missing")
        return

    base_url = os.environ.get("RENDER_EXTERNAL_URL", "").rstrip("/")
    if base_url:
        try:
            response = requests.post(
                f"{API}/setWebhook",
                json={"url": base_url + "/telegram-webhook"},
                timeout=20
            )
            app.logger.info("Webhook setup: %s", response.text)
        except Exception:
            app.logger.exception("Webhook setup failed")

setup_webhook()
