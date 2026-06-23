import os
import json
import urllib.request
import urllib.parse
import http.cookiejar

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

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
    print("🚀 Initializing deep browser simulation handshake...")
    
    # Set up an automatic cookie jar to store and pass back session tracking
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    
    # Realistic high-fidelity desktop headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'Origin': 'https://booking.lastorres.com',
        'Referer': 'https://booking.lastorres.com/',
        'Connection': 'keep-alive'
    }
    
    api_url = "https://api.migtra.com/api/v1/lastorres/availability"
    
    try:
        # Step 1: Hit the front page first to establish regular cookies
        print("🎫 Registering initial user session cookies...")
        init_req = urllib.request.Request("https://booking.lastorres.com/", headers={'User-Agent': headers['User-Agent']})
        with opener.open(init_req, timeout=15) as _:
            pass
            
        # Step 2: Query the real backend with the newly gained cookies
        print("🔑 Pushing data payload via secure pipeline channel...")
        req = urllib.request.Request(api_url, headers=headers)
        
        with opener.open(req, timeout=15) as response:
            raw_data = response.read().decode('utf-8')
            inventory = json.loads(raw_data)
            
            print("✅ Handshake clean! Direct connection established.")
            
            for target in TARGETS:
                label = target["label"]
                date = target["date"]
                prod_id = target["product_id"]
                
                print(f"\n🧐 Analyzing inventory for: {label}")
                
                day_data = inventory.get(date, {})
                product_status = day_data.get(prod_id, {})
                
                available_spots = product_status.get("available", 0)
                is_closed = product_status.get("closed", False)
                
                print(f"   -> Spaces found: {available_spots}")
                print(f"   -> System lockout: {is_closed}")
                
                if available_spots >= 2 and not is_closed:
                    print("🚨 ALERT TRIGGERED!")
                    send_discord_alert(f"🧪 Restock detected! {available_spots} slots open for **{label}**: https://booking.lastorres.com/?checkIn={date}&adults=2")
                else:
                    print(f"🔒 Locked: 0 or insufficient slots available.")
                    
    except urllib.error.HTTPError as e:
        print(f"❌ Security gateway block status ({e.code}): {e.reason}")
        if e.code == 403:
            print("💡 Cloudflare is strictly parsing the Python TLS handshake fingerprint. Let's try running again.")
    except Exception as e:
        print(f"❌ Interrupted: {e}")

if __name__ == "__main__":
    check_las_torres()
