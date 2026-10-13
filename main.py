
import os
import time
import requests

TOKEN = os.environ.get("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN is missing")

API = f"https://api.telegram.org/bot{TOKEN}"

def send_message(chat_id, text):
    requests.post(
        f"{API}/sendMessage",
        json={"chat_id": chat_id, "text": text},
        timeout=20
    )

def search_music(chat_id, query):
    try:
        response = requests.get(
            "https://itunes.apple.com/search",
            params={
                "term": query,
                "entity": "song",
                "limit": 5
            },
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

            caption = f"{name} - {artist}\nသီချင်းစာမျက်နှာ: {link}"

            if preview:
                result = requests.post(
                    f"{API}/sendAudio",
                    json={
                        "chat_id": chat_id,
                        "audio": preview,
                        "caption": caption
                    },
                    timeout=40
                )
                if result.ok:
                    continue

            send_message(chat_id, caption)

    except Exception:
        send_message(
            chat_id,
            "ရှာဖွေရာမှာ အမှားဖြစ်နေပါတယ်။ နောက်မှပြန်စမ်းပါ။"
        )

def main():
    offset = None
    send_message_id = None

    while True:
        try:
            response = requests.get(
                f"{API}/getUpdates",
                params={"offset": offset, "timeout": 25},
                timeout=35
            )
            response.raise_for_status()

            for update in response.json().get("result", []):
                offset = update["update_id"] + 1
                message = update.get("message", {})
                chat = message.get("chat", {})
                chat_id = chat.get("id")
                text = message.get("text", "").strip()

                if not chat_id or not text:
                    continue

                if text.startswith("/start"):
                    send_message(
                        chat_id,
                        "မင်္ဂလာပါ။ သီချင်းနာမည် သို့မဟုတ် "
                        "အဆိုတော်နာမည်ကို ရိုက်ရှာနိုင်ပါတယ်။"
                    )
                elif text.startswith("/"):
                    send_message(chat_id, "သီချင်းနာမည်ကို ရိုက်ပို့ပါ။")
                else:
                    search_music(chat_id, text)

        except Exception:
            time.sleep(5)

if __name__ == "__main__":
    main()
