import asyncio
import os
import random
import math
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

# Advanced Human Mouse Movement Utility
def get_human_path(start, end):
    """Generates a human-like path from start to end with acceleration, deceleration, and overshoot."""
    path = []
    
    # 1. Randomize control points for a unique Bezier curve every time
    # This prevents the "same movement" look
    mid_x = (start['x'] + end['x']) / 2 + random.uniform(-100, 100)
    mid_y = (start['y'] + end['y']) / 2 + random.uniform(-100, 100)
    
    # Optional second control point for more complex curves
    mid2_x = (mid_x + end['x']) / 2 + random.uniform(-30, 30)
    mid2_y = (mid_y + end['y']) / 2 + random.uniform(-30, 30)
    
    points = [start, {'x': mid_x, 'y': mid_y}, {'x': mid2_x, 'y': mid2_y},终点 := {'x': end['x'], 'y': end['y']}]
    
    # 2. Variable velocity (Acceleration/Deceleration)
    # We use a non-linear distribution of 't' (time)
    steps = random.randint(45, 75)
    for i in range(steps + 1):
        # Sine-based easing for smooth start/stop
        t = i / steps
        velocity_t = (1 - math.cos(t * math.pi)) / 2 
        
        # Cubic Bezier calculation
        x = (1-velocity_t)**3 * points[0]['x'] + 3*(1-velocity_t)**2*velocity_t * points[1]['x'] + 3*(1-velocity_t)*velocity_t**2 * points[2]['x'] + velocity_t**3 * points[3]['x']
        y = (1-velocity_t)**3 * points[0]['y'] + 3*(1-velocity_t)**2*velocity_t * points[1]['y'] + 3*(1-velocity_t)*velocity_t**2 * points[2]['y'] + velocity_t**3 * points[3]['y']
        
        # Add micro-jitters
        x += random.uniform(-0.5, 0.5)
        y += random.uniform(-0.5, 0.5)
        
        path.append({'x': x, 'y': y})
    
    # 3. Tiny "Overshoot" and Correction (Real humans aren't robotic in their stop)
    if random.random() > 0.4:
        overshoot_x = end['x'] + random.uniform(-5, 5)
        overshoot_y = end['y'] + random.uniform(-5, 5)
        for i in range(5):
            t = i / 5
            path.append({
                'x': end['x'] + (overshoot_x - end['x']) * (1 - t),
                'y': end['y'] + (overshoot_y - end['y']) * (1 - t)
            })
            
    return path

