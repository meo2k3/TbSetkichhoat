import requests
import hashlib
import os
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

URL = "https://service.dungpham.com.vn/thong-bao"
# KEYWORD = "kame01td"
KEYWORD = "chitogejo"
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
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        page = browser.new_page()

        page.goto(URL, timeout=30000)
        page.wait_for_load_state("networkidle")

        # đợi text thông báo xuất hiện
        page.wait_for_selector(
            "div.ant-space-item span.ant-typography",
            timeout=30000
        )

        items = page.query_selector_all(
            "div.ant-space-item span.ant-typography"
        )

        print(">>> Found notices:", len(items))

        for el in items:
            text = el.inner_text().strip().lower()

            # tag logic theo nội dung
            tags = []
            if "[ht]" in text or "hệ thống" in text:
                tags.append("hệ thống")
            if "set kích hoạt" in text or "5 sao" in text:
                tags.append("5 sao")

            results.append({
                "text": text,
                "tags": tags
            })

        browser.close()

    return results

def main():
    print("=== START BOT ===")

    print("BOT_TOKEN exists:", bool(BOT_TOKEN))
    print("CHAT_ID exists:", bool(CHAT_ID))

    try:
        notices = fetch_notices()
        print("TOTAL NOTICES:", len(notices))
    except Exception as e:
        print("❌ FETCH ERROR:", e)
        return

    sent = load_sent()
    print("SENT HASH COUNT:", len(sent))

    for i, n in enumerate(notices):
        print(f"\n--- NOTICE {i} ---")
        print("TEXT:", n["text"][:200])
        print("TAGS:", n["tags"])
        print("KEYWORD MATCH:", KEYWORD in n["text"])
        print("REQUIRED TAGS OK:",
              all(tag in n["tags"] for tag in REQUIRED_TAGS))

        if not all(tag in n["tags"] for tag in REQUIRED_TAGS):
            continue
        if KEYWORD not in n["text"]:
            continue

        h = hashlib.md5(n["text"].encode()).hexdigest()
        if h in sent:
            print("⚠️ SKIP: already sent")
            continue

        print("✅ SENDING TELEGRAM")
        send_telegram("✅ TEST MESSAGE FROM ACTION")
        save_hash(h)

    print("=== END BOT ===")


if __name__ == "__main__":
    main()
