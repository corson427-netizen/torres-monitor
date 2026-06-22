import os
import urllib.request
import urllib.parse
from playwright.sync_api import sync_playwright

TARGET_URL = "https://torreshike.com/"
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

def send_discord_alert(message):
    if not DISCORD_WEBHOOK_URL:
        print("Error: Webhook URL missing.")
        return
    data = urllib.parse.urlencode({"content": message}).encode("utf-8")
    req = urllib.request.Request(DISCORD_WEBHOOK_URL, data=data, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as r:
            print("Notification sent to Discord!")
    except Exception as e:
        print(f"Failed to send alert: {e}")

def check_campsites():
    print("Launching browser via GitHub Actions...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(TARGET_URL, wait_until="networkidle")
            page_text = page.locator("body").inner_text().lower()
            
            # Change criteria
            is_still_closed = "opening season" in page_text or "coming soon" in page_text
            new_season_live = "2026-2027" in page_text or "2026/2027" in page_text
            
            if not is_still_closed or new_season_live:
                send_discord_alert(f"🚨 ALERT: Torres del Paine bookings are open! Check now: {TARGET_URL}")
            else:
                print("Sites are still locked down.")
        except Exception as e:
            print(f"Error checking site: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    check_campsites()
