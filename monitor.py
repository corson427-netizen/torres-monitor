import os
import json
import urllib.request
import urllib.parse
from playwright.sync_api import sync_playwright

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

# --- MARCH 18-19 TARGETS ---
TARGETS = [
    {"label": "Serón (TEST March 18-19)", "date": "2026-03-18", "product_id": "camping_seron_individual"},
    {"label": "Cuernos (TEST March 18-19)", "date": "2026-03-18", "product_id": "camping_cuernos_individual"},
    {"label": "Chileno (TEST March 18-19)", "date": "2026-03-18", "product_id": "camping_chileno_individual"}
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
    print("🤖 Initializing Chromium Security Bypass Watchtower...")
    
    with sync_playwright() as p:
        # Launch real browser to satisfy Cloudflare check
        browser = p.chromium.launch(headless=True, args=["--disable-web-security", "--no-sandbox"])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        captured_data = {}

        # Set up an active network sniffer to grab the database response
        def handle_response(response):
            if "api.migtra.com/api/v1/lastorres/availability" in response.url:
                try:
                    print("⚡ INTERCEPTED: Live backend database stream captured successfully!")
                    nonlocal captured_data
                    captured_data = response.json()
                except Exception as e:
                    print(f"⚠️ Error parsing intercepted database payload: {e}")

        page.on("response", handle_response)
        
        # Load a base search URL to wake up the system data calls
        test_url = "https://booking.lastorres.com/?checkIn=2026-03-18&checkOut=2026-03-19&adults=2&children=0"
        print(f"🔗 Establishing browser gateway connection via: {test_url}")
        
        try:
            page.goto(test_url, wait_until="load", timeout=60000)
            # Give the browser a clean window to finish streaming data blocks
            page.wait_for_timeout(15000)
            
            if not captured_data:
                print("⚠️ Deep scan fallback: Triggering extra calendar interaction to force background data update...")
                page.reload(wait_until="networkidle")
                page.wait_for_timeout(10000)

            if captured_data:
                print("✅ Processing authentic live inventory metrics...")
                
                for target in TARGETS:
                    label = target["label"]
                    date = target["date"]
                    prod_id = target["product_id"]
                    
                    day_data = captured_data.get(date, {})
                    product_status = day_data.get(prod_id, {})
                    
                    available_spots = product_status.get("available", 0)
                    is_closed = product_status.get("closed", False)
                    
                    print(f"\n📊 {label}:")
                    print(f"   -> System raw vacancies: {available_spots}")
                    print(f"   -> Hard block indicator: {is_closed}")
                    
                    if available_spots >= 2 and not is_closed:
                        print("🚨 MATCH FOUND IN DISPATCH DATABASE!")
                        send_discord_alert(f"🧪 SUCCESS! Found {available_spots} raw spaces open for **{label}**: {test_url}")
                    else:
                        print("🔒 Locked: Checked database numbers directly, no 2-person ground space unblocked.")
            else:
                print("❌ CRITICAL ERROR: Browser failed to capture any backend data payloads from the gateway stream.")
                
        except Exception as e:
            print(f"❌ Execution failure: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    check_las_torres()
