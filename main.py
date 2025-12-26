import requests
import hashlib
import os
from bs4 import BeautifulSoup

URL = "https://service.dungpham.com.vn/thong-bao"
KEYWORD = "kame01td"
REQUIRED_TAGS = ["hệ thống", "5 sao"]

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

HASH_FILE = "sent.txt"
HEADERS = {"User-Agent": "Mozilla/5.0"}

def load_sent():
    if not os.path.exists(HASH_FILE):
        return set()
    with open(HASH_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f)

def save_hash(h):
    with open(HASH_FILE, "a", encoding="utf-8") as f:
        f.write(h + "\n")

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": msg
    }, timeout=10)

def fetch_notices():
    print(">>> Fetching URL:", URL)

    r = requests.get(URL, headers=HEADERS, timeout=15)
    print(">>> Status code:", r.status_code)
    print(">>> Response length:", len(r.text))

    soup = BeautifulSoup(r.text, "html.parser")
    cards = soup.select("div.card")
    print(">>> Found cards:", len(cards))

    results = []

    for i, card in enumerate(cards):
        text = card.get_text(" ", strip=True).lower()
        tags = [b.get_text(strip=True).lower() for b in card.select("span.badge")]

        print(f"--- CARD {i}")
        print("TEXT:", text[:200])
        print("TAGS:", tags)

        results.append({
            "text": text,
            "tags": tags
        })

    return results

def main():
    sent = load_sent()
    notices = fetch_notices()

    for n in notices:
        if not all(tag in n["tags"] for tag in REQUIRED_TAGS):
            continue
        if KEYWORD not in n["text"]:
            continue

        h = hashlib.md5(n["text"].encode()).hexdigest()
        if h in sent:
            continue

        msg = (
            "🔔 THÔNG BÁO HỆ THỐNG – 5 SAO\n"
            f"Keyword: {KEYWORD}\n\n"
            f"{n['text']}"
        )

        send_telegram(msg)
        save_hash(h)

if __name__ == "__main__":
    main()
