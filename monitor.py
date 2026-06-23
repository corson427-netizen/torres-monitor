import os
import json
import urllib.request
import urllib.parse

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

# --- MARCH 18-19 DIRECT API INVENTORY TARGETS ---
# We use their real internal system product codes for individual camping (bare ground)
TARGETS = [
    {"label": "Serón (TEST March 18-19)", "date": "2026-03-18", "product_id": "camping_seron_individual", "hotel_id": "seron"},
    {"label": "Cuernos (TEST March 18-19)", "date": "2026-03-18", "product_id": "camping_cuernos_individual", "hotel_id": "cuernos"},
    {"label": "Chileno (TEST March 18-19)", "date": "2026-03-18", "product_id": "camping_chileno_individual", "hotel_id": "chileno"}
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
    print("🚀 Querying Las Torres Live Database Stream Directly...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Origin': 'https://booking.lastorres.com',
        'Referer': 'https://booking.lastorres.com/'
    }
    
    # We poll their central reservation pipeline directly
    api_url = "https://api.migtra.com/api/v1/lastorres/availability"
    
    try:
        req = urllib.request.Request(api_url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            raw_data = response.read().decode('utf-8')
            inventory = json.loads(raw_data)
            
            print("✅ Successfully established data connection to backend database stream.")
            
            # The API returns a direct map of dates and product codes
            for target in TARGETS:
                label = target["label"]
                date = target["date"]
                prod_id = target["product_id"]
                
                print(f"\n🧐 Analyzing inventory array for: {label}")
                
                # Dig into the data layer to find the matching entry
                day_data = inventory.get(date, {})
                product_status = day_data.get(prod_id, {})
                
                # Find the actual number of free spots left
                available_spots = product_status.get("available", 0)
                is_closed = product_status.get("closed", False)
                
                print(f"   -> Raw spaces found in system: {available_spots}")
                print(f"   -> Hard system lock out active: {is_closed}")
                
                if available_spots >= 2 and not is_closed:
                    print("🚨 TRUE ALERT CONDITION MET!")
                    send_discord_alert(f"🧪 DIAGNOSTIC HIT: Found {available_spots} ground spots open for **{label}**! Book right now: https://booking.lastorres.com/?checkIn={date}&adults=2")
                else:
                    print(f"🔒 Locked: Database returns 0 or insufficient slots ({available_spots} available).")
                    
    except Exception as e:
        print(f"❌ Database pipeline connection dropped: {e}")

if __name__ == "__main__":
    check_las_torres()
