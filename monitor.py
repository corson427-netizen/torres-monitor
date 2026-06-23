import os
import urllib.request
import urllib.parse
from playwright.sync_api import sync_playwright

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

# --- TARGET MATRIX WITH DIRECT DEEP-LINK PARAMETERS ---
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
    print("🤖 Launching Deep-Link Search Engine...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--disable-web-security", "--no-sandbox"])
        page = browser.new_page()
        
        for target in TARGETS:
            label = target["label"]
            camp_id = target["camp_id"]
            search_url = target["url"]
            
            print(f"\n🚀 EVALUATING LIVE GRID: {label}")
            try:
                page.goto(search_url, wait_until="networkidle", timeout=60000)
                page.wait_for_timeout(10000)  # Extended settle time to let dynamic availability load
                
                visible_text = page.locator("body").inner_text().lower()
                html_content = page.content().lower()
                
                # Verify we aren't scanning a blank structural container
                if "adults" not in visible_text and "check-in" not in visible_text:
                    print("⚠️ Frame didn't render cleanly. Skipping fallback safety locks.")
                    continue
                
                # Check for explicit signs of a campsite row being unblocked
                # True availability usually renders pricing components (USD / CLP signs) or specific selection slots
                has_price_tier = "$" in visible_text or "usd" in visible_text or "clp" in visible_text
                
                # Explicit text blocks that appear inside specific camp option cards when filled
                is_explicitly_sold_out = "no availability" in visible_text or "sold out" in visible_text or "not available" in visible_text
                
                print(f"   -> Site layout has pricing indicators: {has_price_tier}")
                print(f"   -> Site explicitly shows sold-out status: {is_explicitly_sold_out}")
                
                # The Golden Trigger: The specific camp identifier MUST be on screen, 
                # a pricing component must exist, and it cannot have explicit sold-out banners.
                if camp_id in visible_text and has_price_tier and not is_explicitly_sold_out:
                    # Double check to filter out the expensive premium setups
                    ground_keywords = ["individual", "sitio", "solo sitio", "pitch", "own tent", "camping basic", "sin acampar"]
                    is_cheap_spot = any(kw in visible_text or kw in html_content for kw in ground_keywords)
                    
                    if is_cheap_spot:
                        print("🚨 TRUE ALERT CONDITION MET!")
                        send_discord_alert(f"🚨 CONFIRMED OPENING: 2-person ground space detected for **{label}**! Book immediately: {search_url}")
                    else:
                        print("🔒 Filtered: Camp found, but only premium glamping setups are open.")
                else:
                    print("🔒 Locked: Site shows zero bookable slots for this sector matrix right now.")
                    
            except Exception as e:
                print(f"❌ Error checking {label}: {e}")
                
        browser.close()

if __name__ == "__main__":
    check_las_torres()
