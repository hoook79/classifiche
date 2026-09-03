import asyncio
from playwright.async_api import async_playwright

async def main():
    print("Starting Playwright script...", flush=True)
    async with async_playwright() as p:
        # Launch browser headless
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Capture console logs
        page.on("console", lambda msg: print(f"[CONSOLE {msg.type.upper()}] {msg.text}", flush=True))
        
        # Capture page errors
        page.on("pageerror", lambda err: print(f"[PAGE ERROR] {err.message}", flush=True))
        
        # Capture alerts
        async def handle_dialog(dialog):
            print(f"[ALERT] {dialog.message}", flush=True)
            await dialog.accept()
        page.on("dialog", handle_dialog)
        
        # Capture network requests
        page.on("request", lambda req: print(f"[REQ] {req.method} {req.url}", flush=True))
        page.on("response", lambda res: print(f"[RES] {res.status} {res.url}", flush=True))
        page.on("requestfailed", lambda req: print(f"[REQ FAILED] {req.url}: {req.failure}", flush=True))
        
        # Load the page first so we are on the correct origin
        print("Navigating to http://localhost:8000/index.html to establish origin...", flush=True)
        try:
            await page.goto("http://localhost:8000/index.html", timeout=10000)
        except Exception as e:
            print(f"Navigation failed (is the server running?): {e}", flush=True)
            await browser.close()
            return
            
        # Set localStorage credentials
        print("Injecting credentials into localStorage...", flush=True)
        await page.evaluate("""() => {
            localStorage.setItem('radio_charts_user', 'admin');
            localStorage.setItem('radio_charts_pass', 'Stationm1');
        }""")
        
        # Reload the page to trigger data loading
        print("Reloading page with credentials...", flush=True)
        await page.reload(timeout=10000)
        
        # Wait for network requests or rendering (15 seconds)
        print("Waiting 15 seconds for data loading...", flush=True)
        await asyncio.sleep(15)
        
        # Check the DOM
        try:
            overlay_display = await page.eval_on_selector("#login-overlay", "el => window.getComputedStyle(el).display")
            error_text = await page.eval_on_selector("#login-error", "el => el.textContent")
            results_count = await page.eval_on_selector("#results-count", "el => el.textContent")
            raw_keys = await page.evaluate("() => Object.keys(RAW).map(k => `${k}: ${RAW[k].songs ? RAW[k].songs.length : 'no songs'}`)")
            local_user = await page.evaluate("() => localStorage.getItem('radio_charts_user')")
            local_pass = await page.evaluate("() => localStorage.getItem('radio_charts_pass')")
            
            print(f"Login Overlay Display: {overlay_display}", flush=True)
            print(f"Login Error Text: {error_text}", flush=True)
            print(f"LocalStorage user: {local_user}", flush=True)
            print(f"LocalStorage pass: {local_pass}", flush=True)
            print(f"RAW Keys and song lengths: {raw_keys}", flush=True)
            print(f"Results Count Element Text: '{results_count}'", flush=True)
            
            # Print state variables
            logged_in_user = await page.evaluate("() => loggedInUser")
            user_role = await page.evaluate("() => userRole")
            print(f"JavaScript loggedInUser: {logged_in_user}", flush=True)
            print(f"JavaScript userRole: {user_role}", flush=True)
            
            # Print tbody text safely
            tbody_text = await page.eval_on_selector("#chart-body", "el => el.innerText")
            print(f"Tbody text (safe): {tbody_text.encode('ascii', 'ignore').decode('ascii')[:300]}", flush=True)
        except Exception as e:
            print(f"Could not read diagnostic state: {e}", flush=True)
            
        # Close browser
        await browser.close()
        print("Playwright script finished.", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
