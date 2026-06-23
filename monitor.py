import os
import urllib.request
import urllib.parse
from playwright.sync_api import sync_playwright

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

# --- MARCH 18-19 TARGETS ---
TARGETS = [
    {"label": "Serón (TEST March 18-19)", "camp_id": "serón", "url": "https://booking.lastorres.com/?checkIn=2026-03-18&checkOut=2026-03-19&adults=2&children=0"},
    {"label": "Cuernos (TEST March 18-19)", "camp_id": "cuernos", "url": "https://booking.lastorres.com/?checkIn=2026-03-18&checkOut=2026-03-19&adults=2&children=0"},
    {"label": "Chileno (TEST March 18-19)", "camp_id": "chileno", "url": "https://booking.lastorres.com/?checkIn=2026-03-18&checkOut=2026-03-19&adults=2&children=0"}
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
    print("🤖 Launching Visual Inspector Engine...")
    
    with sync_playwright() as p:
        # Launch Chromium using a standard desktop window layout
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        
        for target in TARGETS:
            label = target["label"]
            camp_id = target["camp_id"]
            search_url = target["url"]
            
            print(f"\n🖥️ VISUALLY INSPECTING: {label}")
            try:
                page.goto(search_url, wait_until="networkidle", timeout=60000)
                page.wait_for_timeout(10000)  # Generous 10 seconds for layout painting
                
                # Extract exactly what a human would read off the glass screen
                visible_text = page.locator("body").inner_text()
                visible_text_lower = visible_text.lower()
                
                print(f"   -> Successfully extracted {len(visible_text)} characters of visible text.")
                
                # Let's print out a small snippet of the page text to see what's actually showing up
                lines = [line.strip() for line in visible_text.split("\n") if line.strip()]
                print(f"   -> Top page text fragments: {lines[:6]}")
                
                # Check for explicit campground keywords vs availability flags
                has_camp_name = camp_id in visible_text_lower
                has_pricing = "$" in visible_text_lower or "usd" in visible_text_lower
                
                print(f"   -> Sector name '{camp_id}' found on screen: {has_camp_name}")
                print(f"   -> Price/Currency indicators found on screen: {has_pricing}")
                
                # If the camp name is on screen and we see pricing, let's trace it
                if has_camp_name:
                    # Look for explicit block rules
                    sold_out_flags = ["sold out", "no availability", "not available", "agotado", "no disponible"]
                    is_sold_out = any(flag in visible_text_lower for flag in sold_out_flags)
                    
                    print(f"   -> Local sold-out indicators detected: {is_sold_out}")
                    
                    if not is_sold_out and has_pricing:
                        print("🚨 MATCH CRITERIA TRIGGERED!")
                        send_discord_alert(f"🧪 INSPECTOR MATCH: Grid looks active for **{label}**! Verify here: {search_url}")
                    else:
                        print("🔒 Locked: Option card is present but systematically flagged as full.")
                else:
                    print("🔒 Locked: Campground sector card is completely absent from visual workspace.")
                    
            except Exception as e:
                print(f"❌ Parsing failure on target window: {e}")
                
        browser.close()

if __name__ == "__main__":
    check_las_torres()
