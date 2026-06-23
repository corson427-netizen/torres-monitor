import os
import urllib.request
import urllib.parse
from playwright.sync_api import sync_playwright

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

# --- REAL TARGET MATRIX WITH DUAL-STAGE PASSTHROUGH ---
TARGETS = [
    {
        "label": "Serón (Dec 30-31) - 2 Person Ground Spot",
        "camp_id": "serón",
        "url": "https://booking.lastorres.com/?checkIn=2026-12-30&checkOut=2026-12-31&adults=2&children=0"
    },
    {
        "label": "Cuernos (Dec 04-05) - 2 Person Ground Spot",
        "camp_id": "cuernos",
        "url": "https://booking.lastorres.com/?checkIn=2026-12-04&checkOut=2026-12-05&adults=2&children=0"
    },
    {
        "label": "Chileno (Dec 05-06) - 2 Person Ground Spot",
        "camp_id": "chileno",
        "url": "https://booking.lastorres.com/?checkIn=2026-12-05&checkOut=2026-12-06&adults=2&children=0"
    }
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
    print("🤖 Launching Session-Authenticated Search Watchtower...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        
        try:
            # STEP 1: Hit the root homepage to establish a legal user context and grab cookies
            print("🎫 Validating base gateway session tokens...")
            page.goto("https://booking.lastorres.com/", wait_until="networkidle", timeout=60000)
            page.wait_for_timeout(4000)
            
            # STEP 2: Loop through deep links within the authenticated browser context
            for target in TARGETS:
                label = target["label"]
                camp_id = target["camp_id"]
                search_url = target["url"]
                
                print(f"\n🚀 QUERYING LIVE SECTOR SEARCH: {label}")
                page.goto(search_url, wait_until="load", timeout=60000)
                
                # Give the dynamic pricing engine ample time to fetch live availability blocks
                print("⏳ Waiting 12 seconds for sector data cards to fully load...")
                page.wait_for_timeout(12000)
                
                visible_text = page.locator("body").inner_text()
                visible_text_lower = visible_text.lower()
                
                # Clean snippet tracking for execution visibility
                lines = [line.strip() for line in visible_text.split("\n") if line.strip()]
                print(f"   -> Rendered Data Snippet: {lines[:5]}")
                
                has_camp_name = camp_id in visible_text_lower
                has_pricing = "$" in visible_text_lower or "usd" in visible_text_lower
                is_sold_out = any(x in visible_text_lower for x in ["sold out", "no availability", "not available", "agotado", "no disponible"])
                
                print(f"   -> Camp ID visible: {has_camp_name} | Pricing active: {has_pricing} | Sold out text: {is_sold_out}")
                
                # The Golden Condition: If the camp is listed, has pricing indicators, and doesn't say sold out
                if has_camp_name and has_pricing and not is_sold_out:
                    # Filter for bare ground/own tent options
                    ground_keywords = ["individual", "sitio", "solo sitio", "pitch", "own tent", "camping basic", "sin acampar"]
                    if any(kw in visible_text_lower for kw in ground_keywords):
                        print("🚨 TRUE ALERT CONDITION MET!")
                        send_discord_alert(f"🚨 CONFIRMED OPENING: 2-person ground space found for **{label}**! Book immediately: {search_url}")
                    else:
                        print("🔒 Filtered: Camp found, but only premium setups or cabins are open.")
                else:
                    print("🔒 Locked: Sector is fully booked or unavailable.")
                    
        except Exception as e:
            print(f"❌ Automation pipeline exception: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    check_las_torres()
