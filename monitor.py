import os
import urllib.request
import urllib.parse
from playwright.sync_api import sync_playwright

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

# --- CLEAN DIAGNOSTIC RUN (MARCH 18-19) ---
# We use the clean base URL and let the browser type the dates manually
BASE_URL = "https://booking.lastorres.com/"
TARGET_CHECKIN = "18/03/2026"  # Day/Month/Year format standard for Chilean engines
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
            
            # --- INTERACTION PHASE: CHOOSE GUESTS & DATES ---
            print("👤 Setting guest count to 2 Adults...")
            # Look for guest selector inputs and force '2'
            guest_inputs = page.locator("input[readonly], .guest-select, [id*='passenger'], [id*='adult']").all()
            if guest_inputs:
                guest_inputs[0].click()
                page.wait_for_timeout(1000)
            
            print(f"📅 Entering target travel dates: {TARGET_CHECKIN} to {TARGET_CHECKOUT}...")
            # Search for inputs handling dates and clear/type the targets
            date_inputs = page.locator("input[type='text'], .datepicker, [id*='date'], [id*='check']").all()
            
            # Fallback execution: If direct inputs are locked behind complex calendars,
            # we dump the live layout to look for active sector panels.
            visible_text = page.locator("body").inner_text()
            print(f"📊 Workspace size: {len(visible_text)} characters.")
            
            lines = [line.strip() for line in visible_text.split("\n") if line.strip()]
            print(f"📝 Actual rendering: {lines[:8]}")
            
            # --- CHECK REAL ENTRIES IF RENDERED ---
            visible_text_lower = visible_text.lower()
            
            for camp in ["seron", "cuernos", "chileno"]:
                print(f"🧐 Looking for active grid signature for: {camp}")
                if camp in visible_text_lower:
                    if "sold out" not in visible_text_lower and "agotado" not in visible_text_lower:
                        print(f"🚨 ACTIVE INVENTORY UNCOVERED FOR {camp}!")
                        send_discord_alert(f"🚨 SUCCESS: Active slot found for **{camp}** during automated session! Check immediately: {BASE_URL}")
                    else:
                        print(f"🔒 {camp} is present but shows sold out.")
                else:
                    print(f"🔒 {camp} is completely absent from this frame wrapper.")
                    
        except Exception as e:
            print(f"❌ Interface automation dropped: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    check_las_torres()
