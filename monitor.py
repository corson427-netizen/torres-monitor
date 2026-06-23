import os
import urllib.request
import urllib.parse
from playwright.sync_api import sync_playwright

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

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
                page.goto(search_url, wait_until="load", timeout=60000)
                
                print("⏳ Waiting for the booking interface to render elements...")
                # We tell the browser to wait specifically for the body text to become active
                page.wait_for_selector("body", timeout=30000)
                # Hard extra pause to let the pricing engine API calls finish in the background
                page.wait_for_timeout(12000)
                
                visible_text = page.locator("body").inner_text().lower()
                html_content = page.content().lower()
                
                # Double check if we are stuck on a loading screen
                if "loading" in visible_text and len(visible_text) < 500:
                    print("⚠️ Page is still stuck on a loading spinner. Retrying extra wait...")
                    page.wait_for_timeout(10000)
                    visible_text = page.locator("body").inner_text().lower()

                print(f"📊 Live text length analyzed: {len(visible_text)} characters.")
                
                # Look for pricing indicators that mean the grid loaded successfully
                has_price_tier = "$" in visible_text or "usd" in visible_text or "clp" in visible_text
                is_explicitly_sold_out = "no availability" in visible_text or "sold out" in visible_text or "not available" in visible_text or "agotado" in visible_text
                
                print(f"   -> Pricing tokens visible: {has_price_tier}")
                print(f"   -> Sold-out tokens visible: {is_explicitly_sold_out}")
                
                # TRIGGER CRITERIA:
                # If the camp name is on the page, and it's NOT showing a giant "sold out" wall, let's look closer
                if camp_id in visible_text:
                    if is_explicitly_sold_out:
                        print("🔒 Locked: Portal explicitly reads 'Sold Out' or 'No Availability' for this camp.")
                    elif has_price_tier:
                        # Make sure it's the cheap spot
                        ground_keywords = ["individual", "sitio", "solo sitio", "pitch", "own tent", "camping basic", "sin acampar"]
                        is_cheap_spot = any(kw in visible_text or kw in html_content for kw in ground_keywords)
                        
                        if is_cheap_spot:
                            print("🚨 TRUE ALERT CONDITION MET!")
                            send_discord_alert(f"🚨 CONFIRMED OPENING: 2-person ground space detected for **{label}**! Book immediately: {search_url}")
                        else:
                            print("🔒 Filtered: Space found, but only for premium glamping setups.")
                    else:
                        print("🔒 Locked: Camp row is visible but no bookable price options are rendered.")
                else:
                    print("🔒 Locked: This specific campground option is completely hidden/unavailable for this date.")
                    
            except Exception as e:
                print(f"❌ Error checking {label}: {e}")
                
        browser.close()

if __name__ == "__main__":
    check_las_torres()
