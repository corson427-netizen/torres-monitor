import os
import urllib.request
import urllib.parse
from playwright.sync_api import sync_playwright

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

# --- MARCH 18-19 TEST CONFIGURATION ---
TARGET_CHECKIN = "18-03-2026"   # DD-MM-YYYY format matching their visual calendar placeholder
TARGET_CHECKOUT = "19-03-2026"  # DD-MM-YYYY format matching their visual calendar placeholder

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
    print("🤖 Launching Physical Interaction Watchtower (March 18-19)...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = browser.new_context(viewport={"width": 1440, "height": 900}, locale="es-CL")
        page = context.new_page()
        
        try:
            print("🔗 Opening booking portal...")
            page.goto("https://booking.lastorres.com/", wait_until="networkidle", timeout=60000)
            page.wait_for_timeout(4000)
            
            # Target the check-in field by placeholder text rather than technical ID attributes
            print("⌨️ Simulating keystrokes for Check-In Date...")
            checkin_field = page.locator("input[placeholder*='Entrada'], input[placeholder*='Check-in'], input[placeholder*='Check in']").first
            checkin_field.click()
            page.wait_for_timeout(500)
            # Clear field out completely and physically type the date string
            page.keyboard.press("Control+A")
            page.keyboard.press("Backspace")
            page.keyboard.type(TARGET_CHECKIN, delay=100)
            page.keyboard.press("Enter")
            page.wait_for_timeout(1000)
            
            print("⌨️ Simulating keystrokes for Check-Out Date...")
            checkout_field = page.locator("input[placeholder*='Salida'], input[placeholder*='Check-out'], input[placeholder*='Check out']").first
            checkout_field.click()
            page.wait_for_timeout(500)
            page.keyboard.press("Control+A")
            page.keyboard.press("Backspace")
            page.keyboard.type(TARGET_CHECKOUT, delay=100)
            page.keyboard.press("Enter")
            page.wait_for_timeout(1000)
            
            # Fire the query
            search_btn = page.locator("button[type='submit'], .btn-search, button:has-text('Buscar'), button:has-text('SEARCH')").first
            print("💥 Triggering search click event...")
            search_btn.click()
            
            print("⏳ Processing database response frames (15s)...")
            page.wait_for_timeout(15000)
            
            visible_text = page.locator("body").inner_text()
            visible_text_lower = visible_text.lower()
            
            lines = [line.strip() for line in visible_text.split("\n") if line.strip()]
            print(f"\n📊 ACTIVE FRAME RENDER SNIPPET:\n{lines[:10]}")
            
            for target in TARGETS:
                label = target["label"]
                camp_id = target["camp_id"]
                
                has_camp = camp_id in visible_text_lower
                has_pricing = "$" in visible_text_lower or "usd" in visible_text_lower
                is_sold_out = any(flag in visible_text_lower for flag in ["sold out", "no availability", "agotado"])
                
                print(f"\n🧐 Checking status for {label}:")
                print(f"   -> Camp Match: {has_camp} | Pricing Active: {has_pricing} | Terminated Status: {is_sold_out}")
                
                if has_camp and has_pricing and not is_sold_out:
                    print("🚨 TRUE ALERT CONDITION MET!")
                    send_discord_alert(f"🧪 INTERACTION TEST MATCH: Active bookable space found for **{label}** on March 18-19!")
                else:
                    print("🔒 Locked / Unavailable.")
                    
        except Exception as e:
            print(f"❌ Pipeline exception tripped: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    check_las_torres()
