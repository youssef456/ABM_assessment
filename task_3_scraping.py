import asyncio
import os
import json
import base64
from playwright.async_api import async_playwright

async def task_3_scraping():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # The URL for scraping assessment - using the base domain/scraping if not specified
        # Based on task 1/2, it might be at a similar path.
        url = "https://cd.captchaaiplus.com/scraping.html" # Placeholder URL based on previous pattern
        print(f"Navigating to {url} for scraping...")
        
        try:
            await page.goto(url, wait_until="networkidle")
        except Exception as e:
            print(f"Navigation failed: {e}. Trying alternate URL...")
            # If the user's "Click Here" link points elsewhere, we'd need that.
            # Assuming it's on the same site.
            await page.goto("https://cd.captchaaiplus.com/", wait_until="networkidle")

        print("Scraping all images...")
        all_images = await page.eval_on_selector_all("img", """
            imgs => {
                return imgs.map(img => {
                    return {
                        src: img.src,
                        alt: img.alt,
                        id: img.id,
                        className: img.className
                    };
                });
            }
        """)
        
        # Encode all images to base64
        all_images_base64 = []
        for img_info in all_images:
            try:
                # We can use page.evaluate to get base64 of an image efficiently
                b64_data = await page.evaluate(f"""
                    async () => {{
                        const img = document.querySelector('img[src="{img_info['src']}"]');
                        if (!img) return null;
                        const canvas = document.createElement('canvas');
                        canvas.width = img.naturalWidth;
                        canvas.height = img.naturalHeight;
                        const ctx = canvas.getContext('2d');
                        ctx.drawImage(img, 0, 0);
                        return canvas.toDataURL('image/png');
                    }}
                """)
                if b64_data:
                    all_images_base64.append({
                        "id": img_info.get("id"),
                        "src": img_info["src"],
                        "base64": b64_data
                    })
            except Exception as e:
                print(f"Failed to encode image {img_info['src']}: {e}")

        with open("allimages.json", "w") as f:
            json.dump(all_images_base64, f, indent=4)
        print(f"Saved {len(all_images_base64)} images to allimages.json")

        print("Scraping visible images only...")
        # A human-visible image is one that is in the viewport and not display:none or visibility:hidden
        visible_images_base64 = await page.evaluate("""
            async () => {
                const imgs = Array.from(document.querySelectorAll('img'));
                const visible = imgs.filter(img => {
                    const style = window.getComputedStyle(img);
                    const rect = img.getBoundingClientRect();
                    return (
                        style.display !== 'none' &&
                        style.visibility !== 'hidden' &&
                        style.opacity !== '0' &&
                        rect.width > 0 &&
                        rect.height > 0 &&
                        rect.bottom > 0 &&
                        rect.right > 0 &&
                        rect.top < window.innerHeight &&
                        rect.left < window.innerWidth
                    );
                });
                
                const results = [];
                for (const img of visible.slice(0, 9)) {
                    const canvas = document.createElement('canvas');
                    canvas.width = img.naturalWidth || img.width;
                    canvas.height = img.naturalHeight || img.height;
                    const ctx = canvas.getContext('2d');
                    ctx.drawImage(img, 0, 0);
                    results.append({
                        src: img.src,
                        base64: canvas.toDataURL('image/png')
                    });
                }
                return results;
            }
        """)
        
        with open("visible_images_only.json", "w") as f:
            json.dump(visible_images_base64, f, indent=4)
        print(f"Saved {len(visible_images_base64)} visible images to visible_images_only.json")

        print("Scraping visible text instructions...")
        visible_text = await page.evaluate("""
            () => {
                const elements = Array.from(document.querySelectorAll('body *'));
                return elements
                    .filter(el => {
                        const style = window.getComputedStyle(el);
                        const rect = el.getBoundingClientRect();
                        return (
                            el.childNodes.length === 1 && el.childNodes[0].nodeType === 3 && // has text node only
                            style.display !== 'none' &&
                            style.visibility !== 'hidden' &&
                            style.opacity !== '0' &&
                            rect.width > 0 &&
                            rect.height > 0
                        );
                    })
                    .map(el => el.innerText.trim())
                    .filter(txt => txt.length > 0);
            }
        """)
        
        print("\nVisible Instructions Captured:")
        for txt in visible_text:
            print(f"- {txt}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(task_3_scraping())
