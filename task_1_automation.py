import asyncio
import os
import json
import time
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def run_trial(trial_number, headless):
    async with async_playwright() as p:
        # Create a directory for videos if it doesn't exist
        os.makedirs("videos", exist_ok=True)
        
        browser = await p.chromium.launch(headless=headless)
        # Create context with video recording
        context = await browser.new_context(
            record_video_dir="videos/",
            record_video_size={"width": 1280, "height": 720}
        )
        
        page = await context.new_page()
        # Apply stealth to avoid detection
        await Stealth().apply_stealth_async(page)
        
        url = "https://cd.captchaaiplus.com/turnstile.html"
        print(f"Trial {trial_number} ({'Headless' if headless else 'Headful'}): Navigating to {url}")
        
        try:
            # Set a longer navigation timeout
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            # Fields are read-only, skipping filling them.
            # Small delay to ensure widget is ready
            await asyncio.sleep(5)
            
            # Interact with the Turnstile widget
            print(f"Trial {trial_number}: Locating Turnstile widget...")
            iframe_selector = "iframe[src*='turnstile']"
            try:
                iframe = await page.wait_for_selector(iframe_selector, timeout=20000)
                box = await iframe.bounding_box()
                if box:
                    # Click slightly inside the left-top of the widget (where the box usually is)
                    await page.mouse.click(box['x'] + 30, box['y'] + 30)
                    print(f"Trial {trial_number}: Clicked Turnstile widget at {box['x']+30}, {box['y']+30}")
                else:
                    print(f"Trial {trial_number}: Could not get bounding box for Turnstile.")
                    await page.mouse.click(45, 445) # Fallback
            except Exception as e:
                print(f"Trial {trial_number}: Widget not found or error: {e}")
                await page.mouse.click(45, 445) # Fallback
            
            print(f"Trial {trial_number}: Waiting for Turnstile verification...")
            
            # Wait for the response token to appear in the hidden input
            token_element = await page.wait_for_selector("[name='cf-turnstile-response']", state="attached", timeout=90000)
            
            token = ""
            for i in range(120): # 120 seconds timeout
                token = await page.eval_on_selector("[name='cf-turnstile-response']", "el => el.value")
                if token and len(token) > 10: # Ensure it's a real token
                    print(f"Trial {trial_number}: Token found at second {i}!")
                    break
                if i % 10 == 0:
                    print(f"Trial {trial_number}: Waiting for token... (second {i})")
                await asyncio.sleep(1)
            
            if not token:
                print(f"Trial {trial_number}: Failed to get token.")
                await browser.close()
                return False, None

            print(f"Trial {trial_number}: Token obtained. Clicking submit...")
            
            # Click the submit button
            await page.click("button[type='submit']")
            
            # Wait for the verification success message on the next page/state
            # On this site, it might be "Success! Verified" or similar.
            try:
                success_selector = "text='Success! Verified'"
                await page.wait_for_selector(success_selector, timeout=20000)
                print(f"Trial {trial_number}: Success! Verified message found.")
                await browser.close()
                return True, token
            except:
                # Check if it just shows the text on the page
                content = await page.content()
                if "Success! Verified" in content:
                    print(f"Trial {trial_number}: Success! Verified (found via content).")
                    await browser.close()
                    return True, token
                else:
                    print(f"Trial {trial_number}: Success message not found after submission.")
                    await browser.close()
                    return False, None
            
        except Exception as e:
            print(f"Trial {trial_number}: Error occurred: {e}")
            await browser.close()
            return False, None

async def main():
    success_count = 0
    total_trials = 10
    results_data = []
    
    # Toggle headless mode as required
    for i in range(1, total_trials + 1):
        headless = (i % 2 == 0)
        success, token = await run_trial(i, headless)
        results_data.append({
            "trial": i,
            "headless": headless,
            "success": success,
            "token": token
        })
        if success:
            success_count += 1
            print(f"Trial {i} SUCCESS.")
        else:
            print(f"Trial {i} FAILED.")
    
    success_rate = (success_count / total_trials) * 100
    print(f"\nFinal Success Rate: {success_rate}%")
    
    with open("task_1_results.json", "w") as f:
        json.dump({"success_rate": success_rate, "trials": results_data}, f, indent=4)
    
    if success_rate >= 60:
        print("Assessment Criteria Met (>= 60%)")
    else:
        print("Assessment Criteria NOT Met (< 60%)")

if __name__ == "__main__":
    asyncio.run(main())
