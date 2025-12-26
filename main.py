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
KEYWORD = "chitogejo"   # keyword cần lọc

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
        data={
            "chat_id": CHAT_ID,
            "text": msg,
            "disable_web_page_preview": True
        },
        timeout=10
    )


# ======================
# PLAYWRIGHT ACTIONS
# ======================
def select_server(page, server_name):
    print(f">>> Selecting server: {server_name}")

    server_card = page.locator(
        "div.ant-card",
        has_text="Máy chủ"
    )

    btn = server_card.locator(
        "button.ant-btn span",
        has_text=server_name
    ).first

    btn.scroll_into_view_if_needed()
    btn.click(force=True)

    # đợi data reload
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1500)


def select_category(page, category_name):
    print(f">>> Selecting category: {category_name}")

    category_card = page.locator(
        "div.ant-card",
        has_text="Danh mục"
    )

    btn = category_card.locator(
        "button.ant-btn span",
        has_text=category_name
    ).first

    btn.scroll_into_view_if_needed()
    btn.click(force=True)

    page.wait_for_load_state("networkidle")
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

        # 1. chọn server
        select_server(page, SERVER_NAME)

        # 2. chọn category
        select_category(page, CATEGORY_NAME)

        # 3. đợi cards render
        print(">>> Waiting for notice cards")
        page.wait_for_selector(
            "div.ant-card-body",
            timeout=30000
        )

        cards = page.query_selector_all("div.ant-card-body")

        print(f">>> Cards found: {len(cards)}")

        for card in cards:
            spans = card.query_selector_all("span.ant-typography")
            if not spans:
                continue

            text = "\n".join(
                s.inner_text().strip()
                for s in spans
                if s.inner_text().strip()
            )

            if text:
                results.append({"text": text})

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

    for i, n in enumerate(notices):
        text = n["text"]
        print(f"\n--- NOTICE {i} ---")
        print(text)

        # so sánh keyword
        if KEYWORD.lower() not in text.lower():
            continue

        h = hashlib.md5(text.encode("utf-8")).hexdigest()
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
