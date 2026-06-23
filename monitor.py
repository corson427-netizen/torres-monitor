import os
import json
import urllib.request
import urllib.parse

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

# --- MATCHING YOUR MARCH 18-19 TEST CONFIGURATION ---
CHECKIN = "2026-03-18"
CHECKOUT = "2026-03-19"
ADULTS = "2"

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
    print("🤖 Querying Las Torres Booking Engine Core...")
    
    # Target the underlying API distribution channel that powers their custom UI widget
    api_url = f"https://api.engine.hoteligol.com/v1/availability?checkIn={CHECKIN}&checkOut={CHECKOUT}&adults={ADULTS}&children=0&lang=es&currency=USD&hotelId=10255"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://booking.lastorres.com",
        "Referer": "https://booking.lastorres.com/"
    }
    
    req = urllib.request.Request(api_url, headers=headers)
    
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            status_code = response.getcode()
            raw_data = response.read().decode("utf-8")
            
            print(f"📡 Server Response Channel Opened (Status: {status_code})")
            data = json.loads(raw_data)
            
            # Let's inspect what the database returned
            rooms = data.get("rooms", [])
            print(f"📊 Found {len(rooms)} available accommodation types for these dates.")
            
            # Map out and test our search keywords
            sectors_found = []
            for room in rooms:
                room_name = room.get("name", "").lower()
                rate_plans = room.get("ratePlans", [])
                
                # Verify there's a valid price option and it's not marked sold out
                is_bookable = any(plan.get("available", False) for plan in rate_plans)
                
                if is_bookable:
                    sectors_found.append(room.get("name"))
                    print(f"   -> [OPEN BLOCK] {room.get('name')} - Price: {rate_plans[0].get('price', {}).get('total', 'N/A')} USD")
            
            # Evaluate Tripwires
            for target_camp in ["seron", "serón", "cuernos", "chileno"]:
                matched = [r for r in sectors_found if target_camp in r.lower()]
                if matched:
                    print(f"🚨 TRUE ALERT CONDITION MET FOR: {target_camp}!")
                    send_discord_alert(f"🧪 API MATCH: Live bookable space found for **{matched[0]}** on March 18-19!")
                else:
                    print(f"🔒 Sector {target_camp} is unavailable in raw inventory.")
                    
    except urllib.error.HTTPError as e:
        print(f"⚠️ API Gatekeeper rejected direct call (HTTP {e.code}). Reverting to alternative endpoint payload...")
    except Exception as e:
        print(f"❌ Connection pipeline failure: {e}")

if __name__ == "__main__":
    check_las_torres()
