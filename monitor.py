import os
import urllib.request
import urllib.parse
from playwright.sync_api import sync_playwright

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

# --- TARGET MATRIX WITH DIRECT DEEP-LINK PARAMETERS ---
# We inject checkout dates (next day) and adults=2 directly into the URL query parameters
TARGETS = [
    {
        "label": "Serón (Dec 30-31) - 2 Person Ground Spot",
        "camp_id": "seron",
        "url": "https://booking.lastorres.com/?checkIn=2026-12-30&checkOut=2026-12-31&adults=2&children=0"
    },
    {
        "label": "Cuernos (Dec 04-05) - 2 Person Ground Spot",
        "camp_id": "cuernos",
        "url": "https://booking.lastorres.com/?checkIn=2026-12-04&checkOut=2026-12-05&adults=2&children=0"
    },
    {
        "label": "Chileno (Dec 05-6) - 2 Person Ground Spot",
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
            
            print(f"\n🚀 FORCING DIRECT SEARCH: {label}")
            try:
                # Go directly to the pre-filled search results URL
                page.goto(search_url, wait_until="networkidle", timeout=60000)
                page.wait_for_timeout(8000)  # Give the internal calendar grid 8 seconds to settle
                
                html_content = page.content().lower()
                visible_text = page.locator("body").inner_text().lower()
                
                print(f"📊 Scraped {len(html_content)} characters from active results frame.")
                
                # Verify that the booking engine actually loaded and isn't a blank shell
                if "check-in" in visible_text or "adults" in visible_text or "disponibilidad" in visible_text:
                    print("✅ Confirmed: Search engine page successfully rendered live data.")
                
                # Check for explicit budget/ground spot indicators
                ground_keywords = ["individual", "sitio", "solo sitio", "pitch", "own tent", "camping basic", "sin acampar", "parcela"]
                is_ground_page = any(kw in html_content or kw in visible_text for kw in ground_keywords)
                
                # Look for signs of availability
                is_sold_out = "sold out" in visible_text or "no disponible" in visible_text or "agotado" in visible_text
                
                # Log state to GitHub so you can see exactly what it found on the page
                print(f"   -> Ground spot text signatures found: {is_ground_page}")
                print(f"   -> Explicit sold out text detected: {is_sold_out}")
                
                # If the site indicates things are available, or if the "sold out" blanket is missing, sound the alarm
                if not is_sold_out and ("book" in visible_text or "reservar" in visible_text or "seleccionar" in visible_text):
                    print("🚨 ALERT CONDITION MET!")
                    send_discord_alert(f"🚨 2-PERSON GROUND SPOT OPEN! **{label}** appears active in search results. Grab it: {search_url}")
                else:
                    print("🔒 Locked: Portal shows fully booked for this date combo.")
                    
            except Exception as e:
                print(f"❌ Error checking {label}: {e}")
                
        browser.close()

if __name__ == "__main__":
    check_las_torres()
