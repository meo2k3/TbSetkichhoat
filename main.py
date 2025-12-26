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
# MAIN
# ======================
def main():
    print("=== START BOT ===")

    sent = load_sent()

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox"]
        )
        page = browser.new_page()
        page.set_viewport_size({"width": 1280, "height": 900})

        # 1. mở web
        print(">>> Open page")
        page.goto(URL, timeout=30000)
        time.sleep(3)

        # 2. mở dropdown danh mục
        print(">>> Open category dropdown")
        page.locator("div.ant-select-selector").first.click(force=True)
        time.sleep(1)

        # 3. chọn "Hệ thống"
        print(">>> Select category:", CATEGORY_NAME)
        page.locator(
            "div.ant-select-item-option-content",
            has_text=CATEGORY_NAME
        ).click(force=True)

        print(">>> Wait 5s after category")
        time.sleep(5)

        # 4. chọn server 5 sao trong card Máy chủ
        print(">>> Select server:", SERVER_NAME)
        page.locator(
            "div.ant-card:has-text('Máy chủ') button span",
            has_text=SERVER_NAME
        ).click(force=True)

        print(">>> Wait 5s after server")
        time.sleep(5)

        # 5. lấy các thông báo
        print(">>> Fetch notices")
        items = page.query_selector_all(
            "div[style*='border-bottom'] span.ant-typography"
        )

        print(">>> Found items:", len(items))

        for i in range(0, len(items), 2):
            title = items[i].inner_text().strip()

            print(f"\n--- NOTICE {i//2} ---")
            print(title)

            if KEYWORD.lower() not in title.lower():
                continue

            h = hashlib.md5(title.encode("utf-8")).hexdigest()
            if h in sent:
                print("⚠️ Already sent")
                continue

            msg = (
                f"🔔 THÔNG BÁO {SERVER_NAME.upper()} – {CATEGORY_NAME}\n\n"
                f"{title}"
            )

            send_telegram(msg)
            save_hash(h)
            sent.add(h)

            print("✅ SENT")

        browser.close()

    print("=== END BOT ===")


if __name__ == "__main__":
    main()
