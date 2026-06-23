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
    print("🤖 Launching Coordinate-Based Spatial Watchtower (March 18-19)...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        # Lock in a standard large screen viewport to keep the layout grid fixed
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        
        try:
            print("🔗 Connecting to portal...")
            page.goto("https://booking.lastorres.com/", wait_until="networkidle", timeout=60000)
            page.wait_for_timeout(5000)
            
            # Find the primary date/search controller block on the screen
            form_box = page.locator("form, div[class*='search'], div[class*='bar'], div[class*='widget']").first
            
            if form_box.count() > 0:
                box = form_box.bounding_box()
                print(f"📐 Found search container matrix: x={box['x']}, y={box['y']}, w={box['width']}, h={box['height']}")
                
                # Tap the check-in area (left side of the search container)
                print("🎯 Tapping Check-In cell via coordinate matrix...")
                page.mouse.click(box["x"] + (box["width"] * 0.25), box["y"] + (box["height"] * 0.5))
                page.wait_for_timeout(1000)
                
                # Type the date sequence directly into whatever active focus layer opened
                page.keyboard.press("Control+A")
                page.keyboard.press("Backspace")
                page.keyboard.type(TARGET_CHECKIN, delay=60)
                page.wait_for_timeout(500)
                page.keyboard.press("Tab")
                
                # Type the checkout date sequence
                page.keyboard.press("Control+A")
                page.keyboard.press("Backspace")
                page.keyboard.type(TARGET_CHECKOUT, delay=60)
                page.keyboard.press("Enter")
                page.wait_for_timeout(1000)
            else:
                print("⚠️ Structural form box missing. Attempting direct body typing fallback...")
                page.keyboard.press("Tab")
                page.keyboard.type(TARGET_CHECKIN, delay=50)

            # Locate the booking trigger button safely using text definitions
            search_button = page.locator("button:has-text('Buscar'), button:has-text('Search'), button[type='submit']").first
            print("💥 Submitting search matrix...")
            search_button.click()
            
            print("⏳ Capturing server data cards (12s)...")
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
                is_sold_out = any(flag in visible_text_lower for flag in ["sold out", "no availability", "agotado"])
                
                print(f"\n🧐 Status report for {label}:")
                print(f"   -> Camp Match: {has_camp} | Price Detected: {has_pricing} | Terminated/Sold Out: {is_sold_out}")
                
                if has_camp and has_pricing and not is_sold_out:
                    print("🚨 TARGET ALERT TRIGGERED!")
                    send_discord_alert(f"🧪 COORDINATE INTERACTION MATCH: Bookable slots discovered for **{label}** on March 18-19!")
                else:
                    print("🔒 Locked / Unavailable.")
                    
        except Exception as e:
            print(f"❌ Automation pipeline broke: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    check_las_torres()
