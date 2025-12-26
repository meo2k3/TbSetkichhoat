import os
import time
import hashlib
import requests
from playwright.sync_api import sync_playwright

# ======================
# CONFIG
# ======================
URL = "https://service.dungpham.com.vn/thong-bao"

CATEGORY_NAME = "Hệ thống"
SERVER_NAME = "5 sao"
KEYWORD = "chitogejo"

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

HASH_FILE = "sent.txt"


# ======================
# UTILS
# ======================
def load_sent():
    if not os.path.exists(HASH_FILE):
        return set()
    with open(HASH_FILE, "r", encoding="utf-8") as f:
        return set(f.read().splitlines())


def save_hash(h):
    with open(HASH_FILE, "a", encoding="utf-8") as f:
        f.write(h + "\n")


def send_telegram(msg):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": msg},
        timeout=10
    )


# ======================
# MAIN LOGIC
# ======================
def main():
    print("=== START BOT ===")

    sent = load_sent()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print(">>> Open page")
        page.goto(URL, timeout=30000)

        # ----------------------
        # 1. chọn danh mục
        # ----------------------
        print(">>> Select category:", CATEGORY_NAME)
        page.locator(
            "button.ant-btn span",
            has_text=CATEGORY_NAME
        ).first.click(force=True)

        print(">>> Wait 5s after category")
        time.sleep(5)

        # ----------------------
        # 2. chọn server
        # ----------------------
        print(">>> Select server:", SERVER_NAME)
        page.locator(
            "button.ant-btn span",
            has_text=SERVER_NAME
        ).first.click(force=True)

        print(">>> Wait 5s after server")
        time.sleep(5)

        # ----------------------
        # 3. lấy nội dung thẻ
        # ----------------------
        print(">>> Fetch cards")

        cards = page.query_selector_all("div.ant-card-body")

        print(">>> Cards found:", len(cards))

        for i, card in enumerate(cards):
            text = card.inner_text().strip()
            print(f"\n--- CARD {i} ---")
            print(text)

            if KEYWORD.lower() not in text.lower():
                continue

            h = hashlib.md5(text.encode("utf-8")).hexdigest()
            if h in sent:
                print("⚠️ Already sent")
                continue

            msg = (
                f"🔔 THÔNG BÁO {SERVER_NAME.upper()} – {CATEGORY_NAME}\n\n"
                f"{text}"
            )

            send_telegram(msg)
            save_hash(h)
            sent.add(h)

            print("✅ SENT")

        browser.close()

    print("=== END BOT ===")


if __name__ == "__main__":
    main()