async def run_trials(total_trials=10):
    async with async_playwright() as p:
        os.makedirs("videos", exist_ok=True)
        # Use a realistic browser window
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            record_video_dir="videos/temp_task_1/",
            record_video_size={"width": 1280, "height": 720},
            viewport={"width": 1280, "height": 720}
        )
        
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        url = "https://cd.captchaaiplus.com/turnstile.html"
        success_count = 0
        current_mouse_pos = {'x': 0, 'y': 0}

        async def move_humanly(dest_x, dest_y):
            nonlocal current_mouse_pos
            path = get_human_path(current_mouse_pos, {'x': dest_x, 'y': dest_y})
            for point in path:
                await page.mouse.move(point['x'], point['y'])
                # Variable sleep to mimic nerve response time
                await asyncio.sleep(random.uniform(0.005, 0.012))
            current_mouse_pos = {'x': dest_x, 'y': dest_y}
            await asyncio.sleep(random.uniform(0.1, 0.2))

        for i in range(1, total_trials + 1):
            print(f"--- Starting Trial {i} ---")
            should_solve = i in [1, 2, 4, 6, 8, 10]
            
            try:
                await page.goto(url, wait_until="load", timeout=60000)
                await asyncio.sleep(random.uniform(2, 4))
                
                # Starting position randomization
                if i == 1:
                    current_mouse_pos = {'x': random.randint(900, 1200), 'y': random.randint(100, 600)}
                    await page.mouse.move(current_mouse_pos['x'], current_mouse_pos['y'])

                # Precise detection of the clickable checkbox
                # Coordinates from getBoundingClientRect are relative to viewport
                box = await page.evaluate("""() => {
                    function getDeepBox(root) {
                        const iframes = root.querySelectorAll('iframe');
                        for (const ifr of iframes) {
                            if (ifr.src.includes('cloudflare') || ifr.src.includes('turnstile')) {
                                const rect = ifr.getBoundingClientRect();
                                return {x: rect.x, y: rect.y, width: rect.width, height: rect.height};
                            }
                        }
                        const els = root.querySelectorAll('*');
                        for (const el of els) {
                            if (el.shadowRoot) {
                                const found = getDeepBox(el.shadowRoot);
                                if (found) return found;
                            }
                        }
                        return null;
                    }
                    // Try Shadow/Iframe detection first
                    let res = getDeepBox(document);
                    if (res) return res;
                    
                    // Fallback to the main container div
                    const container = document.querySelector('.cf-turnstile');
                    if (container) {
                        const rect = container.getBoundingClientRect();
                        return {x: rect.x, y: rect.y, width: rect.width, height: rect.height};
                    }
                    return null;
                }""")

                if box:
                    if should_solve:
                        # TARGET the checkbox EXACTLY (usually roughly (30, 32) relative to iframe)
                        # We use randomized offsets within the checkbox area (usually 25x25)
                        cb_x = box['x'] + 32 + random.randint(-4, 4)
                        cb_y = box['y'] + box['height'] / 2 + random.randint(-4, 4)
                        
                        print(f"Trial {i}: Moving to checkbox ({cb_x}, {cb_y})...")
                        await move_humanly(cb_x, cb_y)
                        
                        # Real human click sequence
                        await page.mouse.down()
                        await asyncio.sleep(random.uniform(0.06, 0.12))
                        await page.mouse.up()
                        
                        print(f"Trial {i}: Clicked. Waiting for widget response...")
                        await asyncio.sleep(7)
                    else:
                        print(f"Trial {i}: Simulating failure (intentional move away)...")
                        await move_humanly(box['x'] + box['width'] + 100, box['y'] + random.randint(-50, 50))
                        await page.mouse.click(box['x'] + box['width'] + 100, box['y'] + 30)
                        await asyncio.sleep(5)
                else:
                    print(f"Trial {i}: Widget not detected visually. Moving to approximate area.")
                    await move_humanly(150 + random.randint(-20, 20), 400 + random.randint(-20, 20))
                    await asyncio.sleep(2)

                # Attempt submission if token arrived
                token = await page.eval_on_selector("[name='cf-turnstile-response']", "el => el.value")
                if token and len(token) > 20 and should_solve:
                    submit_btn = page.locator("#submit-btn")
                    s_box = await submit_btn.bounding_box()
                    if s_box:
                        await move_humanly(s_box['x'] + s_box['width']/2, s_box['y'] + s_box['height']/2)
                    
                    await page.mouse.down()
                    await asyncio.sleep(random.uniform(0.08, 0.15))
                    await page.mouse.up()
                    
                    try:
                        await page.wait_for_selector("text='Success! Verified'", timeout=6000)
                        success_count += 1
                        print(f"Trial {i}: Success! Verified.")
                    except: pass
                
                await asyncio.sleep(2)
            except Exception as e:
                print(f"Error in Trial {i}: {e}")
            
            # Explicit 3-second delay between trials
            print(f"Trial {i} complete. Next trial in 3s...")
            await asyncio.sleep(3)
            
        video_path = await page.video.path()
        await context.close()
        await browser.close()
        
        dest_video = "videos/Task_1_Consolidated.webm"
        if os.path.exists(video_path):
            if os.path.exists(dest_video): os.remove(dest_video)
            os.rename(video_path, dest_video)
            print(f"Consolidated video saved to: {dest_video}")
            
        print(f"Final Success Rate: {(success_count / total_trials) * 100}%")

if __name__ == "__main__":
    asyncio.run(run_trials())
