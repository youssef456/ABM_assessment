import asyncio
import os
import json
import time
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def run_trials(total_trials=10):
    async with async_playwright() as p:
        os.makedirs("videos", exist_ok=True)
        
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            record_video_dir="videos/temp_task_1/",
            record_video_size={"width": 1280, "height": 720}
        )
        
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        # Inject virtual cursor and status overlay
        await page.add_init_script("""
            window.addEventListener('DOMContentLoaded', () => {
                const cursor = document.createElement('div');
                cursor.id = 'virtual-cursor';
                cursor.style.position = 'absolute';
                cursor.style.width = '20px';
                cursor.style.height = '20px';
                cursor.style.backgroundColor = 'rgba(255, 0, 0, 0.6)';
                cursor.style.borderRadius = '50%';
                cursor.style.border = '2px solid white';
                cursor.style.pointerEvents = 'none';
                cursor.style.zIndex = '999999';
                cursor.style.transition = 'transform 0.1s linear';
                document.body.appendChild(cursor);

                const status = document.createElement('div');
                status.id = 'status-overlay';
                status.style.position = 'fixed';
                status.style.top = '10px';
                status.style.right = '10px';
                status.style.padding = '10px';
                status.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
                status.style.color = 'white';
                status.style.fontFamily = 'monospace';
                status.style.zIndex = '999999';
                status.style.borderRadius = '5px';
                status.innerText = 'Initializing...';
                document.body.appendChild(status);

                document.addEventListener('mousemove', (e) => {
                    cursor.style.transform = `translate(${e.pageX}px, ${e.pageY}px)`;
                });
            });
        """)

        url = "https://cd.captchaaiplus.com/turnstile.html"
        results_data = []
        success_count = 0
        
        async def update_status(msg, color='white'):
            await page.evaluate("([msg, color]) => { const el = document.getElementById('status-overlay'); if(el) { el.innerText = msg; el.style.color = color; } }", [msg, color])

        async def move_cursor_to(x, y):
            await page.mouse.move(x, y, steps=20)
            await asyncio.sleep(0.3)

        for i in range(1, total_trials + 1):
            print(f"--- Starting Trial {i} ---")
            success = False
            token = None
            
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                await update_status(f"Trial {i}: Page Ready (Wait...)")
                await asyncio.sleep(2)
                
                await update_status(f"Trial {i}: Locating Turnstile Widget")
                iframe_selector = "iframe[src*='turnstile']"
                try:
                    iframe = await page.wait_for_selector(iframe_selector, timeout=10000)
                    box = await iframe.bounding_box()
                    if box:
                        # Move to widget
                        await move_cursor_to(box['x'] + 30, box['y'] + 30)
                        await page.mouse.click(box['x'] + 30, box['y'] + 30)
                        await update_status(f"Trial {i}: Widget Clicked", "yellow")
                except:
                    await update_status(f"Trial {i}: Widget Timeout", "red")
                    await move_cursor_to(100, 450)
                    await page.mouse.click(100, 450)
                
                await update_status(f"Trial {i}: Waiting for Response Token")
                for sec in range(40):
                    token = await page.eval_on_selector("[name='cf-turnstile-response']", "el => el.value")
                    if token and len(token) > 20:
                        await update_status(f"Trial {i}: Token Captured!", "cyan")
                        break
                    await asyncio.sleep(0.5)
                
                if token and len(token) > 20:
                    submit_selector = "#submit-btn"
                    try:
                        submit_btn = await page.wait_for_selector(submit_selector, timeout=5000)
                        s_box = await submit_btn.bounding_box()
                        if s_box:
                            await move_cursor_to(s_box['x'] + s_box['width']/2, s_box['y'] + s_box['height']/2)
                        
                        await update_status(f"Trial {i}: Submitting Token", "orange")
                        await page.click(submit_selector)
                        
                        # Verify Success
                        try:
                            await page.wait_for_selector("text='Success! Verified'", timeout=5000)
                            await update_status(f"Trial {i}: Success! Verified", "#00FF00")
                            success = True
                            success_count += 1
                        except:
                            # If the real message is hidden, we explicitly show result in status
                            await update_status(f"Trial {i}: Submission Finished", "white")
                    except:
                        await update_status(f"Trial {i}: Submit Button Error", "red")
                else:
                    await update_status(f"Trial {i}: FAILED - Token Timeout", "red")
                    
            except Exception as e:
                print(f"Error: {e}")
                await update_status(f"Trial {i}: Error Occurred", "red")
            
            await asyncio.sleep(2) # Visible result time
            
        await update_status(f"Final Success Rate: {success_count}/{total_trials}", "white")
        await asyncio.sleep(3)
        
        video_path = await page.video.path()
        await context.close()
        await browser.close()
        
        dest_video = "videos/Task_1_Consolidated.webm"
        if os.path.exists(video_path):
            if os.path.exists(dest_video): os.remove(dest_video)
            os.rename(video_path, dest_video)
            print(f"Consolidated video saved to: {dest_video}")
            
        success_rate = (success_count / total_trials) * 100
        return success_rate

if __name__ == "__main__":
    asyncio.run(run_trials())
