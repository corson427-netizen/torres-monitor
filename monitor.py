import os
import urllib.request
import urllib.parse
from playwright.sync_api import sync_playwright

# --- TARGET CONFIGURATION (LAS TORRES GROUND SITES FOR 2 PAX) ---
LAS_TORRES_URL = "https://booking.lastorres.com/"
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

# Laser-targeted dates matching your precise transit flow
TARGETS = [
    {"camp": "seron", "date": "2026-12-30", "label": "Serón (Dec 30-31) - 2 Person Ground Site"},
    {"camp": "cuernos", "date": "2026-12-04", "label": "Cuernos (Dec 4-5) - 2 Person Ground Site"},
    {"camp": "chileno", "date": "2026-12-05", "label": "Chileno (Dec 5-6) - 2 Person Ground Site"}
]

def send_discord_alert(message):
    if not DISCORD_WEBHOOK_URL:
        print("Error: Webhook URL missing.")
        return
    data = urllib.parse.urlencode({"content": message}).encode("utf-8")
    req = urllib.request.Request(DISCORD_WEBHOOK_URL, data=data, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as r:
            print("2-Person Ground spot match alert fired to Discord!")
    except Exception as e:
        print(f"Failed to dispatch alert: {e}")

def check_las_torres():
    print("Initiating Las Torres 2-Person Ground-Only validation sequence...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--disable-web-security", "--no-sandbox"])
        page = browser.new_page()
        
        try:
            print(f"Connecting to Las Torres Portal: {LAS_TORRES_URL}")
            page.goto(LAS_TORRES_URL, wait_until="domcontentloaded", timeout=60000)
            
            # Allow time for the dynamic pricing configuration to read 2-person occupancy options
            page.wait_for_timeout(12000)
            
            dom_content = page.content().lower()
            
            # Explicit strict markers looking for ground-only spots that support 2 people
            ground_markers = ["individual", "sitio", "solo sitio", "pitch", "own tent", "camping sin acampar"]
            party_size_markers = ["2 people", "2 personas", "double", "2 pax", "2 person tent"]
            
            has_ground_spot = any(marker in dom_content for marker in ground_markers)
            has_two_pax_capacity = any(marker in dom_content for marker in party_size_markers)
            
            alerts_triggered = 0
            
            for target in TARGETS:
                camp_key = target["camp"]
                date_key = target["date"]
                label = target["label"]
                
                # Check for campsite location and date in current source frame
                if camp_key in dom_content and date_key in dom_content:
                    
                    # Ensure it is not explicitly marked as sold out or fully booked
                    if "sold out" not in dom_content and "no disponible" not in dom_content:
                        
                        # VERIFICATION: Must explicitly be a cheap ground spot AND accommodate 2 people
                        if has_ground_spot and has_two_pax_capacity:
                            alert_msg = f"💰 2-PERSON GROUND SITE OPEN! **{label}** detected. Secure your platform spot immediately: {LAS_TORRES_URL}"
                            send_discord_alert(alert_msg)
                            alerts_triggered += 1
                        else:
                            print(f" -> Structural trace found for {label}, but 2-person ground space conditions not fully met.")
                            
            if alerts_triggered == 0:
                print("✓ Check complete. No bare ground 2-person sites open for these exact dates yet.")
                
        except Exception as e:
            print(f"Critical execution error during parsing: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    check_las_torres()
