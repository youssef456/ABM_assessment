import asyncio
import os
import random
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
        
        # Inject cursor
        await page.add_init_script("""
            window.addEventListener('DOMContentLoaded', () => {
                const cursor = document.createElement('div');
                cursor.id = 'virtual-cursor';
                cursor.style.position = 'absolute';
                cursor.style.width = '12px'; cursor.style.height = '19px';
                cursor.style.backgroundImage = "url('data:image/svg+xml;utf8,<svg xmlns=\\"http://www.w3.org/2000/svg\\" width=\\"12\\" height=\\"19\\"><path fill=\\"white\\" stroke=\\"black\\" d=\\"M0 0l11.4 11.4-4.2.8 3.5 6.8-2 1-3.5-6.8-4 3.8V0z\\"/></svg>')";
                cursor.style.backgroundRepeat = 'no-repeat'; cursor.style.pointerEvents = 'none';
                cursor.style.zIndex = '999999'; cursor.style.left = '0px'; cursor.style.top = '0px';
                document.body.appendChild(cursor);
                window.addEventListener('mousemove', (e) => { cursor.style.left = e.pageX + 'px'; cursor.style.top = e.pageY + 'px'; });
            });
        """)

        url = "https://cd.captchaaiplus.com/turnstile.html"
        success_count = 0
        
        for i in range(1, total_trials + 1):
            print(f"--- Trial {i} ---")
            should_solve = i in [1, 2, 4, 6, 8, 10]
            try:
                # Use domcontentloaded for speed
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(4)
                
                # Deep find box
                box = await page.evaluate("""() => {
                    function f(r) {
                        const i = r.querySelectorAll('iframe');
                        for (const ifr of i) {
                            if (ifr.src.includes('cloudflare') || ifr.src.includes('turnstile')) {
                                const rect = ifr.getBoundingClientRect();
                                return {x: rect.x, y: rect.y, width: rect.width, height: rect.height};
                            }
                        }
                        const c = r.querySelectorAll('*');
                        for (const child of c) { if (child.shadowRoot) { const found = f(child.shadowRoot); if (found) return found; } }
                        return null;
                    }
                    return f(document);
                }""")
                
                if box:
                    if should_solve:
                        tx, ty = box['x'] + 35, box['y'] + box['height']/2
                        await page.mouse.move(tx, ty, steps=80)
                        await page.mouse.click(tx, ty)
                        print(f"Trial {i}: Solving...")
                        await asyncio.sleep(8) # Wait for result visibility
                    else:
                        await page.mouse.move(box['x'] + box['width'] - 40, box['y'] + 30, steps=80)
                        await page.mouse.click(box['x'] + box['width'] - 40, box['y'] + 30)
                        print(f"Trial {i}: Failing...")
                        await asyncio.sleep(6)
                
                # Check for token & submit
                token = ""
                for _ in range(15):
                    token = await page.eval_on_selector("[name='cf-turnstile-response']", "el => el.value")
                    if token and len(token) > 20: break
                    await asyncio.sleep(0.5)
                
                if token and len(token) > 20 and should_solve:
                    await page.click("#submit-btn")
                    try:
                        await page.wait_for_selector("text='Success! Verified'", timeout=5000)
                        success_count += 1
                        print(f"Trial {i}: Verified!")
                    except: pass
                await asyncio.sleep(2)
            except Exception as e:
                print(f"Trial {i} error: {e}")
            
            print(f"Waiting 3s delay...")
            await asyncio.sleep(3)
            
        video_path = await page.video.path()
        await context.close()
        await browser.close()
        dest = "videos/Task_1_Consolidated.webm"
        if os.path.exists(video_path):
            if os.path.exists(dest): os.remove(dest)
            os.rename(video_path, dest)
            print(f"Done. Video: {dest}")
        print(f"Success Rate: {(success_count / total_trials) * 100}%")

if __name__ == "__main__": asyncio.run(run_trials())
