import os
import hashlib
import requests
from playwright.sync_api import sync_playwright

# ======================
# CONFIG
# ======================
URL = "https://service.dungpham.com.vn/thong-bao"

SERVER_NAME = "5 sao"
CATEGORY_NAME = "Hệ thống"
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
        return set(line.strip() for line in f)


def save_hash(h):
    with open(HASH_FILE, "a", encoding="utf-8") as f:
        f.write(h + "\n")


def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(
        url,
        data={"chat_id": CHAT_ID, "text": msg},
        timeout=10
    )


# ======================
# PLAYWRIGHT ACTIONS
# ======================
def select_server(page, server_name):
    print(f">>> Selecting server: {server_name}")

    btn = page.locator(
        "button.ant-btn span",
        has_text=server_name
    ).first

    btn.scroll_into_view_if_needed()
    btn.click(force=True)

    # ⏳ đợi server ACTIVE (màu tím)
    page.wait_for_selector(
        "button.ant-btn[style*='background: rgb(128, 90, 213)'] span",
        timeout=15000
    )


def select_category(page, category_name):
    print(f">>> Selecting category: {category_name}")

    page.click("div.ant-select-selector", force=True)

    page.locator(
        "div.ant-select-item-option-content",
        has_text=category_name
    ).first.click(force=True)

    page.wait_for_timeout(1000)


# ======================
# FETCH DATA
# ======================
def fetch_notices():
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        page = browser.new_page()
        page.set_viewport_size({"width": 1280, "height": 900})

        print(">>> Opening page")
        page.goto(URL, timeout=30000)
        page.wait_for_load_state("networkidle")

        # 1️⃣ chọn server
        select_server(page, SERVER_NAME)

        # 2️⃣ chọn category
        select_category(page, CATEGORY_NAME)

        # 3️⃣ đợi danh sách render LẠI
        print(">>> Waiting for notices")
        page.wait_for_selector(
            "div.ant-card-body > div[style*='border-bottom'] span.ant-typography",
            timeout=20000
        )

        cards = page.query_selector_all(
            "div.ant-card-body > div[style*='border-bottom']"
        )

        print(">>> Cards found:", len(cards))

        for card in cards:
            title = card.query_selector(
                "span.ant-typography[style*='font-weight: 600']"
            )
            if not title:
                continue

            text = title.inner_text().strip()
            results.append(text)

        browser.close()

    return results


# ======================
# MAIN
# ======================
def main():
    print("=== START BOT ===")

    if not BOT_TOKEN or not CHAT_ID:
        print("❌ Missing Telegram config")
        return

    notices = fetch_notices()
    sent = load_sent()

    for text in notices:
        if KEYWORD.lower() not in text.lower():
            continue

        h = hashlib.md5(text.encode()).hexdigest()
        if h in sent:
            continue

        msg = f"🔔 THÔNG BÁO {SERVER_NAME.upper()} – {CATEGORY_NAME}\n\n{text}"
        send_telegram(msg)
        save_hash(h)

        print("✅ SENT:", text)

    print("=== END BOT ===")


if __name__ == "__main__":
    main()
