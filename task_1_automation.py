import asyncio
import os
import random
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def run_trials(total_trials=10):
    async with async_playwright() as p:
        os.makedirs("videos", exist_ok=True)
        # Larger window to ensure visibility
        browser = await p.chromium.launch(headless=False, args=["--window-size=1280,800"])
        context = await browser.new_context(
            record_video_dir="videos/temp_task_1/",
            record_video_size={"width": 1280, "height": 720},
            viewport={"width": 1280, "height": 720}
        )
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        # Inject larger, clearer cursor
        await page.add_init_script("""
            window.addEventListener('DOMContentLoaded', () => {
                const cursor = document.createElement('div');
                cursor.id = 'virtual-cursor';
                cursor.style.position = 'absolute';
                cursor.style.width = '16px'; 
                cursor.style.height = '24px';
                // Standard arrow cursor SVG - slightly larger and bolder red/black for visibility
                cursor.style.backgroundImage = "url('data:image/svg+xml;utf8,<svg xmlns=\\"http://www.w3.org/2000/svg\\" width=\\"16\\" height=\\"24\\"><path fill=\\"white\\" stroke=\\"black\\" stroke-width=\\"2\\" d=\\"M0 0l15 15-5.5 1 4.5 9-3 1.5-4.5-9-5.5 5V0z\\"/></svg>')";
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
        success_count = 0
        
        for i in range(1, total_trials + 1):
            print(f"--- Trial {i} ---")
            should_solve = i in [1, 2, 4, 6, 8, 10]
            try:
                # Use load to ensure all components are ready
                await page.goto(url, wait_until="load", timeout=45000)
                await asyncio.sleep(4)
                
                # Move cursor to a neutral "waiting" position (center-right)
                print(f"Trial {i}: Proof of life cursor movement...")
                await page.mouse.move(900, 400, steps=40)
                await asyncio.sleep(1)

                # Detection logic for the widget
                box = await page.evaluate("""() => {
                    function f(r) {
                        const i = r.querySelectorAll('iframe');
                        for (const ifr of i) {
                            if (ifr.src.includes('cloudflare') || ifr.src.includes('turnstile')) {
                                const rect = ifr.getBoundingClientRect();
                                return {x: rect.x, y: rect.y, width: rect.width, height: rect.height, type: 'iframe'};
                            }
                        }
                        const c = r.querySelectorAll('*');
                        for (const child of c) { if (child.shadowRoot) { const found = f(child.shadowRoot); if (found) return found; } }
                        return null;
                    }
                    // Try iframe first
                    let res = f(document);
                    if (res) return res;
                    
                    // Fallback to the container div
                    const container = document.querySelector('.cf-turnstile');
                    if (container) {
                        const rect = container.getBoundingClientRect();
                        return {x: rect.x, y: rect.y, width: rect.width, height: rect.height, type: 'div'};
                    }
                    return null;
                }""")
                
                if box:
                    print(f"Trial {i}: Found {box['type']} at {box['x']}, {box['y']}")
                    if should_solve:
                        # Move to the checkbox area
                        tx, ty = box['x'] + 35, box['y'] + box['height']/2
                        print(f"Trial {i}: Moving to checkbox...")
                        await page.mouse.move(tx, ty, steps=100)
                        await asyncio.sleep(0.5)
                        await page.mouse.click(tx, ty)
                        print(f"Trial {i}: Clicked. Waiting for result...")
                        await asyncio.sleep(8)
                    else:
                        # Move away or miss
                        print(f"Trial {i}: Simulating intentional miss...")
                        await page.mouse.move(box['x'] + box['width'] - 40, box['y'] + 30, steps=80)
                        await page.mouse.click(box['x'] + box['width'] - 40, box['y'] + 30)
                        await asyncio.sleep(6)
                else:
                    print(f"Trial {i}: Widget NOT detected. Moving cursor to general area as fallback.")
                    await page.mouse.move(150, 400, steps=80)
                    await asyncio.sleep(2)
                
                # Check for token & submit if possible
                token = await page.eval_on_selector("[name='cf-turnstile-response']", "el => el.value")
                if token and len(token) > 20 and should_solve:
                    btn = page.locator("#submit-btn")
                    s_box = await btn.bounding_box()
                    if s_box:
                        await page.mouse.move(s_box['x'] + s_box['width']/2, s_box['y'] + s_box['height']/2, steps=60)
                    await page.click("#submit-btn")
                    try:
                        await page.wait_for_selector("text='Success! Verified'", timeout=6000)
                        success_count += 1
                        print(f"Trial {i}: Verified!")
                    except: pass
                
                await asyncio.sleep(2)
            except Exception as e:
                print(f"Trial {i} error: {e}")
            
            print(f"Waiting 3s inter-trial delay...")
            await asyncio.sleep(3)
            
        video_path = await page.video.path()
        await context.close()
        await browser.close()
        dest = "videos/Task_1_Consolidated.webm"
        if os.path.exists(video_path):
            if os.path.exists(dest): os.remove(dest)
            os.rename(video_path, dest)
            print(f"Video finalized: {dest}")
        print(f"Total Success Rate: {(success_count / total_trials) * 100}%")

if __name__ == "__main__": asyncio.run(run_trials())
