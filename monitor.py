import os
import urllib.request
import urllib.parse
from playwright.sync_api import sync_playwright

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

TARGETS = [
    {"label": "Serón (TEST March 18-19)", "keywords": ["seron", "serón"]},
    {"label": "Cuernos (TEST March 18-19)", "keywords": ["cuernos"]},
    {"label": "Chileno (TEST March 18-19)", "keywords": ["chileno"]}
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
    print("🤖 Launching True-Path Step Monitor...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = browser.new_context(viewport={"width": 1440, "height": 900}, locale="en-US")
        page = context.new_page()
        
        try:
            print("🔗 Step 1: Loading homepage...")
            page.goto("https://lastorres.com/", wait_until="networkidle", timeout=60000)
            page.wait_for_timeout(5000)
            
            # Step 2: Handle popup exit
            print("💥 Step 2: Dismissing promotional popup box...")
            popup_close = page.locator(".modal-close, [class*='close'], button:has-text('X'), a:has-text('X')").first
            if popup_close.count() > 0 and popup_close.is_visible():
                popup_close.click()
                page.wait_for_timeout(1000)
            
            # Step 3: Click "Per Night" button
            print("👆 Step 3: Selecting 'Per Night' booking mode...")
            page.locator("text=Per Night, text=Por Noche").first.click()
            page.wait_for_timeout(1000)
            
            # Step 4: Click Type of Experience -> Camp
            print("🏕️ Step 4: Filtering experience category by 'Camp'...")
            page.locator("text=Type of Experience, text=Tipo de Experiencia").first.click()
            page.wait_for_timeout(500)
            page.locator("text=Camp, text=Camping").first.click()
            page.wait_for_timeout(1000)
            
            # Step 5: Click Book Now
            print("🚀 Step 5: Initializing reservation workflow container...")
            page.locator("text=Book Now, text=Reservar Ahora").first.click()
            page.wait_for_timeout(4000)
            
            # Step 6: Step through the calendar to March 2026
            print("📅 Step 6: Advancing calendar arrays forward to March 2026...")
            next_month = page.locator("[class*='next'], .arrow-right, text=>").first
            for _ in range(12):
                cal_text = page.locator("body").inner_text().upper()
                if "MARCH 2026" in cal_text or "MARZO 2026" in cal_text:
                    print("🎯 Anchored on March 2026 grid.")
                    break
                if next_month.count() > 0 and next_month.is_visible():
                    next_month.click()
                    page.wait_for_timeout(600)
            
            # Select March 18 and March 19 cells
            print("📍 Registering targeted cell matrix values...")
            page.locator(".day:has-text('18'), button:has-text('18'), [class*='cell']:has-text('18')").first.click()
            page.wait_for_timeout(500)
            page.locator(".day:has-text('19'), button:has-text('19'), [class*='cell']:has-text('19')").first.click()
            page.wait_for_timeout(1000)
            
            # Step 7: Click people selector and change to 2 Adults
            print("👥 Step 7: Modifying passenger matrix to 2 adults...")
            guests_menu = page.locator("[class*='guest'], [class*='passenger'], text=People, text=Pasajeros").first
            if guests_menu.count() > 0:
                guests_menu.click()
                page.wait_for_timeout(500)
                # Find the plus button for adults
                plus_btn = page.locator(".plus, [class*='increase'], button:has-text('+')").first
                if plus_btn.count() > 0:
                    plus_btn.click() # Default is usually 1, click once to make it 2
                    page.wait_for_timeout(500)
            
            # Step 8: Hit primary Book button
            print("💥 Step 8: Submitting baseline parameters to core search engine...")
            page.locator("button:has-text('Book'), button:has-text('Buscar'), .btn-search").first.click()
            page.wait_for_timeout(8000)
            
            # Step 9: Handle the country selection drop down ("United States")
            print("🌎 Step 9: Overriding country routing checkpoint...")
            dropdown = page.locator("select, [class*='country'], [id*='country']").first
            if dropdown.count() > 0:
                dropdown.select_option(label="United States")
                page.wait_for_timeout(1000)
                # Click next/continue
                page.locator("button:has-text('Next'), button:has-text('Siguiente'), .btn-next").first.click()
                page.wait_for_timeout(6000)
            
            # Step 10: Deep inventory evaluation of specific campsites
            print("🔍 Step 10: Expanding detailed inventory panels for campsites...")
            search_bars = page.locator("button:has-text('Search'), .search-bar, [class*='expand']").all()
            for bar in search_bars:
                try:
                    if bar.is_visible():
                        bar.click()
                        page.wait_for_timeout(500)
                except:
                    continue
            
            # Final assessment: Extract the text layers
            page.wait_for_timeout(4000)
            visible_text = page.locator("body").inner_text()
            visible_text_lower = visible_text.lower()
            
            lines = [line.strip() for line in visible_text.split("\n") if line.strip()]
            print(f"\n📊 ACTIVE FRAME RENDER SNIPPET:\n{lines[:15]}")
            
            for target in TARGETS:
                label = target["label"]
                
                # Check if the specific camp name exists on the screen
                has_camp = any(kw in visible_text_lower for kw in target["keywords"])
                has_pricing = any(symbol in visible_text_lower for symbol in ["$", "usd", "clp", "total"])
                is_sold_out = any(flag in visible_text_lower for flag in ["sold out", "agotado", "no rooms", "no slots"])
                
                print(f"\n🧐 Evaluating {label}:")
                print(f"   -> Site Node Present: {has_camp} | Active Price Tracked: {has_pricing} | Sold Out Marker: {is_sold_out}")
                
                if has_camp and has_pricing and not is_sold_out:
                    print("🚨 TARGET MATCH CRITERIA ACHIEVED!")
                    send_discord_alert(f"🧪 LIVE PATH MATCH: Active available space located for **{label}** on March 18-19!")
                else:
                    print("🔒 Locked / Unavailable.")
                    
        except Exception as e:
            print(f"❌ Automation funnel break: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    check_las_torres()
