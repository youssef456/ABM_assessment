import asyncio
import os
import json
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def task_2_interception():
    async with async_playwright() as p:
        os.makedirs("videos", exist_ok=True)
        
        # Launch headful to show the injection and success message
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            record_video_dir="videos/",
            record_video_size={"width": 1280, "height": 720}
        )
        
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        # Data to capture
        captured_data = {
            "sitekey": None,
            "pageaction": None,
            "cdata": None,
            "pagedata": None
        }
        
        # Intercept network requests to block turnstile loading and capture details
        # Turnstile usually loads from challenges.cloudflare.com
        async def handle_request(route):
            url = route.request.url
            if "challenges.cloudflare.com" in url:
                # Capture details from URL parameters if present
                # Pageaction, cdata, etc are often in the request to cloudflare
                if "sitekey" in url:
                    # Parse URL for parameters
                    from urllib.parse import urlparse, parse_qs
                    parsed = urlparse(url)
                    params = parse_qs(parsed.query)
                    if not captured_data["sitekey"]: captured_data["sitekey"] = params.get("sitekey", [None])[0]
                    if not captured_data["pageaction"]: captured_data["pageaction"] = params.get("action", [None])[0]
                    if not captured_data["cdata"]: captured_data["cdata"] = params.get("cdata", [None])[0]
                
                print(f"Blocking Turnstile request: {url[:100]}...")
                await route.abort()
            else:
                await route.continue_()

        await page.route("**/*", handle_request)
        
        url = "https://cd.captchaaiplus.com/turnstile.html"
        print(f"Navigating to {url} with interception enabled...")
        await page.goto(url, wait_until="domcontentloaded")
        
        # Wait a bit to ensure all initial requests are intercepted
        await asyncio.sleep(5)
        
        # Extract metadata from DOM if not captured from network
        # Sometimes sitekey is in a div attribute
        if not captured_data["sitekey"]:
            captured_data["sitekey"] = await page.eval_on_selector(".cf-turnstile", "el => el.getAttribute('data-sitekey')")
        
        print(f"Captured Metadata: {json.dumps(captured_data, indent=2)}")
        
        # Inject valid token (In a real scenario, this would come from Task 1)
        # For demonstration, we'll try to find a token from task_1_results.json if it exists
        token_to_inject = "MOCK_TOKEN_VAL_FROM_TASK_1"
        if os.path.exists("task_1_results.json"):
            with open("task_1_results.json", "r") as f:
                task1_data = json.load(f)
                if task1_data.get("tokens"):
                    token_to_inject = task1_data["tokens"][0]
        
        print(f"Injecting token: {token_to_inject[:50]}...")
        
        # Inject the token into the hidden input
        # If the script is blocked, the element might not exist. Create it if missing.
        await page.evaluate("""(token) => {
            const form = document.querySelector('#turnstile-form') || document.querySelector('form');
            if (form && !document.querySelector('[name="cf-turnstile-response"]')) {
                const input = document.createElement('input');
                input.type = 'hidden';
                input.name = 'cf-turnstile-response';
                form.appendChild(input);
            }
            if (document.querySelector('[name="cf-turnstile-response"]')) {
                document.querySelector('[name="cf-turnstile-response"]').value = token;
            }
        }""", token_to_inject)
        
        # Take a screenshot before submit to show Turnstile didn't load (blocked)
        await page.screenshot(path="task_2_blocked.png")
        
        # Click submit
        print("Clicking submit with injected token...")
        try:
            # Try different possible selectors
            if await page.query_selector("#submit-btn"):
                await page.click("#submit-btn")
            elif await page.query_selector("button[type='submit']"):
                await page.click("button[type='submit']")
            elif await page.query_selector("input[type='submit']"):
                await page.click("input[type='submit']")
            else:
                print("Submit button not found with standard selectors. Checking all buttons...")
                buttons = await page.query_selector_all("button")
                for btn in buttons:
                    text = await btn.inner_text()
                    if "Submit" in text:
                        await btn.click()
                        break
        except Exception as e:
            print(f"Error clicking button: {e}")
            await page.screenshot(path="task_2_error.png")
            content = await page.content()
            with open("task_2_debug.html", "w", encoding="utf-8") as f:
                f.write(content)
        
        # Wait for success message
        try:
            success_selector = "text='Success! Verified'"
            await page.wait_for_selector(success_selector, timeout=15000)
            print("Successfully verified with injected token!")
        except Exception as e:
            print(f"Verification message not found: {e}")
            content = await page.content()
            if "Success! Verified" in content:
                print("Successfully verified (found in content)!")
            else:
                print("Verification failed.")
        
        await asyncio.sleep(5)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(task_2_interception())
