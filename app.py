import requests
import time
import hashlib
import os
from bs4 import BeautifulSoup

# ================= CẤU HÌNH =================
URL = "https://service.dungpham.com.vn/thong-bao"
INTERVAL = 300  # 5 phút

BOT_TOKEN = "7595884145:AAHSaetDabglE8nQnL3v1VAUJAj-t8uijec"
CHAT_ID = "5886715013"

REQUIRED_TAGS = ["hệ thống", "5 sao"]
KEYWORD = "kame01td"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

HASH_FILE = "sent.txt"
# ============================================


def load_sent():
    if not os.path.exists(HASH_FILE):
        return set()
    with open(HASH_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f)


def save_hash(h):
    with open(HASH_FILE, "a", encoding="utf-8") as f:
        f.write(h + "\n")


sent_hashes = load_sent()


def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text
    }
    requests.post(url, data=payload, timeout=10)


def fetch_notices():
    r = requests.get(URL, headers=HEADERS, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")

    notices = []

    # mỗi thông báo là 1 card
    for card in soup.select("div.card"):
        text = card.get_text(" ", strip=True).lower()

        tags = [
            badge.get_text(strip=True).lower()
            for badge in card.select("span.badge")
        ]

        notices.append({
            "text": text,
            "tags": tags
        })

    return notices


def main():
    send_telegram("🤖 Bot theo dõi Hệ thống – 5 sao đã khởi động")

    while True:
        try:
            notices = fetch_notices()

            for n in notices:
                if not all(tag in n["tags"] for tag in REQUIRED_TAGS):
                    continue

                if KEYWORD not in n["text"]:
                    continue

                h = hashlib.md5(n["text"].encode()).hexdigest()
                if h in sent_hashes:
                    continue

                msg = (
                    "🔔 THÔNG BÁO HỆ THỐNG – 5 SAO\n"
                    f"Keyword: {KEYWORD}\n\n"
                    f"{n['text']}"
                )

                send_telegram(msg)
                sent_hashes.add(h)
                save_hash(h)

        except Exception as e:
            send_telegram(f"⚠️ Bot lỗi: {e}")

        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
