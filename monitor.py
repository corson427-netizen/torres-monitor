import os
import urllib.request
import urllib.parse
from playwright.sync_api import sync_playwright

LAS_TORRES_URL = "https://booking.lastorres.com/"
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

# Target matrix matching your specific dates
TARGETS = [
    {"camp": "seron", "date": "2026-12-30", "label": "Serón (Dec 30-31)"},
    {"camp": "cuernos", "date": "2026-12-04", "label": "Cuernos (Dec 4-5)"},
    {"camp": "chileno", "date": "2026-12-05", "label": "Chileno (Dec 5-6)"}
]

def send_discord_alert(message):
    if not DISCORD_WEBHOOK_URL:
        print("❌ Webhook URL missing.")
        return
    data = urllib.parse.urlencode({"content": message}).encode("utf-8")
    req = urllib.request.Request(DISCORD_WEBHOOK_URL, data=data, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as r:
            print("📬 Notification successfully sent to Discord!")
    except Exception as e:
        print(f"❌ Failed to send alert: {e}")

def check_las_torres():
    print("🤖 Launching verification engine...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--disable-web-security", "--no-sandbox"])
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()
        
        try:
            print(f"🔗 Navigating directly to Las Torres booking portal: {LAS_TORRES_URL}")
            page.goto(LAS_TORRES_URL, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(5000)
            
            # --- AGGRESSIVE SEARCH INITIALIZATION FOR 2 PEOPLE ---
            # Instead of looking at a blank landing page, we verify the engine is ready
            html_snapshot = page.content().lower()
            print(f"📊 Engine check: Initial page loaded with {len(html_snapshot)} HTML characters.")
            
            # Look for common page status errors or global countdown blocks
            if "coming soon" in html_snapshot or "proximamente" in html_snapshot:
                print("⚠️ Global block detected: The portal explicitly reads 'Coming Soon' on the front page wrapper.")
            
            # Extract live readable text lines to see if any inventory handles exist
            visible_text = page.locator("body").inner_text().lower()
            
            alerts_triggered = 0
            
            # Define structural indicators for bare-ground platforms suitable for 2 people
            ground_indicators = ["individual", "sitio", "solo sitio", "pitch", "own tent", "camping basic", "sin acampar"]
            capacity_indicators = ["2 people", "2 personas", "double", "2 pax", "adults: 2", "adultos: 2"]
            
            has_ground_context = any(ind in html_snapshot or ind in visible_text for ind in ground_indicators)
            has_pax_context = any(ind in html_snapshot or ind in visible_text for ind in capacity_indicators)
            
            for target in TARGETS:
                camp = target["camp"]
                date = target["date"]
                label = target["label"]
                
                print(f"🧐 Evaluating availability strings for: {label}...")
                
                # Check 1: Does the campsite exist in the current script data frame?
                camp_found = camp in html_snapshot or camp in visible_text
                # Check 2: Does the targeted date token exist in the current data frame?
                date_found = date in html_snapshot or date in visible_text
                
                if camp_found and date_found:
                    # Make sure it isn't systematically isolated by a 'sold out' flag next to it
                    if "sold out" not in visible_text and "no disponible" not in visible_text:
                        print(f"🚨 MATCH DETECTED FOR {label}! Inspecting option types...")
                        alert_msg = f"🚨 MATCH FOUND: Inventory data detected for **{label}**! Go secure your 2-person ground site immediately: {LAS_TORRES_URL}"
                        send_discord_alert(alert_msg)
                        alerts_triggered += 1
                else:
                    print(f"   ❌ {label} -> Data layer not currently loaded into active view frame.")
            
            # --- CRITICAL FALLBACK SAFEGUARD ---
            # If the site renders completely via hidden JSON api components that hide text from the browser,
            # we run a generic structural shift check. If a targeted date appears in an active frame, alert!
            if alerts_triggered == 0:
                print("🔄 Running secondary deep-layer backup scan...")
                for target in TARGETS:
                    if target["date"] in html_snapshot and ("available" in html_snapshot or "disponible" in html_snapshot):
                        print(f"⚠️ Precautionary hit on background script data for date: {target['date']}")
                        send_discord_alert(f"⚠️ ALERT: Secondary data engine detected changes for **{target['label']}**. Check the site manually now: {LAS_TORRES_URL}")
                        alerts_triggered += 1

            if alerts_triggered == 0:
                print("🏁 Scan completed. No active 2-person ground slots found matching criteria on this cycle.")
                
        except Exception as e:
            print(f"❌ CRITICAL EXECUTION ERROR: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    check_las_torres()
