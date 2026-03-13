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
        
        # Inject realistic arrow cursor
        await page.add_init_script("""
            window.addEventListener('DOMContentLoaded', () => {
                const cursor = document.createElement('div');
                cursor.id = 'virtual-cursor';
                cursor.style.position = 'absolute';
                cursor.style.width = '12px';
                cursor.style.height = '19px';
                // Standard arrow cursor SVG
                cursor.style.backgroundImage = "url('data:image/svg+xml;utf8,<svg xmlns=\\"http://www.w3.org/2000/svg\\" width=\\"12\\" height=\\"19\\"><path fill=\\"white\\" stroke=\\"black\\" d=\\"M0 0l11.4 11.4-4.2.8 3.5 6.8-2 1-3.5-6.8-4 3.8V0z\\"/></svg>')";
                cursor.style.backgroundRepeat = 'no-repeat';
                cursor.style.pointerEvents = 'none';
                cursor.style.zIndex = '999999';
                cursor.style.left = '0px';
                cursor.style.top = '0px';
                document.body.appendChild(cursor);

                window.addEventListener('mousemove', (e) => {
                    cursor.style.left = e.pageX + 'px';
                    cursor.style.top = e.pageY + 'px';
                });
            });
        """)

        url = "https://cd.captchaaiplus.com/turnstile.html"
        results_data = []
        success_count = 0
        
        async def move_cursor_to(x, y):
            await page.mouse.move(x, y, steps=25)
            await asyncio.sleep(0.2)

        for i in range(1, total_trials + 1):
            print(f"--- Starting Trial {i} ---")
            success = False
            token = None
            
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(2)
                
                iframe_selector = "iframe[src*='turnstile']"
                try:
                    iframe = await page.wait_for_selector(iframe_selector, timeout=10000)
                    box = await iframe.bounding_box()
                    if box:
                        await move_cursor_to(box['x'] + 30, box['y'] + 30)
                        await page.mouse.click(box['x'] + 30, box['y'] + 30)
                except:
                    await move_cursor_to(100, 450)
                    await page.mouse.click(100, 450)
                
                for sec in range(40):
                    token = await page.eval_on_selector("[name='cf-turnstile-response']", "el => el.value")
                    if token and len(token) > 20:
                        break
                    await asyncio.sleep(0.5)
                
                if token and len(token) > 20:
                    submit_selector = "#submit-btn"
                    try:
                        submit_btn = await page.wait_for_selector(submit_selector, timeout=5000)
                        s_box = await submit_btn.bounding_box()
                        if s_box:
                            await move_cursor_to(s_box['x'] + s_box['width']/2, s_box['y'] + s_box['height']/2)
                        
                        await page.click(submit_selector)
                        
                        try:
                            await page.wait_for_selector("text='Success! Verified'", timeout=5000)
                            success = True
                            success_count += 1
                            await asyncio.sleep(2) # Show verification result in video
                        except:
                            pass
                    except:
                        pass
                else:
                    await asyncio.sleep(1)
                    
            except Exception as e:
                print(f"Error: {e}")
            
            await asyncio.sleep(1)
            
        await asyncio.sleep(2)
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
