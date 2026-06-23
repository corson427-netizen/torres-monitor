import os
import urllib.request
import urllib.parse
from playwright.sync_api import sync_playwright

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

# --- MATCHING YOUR MARCH 18-19 TEST CONFIGURATION ---
TARGET_CHECKIN = "18-03-2026"
TARGET_CHECKOUT = "19-03-2026"

TARGETS = [
    {"label": "Serón (TEST March 18-19)", "camp_id": "seron"},
    {"label": "Cuernos (TEST March 18-19)", "camp_id": "cuernos"},
    {"label": "Chileno (TEST March 18-19)", "camp_id": "chileno"}
]

def send_discord_alert(message):
    if not DISCORD_WEBHOOK_URL:
        print("❌ Webhook configuration missing.")
        return
    data = urllib.parse.urlencode({"content": message}).encode("utf-8")
    req = urllib.request.Request(DISCORD_WEBHOOK_URL, data=data, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as r:
            print("📬 Alert transmitted to Discord successfully!")
    except Exception as e:
        print(f"❌ Discord transmission failed: {e}")

def check_las_torres():
    print("🤖 Initializing Cloud Native Engine Parser (March 18-19)...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        
        try:
            print("🔗 Connecting to engine layout root...")
            page.goto("https://booking.lastorres.com/es/", wait_until="networkidle", timeout=60000)
            page.wait_for_timeout(3000)
            
            # Map elements using native input fields to bypass the interface framework
            print("⌨️ Populating text engine layers directly...")
            
            # Target check-in element arrays
            checkin_selectors = ["input[name*='checkin']", "input[id*='checkin']", "input[class*='date']", "input[type='text']"]
            checkin_filled = False
            for selector in checkin_selectors:
                try:
                    el = page.locator(selector).first
                    if el.count() > 0:
                        el.click()
                        page.keyboard.press("Control+A")
                        page.keyboard.press("Backspace")
                        page.keyboard.type(TARGET_CHECKIN, delay=20)
                        checkin_filled = True
                        break
                except:
                    continue
                    
            # Target check-out element arrays
            checkout_selectors = ["input[name*='checkout']", "input[id*='checkout']", "input[type='text']"]
            for selector in checkout_selectors:
                try:
                    el = page.locator(selector).nth(1) if "type" in selector else page.locator(selector).first
                    if el.count() > 0:
                        el.click()
                        page.keyboard.press("Control+A")
                        page.keyboard.press("Backspace")
                        page.keyboard.type(TARGET_CHECKOUT, delay=20)
                        page.keyboard.press("Enter")
                        break
                except:
                    continue

            # Locate submission nodes
            search_button = page.locator("button[type='submit'], input[type='submit'], .btn-search").first
            print("💥 Triggering full session evaluation query...")
            search_button.click()
            
            print("⏳ Processing downstream reservation components (15s)...")
            page.wait_for_timeout(15000)
            
            visible_text = page.locator("body").inner_text()
            visible_text_lower = visible_text.lower()
            
            lines = [line.strip() for line in visible_text.split("\n") if line.strip()]
            print(f"\n📊 ACTIVE FRAME RENDER SNIPPET:\n{lines[:15]}")
            
            for target in TARGETS:
                label = target["label"]
                camp_id = target["camp_id"]
                
                has_camp = camp_id in visible_text_lower
                has_pricing = any(marker in visible_text_lower for marker in ["$", "usd", "clp", "total"])
                is_sold_out = any(flag in visible_text_lower for flag in ["sold out", "agotado", "no availability", "no disponible"])
                
                print(f"\n🧐 Sector Evaluation for {label}:")
                print(f"   -> Node Discovered: {has_camp} | Price Detected: {has_pricing} | Sold Out Flags: {is_sold_out}")
                
                if has_camp and has_pricing and not is_sold_out:
                    print("🚨 TARGET CONDITIONAL CRITERIA MET!")
                    send_discord_alert(f"🧪 CLOUD WORKFLOW MATCH: Bookable room configurations discovered for **{label}** on March 18-19!")
                else:
                    print("🔒 Status: Unavailable / Locked.")
                    
        except Exception as e:
            print(f"❌ Core engine execution fault: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    check_las_torres()
