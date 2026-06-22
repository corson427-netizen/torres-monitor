import os
import urllib.request
import urllib.parse
from playwright.sync_api import sync_playwright

# --- HOLIDAY WINDOW CONFIGURATION ---
START_WINDOW_DATES = ["2026-12-28", "2026-12-29", "2026-12-30", "2026-12-31", "2027-01-01", "2027-01-02"]
VERTICE_PORTAL = "https://booking.vertice.travel/"
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

def send_discord_alert(message):
    if not DISCORD_WEBHOOK_URL:
        print("Error: Webhook URL missing.")
        return
    data = urllib.parse.urlencode({"content": message}).encode("utf-8")
    req = urllib.request.Request(DISCORD_WEBHOOK_URL, data=data, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as r:
            print("Targeted alert fired to Discord successfully.")
    except Exception as e:
        print(f"Failed to dispatch alert: {e}")

def verify_consecutive_circuit(page, target_start_date):
    portal_text = page.locator("body").inner_text().lower()
    if "coming soon" in portal_text or "not available" in portal_text:
        return False
        
    try:
        rendered_content = page.content().lower()
        if target_start_date in rendered_content and "sold out" not in rendered_content:
            camps = ["dickson", "perros", "grey", "paine grande"]
            all_clear = all(camp in rendered_content for camp in camps)
            if all_clear:
                return True
    except Exception as e:
        print(f"Parsing engine state failed for {target_start_date}: {e}")
        
    return False

def check_campsites():
    print("Initiating custom calendar sequence via GitHub Actions...")
    with sync_playwright() as p:
        # Added an argument to bypass minor webgl/browser errors
        browser = p.chromium.launch(headless=True, args=["--disable-web-security"])
        page = browser.new_page()
        
        try:
            print(f"Connecting to Vértice Engine: {VERTICE_PORTAL}")
            
            # CHANGED: Changed wait_until to "domcontentloaded" and added a generous 60s timeout
            # This ensures slow background analytic trackings won't crash the script.
            page.goto(VERTICE_PORTAL, wait_until="domcontentloaded", timeout=60000)
            
            # Give the JavaScript an extra 5 seconds just to settle down natively
            page.wait_for_timeout(5000)
            
            match_found = False
            for target_date in START_WINDOW_DATES:
                print(f"Evaluating availability for a potential O-Trek launch on: {target_date}")
                
                if verify_consecutive_circuit(page, target_date):
                    alert_msg = f"🚨 O-TREK LOCKOUT BROKEN! Consecutive spots found starting **{target_date}** matching Dickson -> Los Perros -> Grey -> Paine Grande. Secure immediately: {VERTICE_PORTAL}"
                    send_discord_alert(alert_msg)
                    match_found = True
                    break
            
            if not match_found:
                print("✓ Checked all targets. Holiday window remains systematically locked down.")
                
        except Exception as e:
            print(f"Critical execution error during parsing: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    check_campsites()
