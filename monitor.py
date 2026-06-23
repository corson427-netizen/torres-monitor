import os
import urllib.request
import urllib.parse
from playwright.sync_api import sync_playwright

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

# --- MARCH 18-19 TEST CRITERIA ---
TARGET_CHECKIN = "2026-03-18"
TARGET_CHECKOUT = "2026-03-19"

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
    print("🤖 Launching March 18-19 Live Data Test...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        
        try:
            print("🔗 Loading official base booking portal...")
            page.goto("https://booking.lastorres.com/", wait_until="networkidle", timeout=60000)
            page.wait_for_timeout(5000)
            
            # Use native page-level scripts to directly apply search criteria to the widget engine
            print(f"⚙️ Injecting Target Parameters: Dates={TARGET_CHECKIN} to {TARGET_CHECKOUT}, Adults=2")
            page.evaluate(f"""() => {{
                const checkInInput = document.querySelector("input[id*='check-in'], input[id*='checkin']");
                const checkOutInput = document.querySelector("input[id*='check-out'], input[id*='checkout']");
                if(checkInInput) checkInInput.value = '{TARGET_CHECKIN}';
                if(checkOutInput) checkOutInput.value = '{TARGET_CHECKOUT}';
                
                const adultSelect = document.querySelector("select[id*='adults']");
                if(adultSelect) adultSelect.value = '2';
            }}""")
            
            # Look for and click the primary booking submit button
            search_btn = page.locator("button[type='submit'], .btn-search, [class*='search-button']")
            if search_btn.count() > 0:
                print("💥 Clicking Search Button...")
                search_btn.first.click()
                page.wait_for_timeout(12000)  # Wait for the results to process and render
            else:
                print("⚠️ Search button not found by standard signature, waiting for lazy load layout anyway...")
                page.wait_for_timeout(10000)
            
            visible_text = page.locator("body").inner_text()
            visible_text_lower = visible_text.lower()
            
            lines = [line.strip() for line in visible_text.split("\n") if line.strip()]
            print(f"\n📊 ACTIVE FRAME RENDER SNIPPET:\n{lines[:10]}")
            
            for target in TARGETS:
                label = target["label"]
                camp_id = target["camp_id"]
                
                has_camp = camp_id in visible_text_lower
                has_pricing = "$" in visible_text_lower or "usd" in visible_text_lower or "clp" in visible_text_lower
                is_sold_out = any(flag in visible_text_lower for flag in ["sold out", "no availability", "not available", "agotado", "no disponible"])
                
                print(f"\n🧐 Checking status for {label}:")
                print(f"   -> Found on screen: {has_camp} | Prices visible: {has_pricing} | Sold out status: {is_sold_out}")
                
                if has_camp and has_pricing and not is_sold_out:
                    print("🚨 TRUE ALERT CONDITION MET!")
                    send_discord_alert(f"🧪 DIAGNOSTIC TEST MATCH: Found active availability for **{label}** on March 18-19!")
                else:
                    print("🔒 Locked / Unavailable.")
                    
        except Exception as e:
            print(f"❌ Test aborted due to error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    check_las_torres()
