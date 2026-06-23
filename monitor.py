import os
import urllib.request
import urllib.parse
from playwright.sync_api import sync_playwright

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

BASE_URL = "https://booking.lastorres.com/"
TARGET_CHECKIN = "18/03/2026"
TARGET_CHECKOUT = "19/03/2026"

def send_discord_alert(message):
    if not DISCORD_WEBHOOK_URL:
        print("❌ Webhook missing.")
        return
    data = urllib.parse.urlencode({"content": message}).encode("utf-8")
    req = urllib.request.Request(DISCORD_WEBHOOK_URL, data=data, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as r:
            print("📬 Alert sent to Discord!")
    except Exception as e:
        print(f"❌ Discord failed: {e}")

def check_las_torres():
    print("🤖 Initializing Automated Interaction Engine...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        
        try:
            print(f"🔗 Landing on raw portal: {BASE_URL}")
            page.goto(BASE_URL, wait_until="networkidle", timeout=60000)
            page.wait_for_timeout(5000)
            
            # --- INTERACTION PHASE: NATIVE DROPDOWN SELECT ---
            print("👤 Forcing guest count to 2 Adults...")
            adult_select = page.locator("select[id*='adults']")
            
            if adult_select.count() > 0:
                # Use native select_option instead of click to bypass visibility issues on raw dropdowns
                adult_select.first.select_option(value="2", force=True)
                print("✓ Successfully set adults to 2 using value selection.")
            else:
                print("⚠️ Direct adult select element not found, attempting fallback...")
            
            print(f"📅 Locating date inputs...")
            # Target the text fields where dates are entered
            date_inputs = page.locator("input[id*='date'], input[id*='check'], .roi-search-engine__date-input").all()
            
            # Let's inspect the page content right now to see if we've loaded the search context
            visible_text = page.locator("body").inner_text()
            lines = [line.strip() for line in visible_text.split("\n") if line.strip()]
            print(f"📝 Current Page Snippet: {lines[:8]}")
            
            # --- FALLBACK CHECK ---
            visible_text_lower = visible_text.lower()
            for camp in ["seron", "cuernos", "chileno"]:
                if camp in visible_text_lower:
                    if "sold out" not in visible_text_lower and "agotado" not in visible_text_lower:
                        print(f"🚨 INVENTORY FOUND FOR {camp}!")
                        send_discord_alert(f"🚨 SUCCESS: Active slot found for **{camp}**! Check: {BASE_URL}")
                    else:
                        print(f"🔒 {camp} is visible but sold out.")
                else:
                    print(f"🔍 {camp} sector not visible in current view frame.")
                    
        except Exception as e:
            print(f"❌ Interface automation dropped: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    check_las_torres()
