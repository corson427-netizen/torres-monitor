from playwright.sync_api import sync_playwright

def run():
    print("📡 Launching automated network sniffer... Please wait.")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Listen and log every single background network request
        def log_request(request):
            # Ignore basic images, fonts, and stylesheets to keep the logs clean
            if request.resource_type in ["fetch", "xhr", "document"]:
                print(f"🔗 [FOUND]: {request.url}")

        page.on("request", log_request)

        # Load the portal and let it stream background assets
        page.goto("https://booking.lastorres.com/", wait_until="load")
        page.wait_for_timeout(15000)
        
        browser.close()
        print("\n✅ Sniff complete. Copy and paste the links above here!")

if __name__ == "__main__":
    run()
