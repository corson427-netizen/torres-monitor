import os
import urllib.request
import urllib.parse
from playwright.sync_api import sync_playwright

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

# --- MARCH 18-19 TEST CONFIGURATION ---
TARGET_CHECKIN = "18-03-2026"
TARGET_CHECKOUT = "19-03-2026"

TARGETS = [
    {"label": "Serón (TEST March 18-19)", "camp_id": "seron"},
    {"label": "Cuernos (TEST March 18-19)", "camp_id": "cuernos"},
    {"label": "Chileno (TEST March 18-19)", "camp_id": "chileno"}
]

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
    print("🤖 Launching Targeted Direct-Frame Watchtower (March 18-19)...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        
        try:
            # Bypass the landing splash wrapper and open the actual isolated reservation frame document
            print("🔗 Connecting directly to inner reservation template...")
            page.goto("https://booking.lastorres.com/en/", wait_until="networkidle", timeout=60000)
            page.wait_for_timeout(3000)
            
            # Select inputs using explicit index positions to avoid layout differences
            print("⌨️ Inputting target search criteria...")
            inputs = page.locator("input[type='text']")
            
            if inputs.count() >= 2:
                # Interact with Check-in
                inputs.nth(0).click()
                page.keyboard.press("Control+A")
                page.keyboard.press("Backspace")
                page.keyboard.type(TARGET_CHECKIN, delay=50)
                page.keyboard.press("Tab")
                page.wait_for_timeout(500)
                
                # Interact with Check-out
                page.keyboard.press("Control+A")
                page.keyboard.press("Backspace")
                page.keyboard.type(TARGET_CHECKOUT, delay=50)
                page.keyboard.press("Enter")
                page.wait_for_timeout(1000)
            else:
                # Fallback to direct attribute mapping if input structure shifts
                page.locator(".check-in-input, [name*='checkin'], #checkin").first.fill(TARGET_CHECKIN)
                page.locator(".check-out-input, [name*='checkout'], #checkout").first.fill(TARGET_CHECKOUT)

            # Locate the booking trigger button
            search_button = page.locator("button[type='submit'], .search-btn, button:has-text('Book'), button:has-text('Buscar')").first
            print("💥 Executing search...")
            search_button.click()
            
            print("⏳ Parsing system search results (12s)...")
            page.wait_for_timeout(12000)
            
            visible_text = page.locator("body").inner_text()
            visible_text_lower = visible_text.lower()
            
            lines = [line.strip() for line in visible_text.split("\n") if line.strip()]
            print(f"\n📊 ACTIVE FRAME RENDER SNIPPET:\n{lines[:12]}")
            
            for target in TARGETS:
                label = target["label"]
                camp_id = target["camp_id"]
                
                has_camp = camp_id in visible_text_lower
                has_pricing = any(symbol in visible_text_lower for symbol in ["$", "usd", "clp"])
                is_sold_out = any(flag in visible_text_lower for flag in ["sold out", "no availability", "agotado", "no disponible"])
                
                print(f"\n🧐 Evaluating {label}:")
                print(f"   -> Found: {has_camp} | Price Detected: {has_pricing} | Sold Out Flags: {is_sold_out}")
                
                if has_camp and has_pricing and not is_sold_out:
                    print("🚨 TARGET TRIGGER CONDITION MET!")
                    send_discord_alert(f"🧪 FRAME INTERACTION MATCH: Active availability discovered for **{label}** on March 18-19!")
                else:
                    print("🔒 Unavailable.")
                    
        except Exception as e:
            print(f"❌ Automation pipeline broke: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    check_las_torres()
