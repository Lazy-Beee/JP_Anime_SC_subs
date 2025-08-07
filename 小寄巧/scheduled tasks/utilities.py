import requests
import time
import datetime

BOT_TOKEN = ""
CHAT_ID = ""

def time_stamp(no_space=False):
    if no_space:
        return datetime.datetime.fromtimestamp(time.time()).strftime('%Y%m%d-%H%M')
    else:
        return f"[{datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')}]"

def send_telegram_message(message):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        response = requests.post(url, data=payload)
        if response.status_code != 200:
            print(f"{time_stamp()} Failed to send Telegram message: {response.text}")
    except Exception as e:
        print(f"{time_stamp()} Telegram error: {e}")
