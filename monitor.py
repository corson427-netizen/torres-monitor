import os
from playwright.sync_api import sync_playwright

def check_las_torres():
    print("📡 Launching Cloud Network Sniffer...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_page()

        # This listener intercepts every background data request the site makes
        def log_request(request):
            if request.resource_type in ["fetch", "xhr", "document"]:
                print(f"🔗 [FOUND LINK]: {request.url}")

        page.on("request", log_request)

        print("🔗 Loading base booking portal on cloud runner...")
        page.goto("https://booking.lastorres.com/", wait_until="load")
        page.wait_for_timeout(15000)  # Let it stream background traffic for 15 seconds
        
        print("\n✅ Sniff complete! Check the lines above for the [FOUND LINK] outputs.")
        browser.close()

if __name__ == "__main__":
    check_las_torres()
