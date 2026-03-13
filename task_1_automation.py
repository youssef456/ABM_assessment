import asyncio
import os
import json
import time
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def run_trials(total_trials=10):
    async with async_playwright() as p:
        # Create a directory for videos if it doesn't exist
        os.makedirs("videos", exist_ok=True)
        
        # Run in headful mode to ensure a good recording of the interactions
        browser = await p.chromium.launch(headless=False)
        # Create a single context for all trials to generate one video
        context = await browser.new_context(
            record_video_dir="videos/temp_task_1/",
            record_video_size={"width": 1280, "height": 720}
        )
        
        page = await context.new_page()
        # Apply stealth to avoid detection
        await Stealth().apply_stealth_async(page)
        
        url = "https://cd.captchaaiplus.com/turnstile.html"
        results_data = []
        success_count = 0
        
        # Function to simulate cursor movement
        async def move_cursor_to(x, y):
            await page.mouse.move(x, y, steps=20)
            await asyncio.sleep(0.5)

        for i in range(1, total_trials + 1):
            print(f"--- Starting Trial {i} ---")
            success = False
            token = None
            
            try:
                # Set a shorter navigation timeout and wait_until
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                
                # Reduced delay
                await asyncio.sleep(2)
                
                # Move cursor around to show it's "active"
                await move_cursor_to(400, 300)
                
                # Interact with the Turnstile widget
                print(f"Trial {i}: Locating Turnstile widget...")
                iframe_selector = "iframe[src*='turnstile']"
                try:
                    iframe = await page.wait_for_selector(iframe_selector, timeout=10000)
                    box = await iframe.bounding_box()
                    if box:
                        # Move cursor to the box
                        await move_cursor_to(box['x'] + 30, box['y'] + 30)
                        await page.mouse.click(box['x'] + 30, box['y'] + 30)
                        print(f"Trial {i}: Clicked Turnstile widget.")
                    else:
                        print(f"Trial {i}: Could not get bounding box.")
                        await move_cursor_to(100, 450)
                        await page.mouse.click(100, 450)
                except Exception as e:
                    print(f"Trial {i}: Widget error: {e}")
                    await move_cursor_to(100, 450)
                    await page.mouse.click(100, 450)
                
                # Wait for the response token
                print(f"Trial {i}: Waiting for token...")
                for sec in range(60): # Reduced wait
                    token = await page.eval_on_selector("[name='cf-turnstile-response']", "el => el.value")
                    if token and len(token) > 20:
                        print(f"Trial {i}: Token found!")
                        break
                    await asyncio.sleep(0.5)
                
                if token and len(token) > 20:
                    # Move cursor to submit
                    submit_selector = "#submit-btn"
                    submit_btn = await page.wait_for_selector(submit_selector)
                    s_box = await submit_btn.bounding_box()
                    if s_box:
                        await move_cursor_to(s_box['x'] + s_box['width']/2, s_box['y'] + s_box['height']/2)
                    
                    # Click the submit button
                    await page.click(submit_selector)
                    
                    # Verify success
                    try:
                        await page.wait_for_selector("text='Success! Verified'", timeout=5000)
                        print(f"Trial {i}: SUCCESS! Verified.")
                        success = True
                        success_count += 1
                    except:
                        content = await page.content()
                        if "Success! Verified" in content:
                            print(f"Trial {i}: SUCCESS (found in content).")
                            success = True
                            success_count += 1
                        else:
                            print(f"Trial {i}: FAILED - Success message not found.")
                else:
                    print(f"Trial {i}: FAILED - Token timeout.")
                    
            except Exception as e:
                print(f"Trial {i}: Error: {e}")
            
            results_data.append({
                "trial": i,
                "success": success,
                "token": token
            })
            
            # Short pause between trials
            await asyncio.sleep(1)
            
        # Close everything to finalize the video
        video_path = await page.video.path()
        await context.close()
        await browser.close()
        
        # Move the video to the final location
        dest_video = "videos/Task_1_Consolidated.webm"
        if os.path.exists(video_path):
            if os.path.exists(dest_video): os.remove(dest_video)
            os.rename(video_path, dest_video)
            print(f"Consolidated video saved to: {dest_video}")
            
        success_rate = (success_count / total_trials) * 100
        print(f"\nFinal Success Rate: {success_rate}%")
        
        with open("task_1_results.json", "w") as f:
            json.dump({"success_rate": success_rate, "trials": results_data}, f, indent=4)
        
        return success_rate

if __name__ == "__main__":
    asyncio.run(run_trials())
