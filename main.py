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

    page.wait_for_selector("button.ant-btn span", timeout=20000)

    page.locator(
        "button.ant-btn span",
        has_text=server_name
    ).first.click(force=True)

    page.wait_for_timeout(1500)


def select_category(page, category_name):
    print(f">>> Selecting category: {category_name}")

    page.wait_for_selector("div.ant-select-selector", timeout=20000)
    page.click("div.ant-select-selector", force=True)

    page.wait_for_selector("div.ant-select-item-option-content")

    page.locator(
        "div.ant-select-item-option-content",
        has_text=category_name
    ).first.click(force=True)

    page.wait_for_timeout(1500)


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

        # chọn server & category
        select_server(page, SERVER_NAME)
        select_category(page, CATEGORY_NAME)

        print(">>> Waiting for notice cards")
        page.wait_for_selector(
            "div[style*='border-bottom']",
            timeout=30000
        )

        cards = page.query_selector_all(
            "div[style*='border-bottom']"
        )

        print(">>> Cards found:", len(cards))

        for card in cards:
            spans = card.query_selector_all("span.ant-typography")
            if not spans:
                continue

            texts = [s.inner_text().strip() for s in spans]
            full_text = "\n".join(texts)

            results.append(full_text)

        browser.close()

    return results


# ======================
# MAIN
# ======================
def main():
    print("=== START BOT ===")
    print("BOT_TOKEN exists:", bool(BOT_TOKEN))
    print("CHAT_ID exists:", bool(CHAT_ID))

    if not BOT_TOKEN or not CHAT_ID:
        print("❌ Missing Telegram config")
        return

    try:
        notices = fetch_notices()
    except Exception as e:
        print("❌ FETCH ERROR:", e)
        return

    print("TOTAL NOTICES:", len(notices))

    sent = load_sent()
    print("SENT HASH COUNT:", len(sent))

    for i, text in enumerate(notices):
        print(f"\n--- NOTICE {i} ---")
        print(text)

        if KEYWORD.lower() not in text.lower():
            continue

        h = hashlib.md5(text.encode()).hexdigest()
        if h in sent:
            print("⚠️ SKIP (already sent)")
            continue

        msg = (
            f"🔔 THÔNG BÁO {SERVER_NAME.upper()} – {CATEGORY_NAME}\n\n"
            f"{text}"
        )

        send_telegram(msg)
        save_hash(h)
        print("✅ SENT TO TELEGRAM")

    print("=== END BOT ===")


if __name__ == "__main__":
    main()
