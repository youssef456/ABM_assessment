import asyncio
import os
import json
import base64
from playwright.async_api import async_playwright

async def task_3_scraping():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Specified BLS Spain Captcha URL
        url = "https://egypt.blsspainglobal.com/Global/CaptchaPublic/GenerateCaptcha?data=4CDiA9odF2%2b%2bsWCkAU8htqZkgDyUa5SR6waINtJfg1ThGb6rPIIpxNjefP9UkAaSp%2fGsNNuJJi5Zt1nbVACkDRusgqfb418%2bScFkcoa1F0I%3d"
        print(f"Navigating to BLS Captcha page...")
        
        try:
            await page.goto(url, wait_until="networkidle", timeout=60000)
        except Exception as e:
            print(f"Navigation timed out: {e}. Trying again with shorter wait...")
            await page.goto(url, wait_until="domcontentloaded")
            await asyncio.sleep(5)

        print("Scraping ALL images as base64...")
        # Get all img tags
        all_images_data = await page.evaluate("""
            async () => {
                const images = Array.from(document.querySelectorAll('img'));
                const results = [];
                for (const img of images) {
                    try {
                        const canvas = document.createElement('canvas');
                        canvas.width = img.naturalWidth || img.width;
                        canvas.height = img.naturalHeight || img.height;
                        const ctx = canvas.getContext('2d');
                        ctx.drawImage(img, 0, 0);
                        results.push({
                            src: img.src,
                            alt: img.alt,
                            id: img.id,
                            base64: canvas.toDataURL('image/png')
                        });
                    } catch (e) {
                        results.push({ src: img.src, error: e.message, base64: null });
                    }
                }
                return results;
            }
        """)
        
        with open("allimages.json", "w") as f:
            json.dump(all_images_data, f, indent=4)
        print(f"Saved {len(all_images_data)} total images to allimages.json")

        print("Scraping only the 9 human-visible captcha images...")
        # Based on investigation, visible images have class 'captcha-img' and are in the grid
        visible_images_data = await page.evaluate("""
            async () => {
                const images = Array.from(document.querySelectorAll('.captcha-img, img'))
                    .filter(img => {
                        const style = window.getComputedStyle(img);
                        const rect = img.getBoundingClientRect();
                        return (
                            style.display !== 'none' &&
                            style.visibility !== 'hidden' &&
                            rect.width > 10 && rect.height > 10 &&
                            rect.top >= 0 && rect.left >= 0
                        );
                    });
                
                // We specifically want the 9 grid images
                const gridImages = images.slice(0, 9);
                const results = [];
                for (const img of gridImages) {
                    const canvas = document.createElement('canvas');
                    canvas.width = img.naturalWidth || img.width;
                    canvas.height = img.naturalHeight || img.height;
                    const ctx = canvas.getContext('2d');
                    ctx.drawImage(img, 0, 0);
                    results.push({
                        src: img.src,
                        base64: canvas.toDataURL('image/png')
                    });
                }
                return results;
            }
        """)
        
        with open("visible_images_only.json", "w") as f:
            json.dump(visible_images_data, f, indent=4)
        print(f"Saved {len(visible_images_data)} visible images to visible_images_only.json")

        print("Scraping the visible text instruction...")
        # The site has many hidden instructions. We find the one that is human-visible.
        visible_instruction = await page.evaluate("""
            () => {
                const instructions = Array.from(document.querySelectorAll('body *'))
                    .filter(el => {
                        const style = window.getComputedStyle(el);
                        const rect = el.getBoundingClientRect();
                        
                        // STRICT VISIBILITY CHECK
                        const isVisible = (
                            el.innerText && el.innerText.trim().length > 5 &&
                            style.display !== 'none' &&
                            style.visibility !== 'hidden' &&
                            style.opacity !== '0' &&
                            rect.width > 0 && rect.height > 0 &&
                            el.offsetParent !== null &&
                            (el.innerText.toLowerCase().includes('select') || el.innerText.toLowerCase().includes('number'))
                        );
                        
                        // Check if it's the specific instruction container
                        return isVisible;
                    })
                    .map(el => el.innerText.trim());
                
                // Return the first purely text instruction that isn't just a container for others
                // Often the visible one is the only one with offsetParent
                return instructions[0] || "No visible instruction found";
            }
        """)
        
        # If it returned a multiline string, take the first non-empty line
        clean_instruction = visible_instruction.split('\n')[0].strip()
        print(f"\nFinal Captured Instruction: {clean_instruction}")
        
        # Save instruction to a text file
        with open("instructions.txt", "w") as f:
            f.write(clean_instruction)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(task_3_scraping())
