import asyncio
from playwright.async_api import async_playwright
import os

async def run():
    # Ensure docs/assets dir exists
    os.makedirs("docs/assets", exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Use a high resolution viewport
        page = await browser.new_page(viewport={"width": 1440, "height": 900})
        
        print("Navigating to app...")
        await page.goto("https://centaurus-six.vercel.app/app/")
        
        # Wait for "Backend Connected" indicator
        try:
            print("Waiting for backend connection...")
            await page.wait_for_selector('text=Backend Connected', timeout=30000)
            print("Backend connected.")
        except Exception as e:
            print("Warning: Backend connection indicator not found or timed out.", e)
            
        print("Taking initial screenshot...")
        await page.screenshot(path="docs/assets/ui-initial.png")
        
        print("Entering identity information...")
        await page.fill('#user_email', 'sara.johnson@xyz.com')
        
        print("Sending message...")
        await page.fill('#message', 'When will I get my royalty payment?')
        
        async with page.expect_response("**/chat") as response_info:
            await page.click('button[type="submit"]')
        
        response = await response_info.value
        print(f"Chat response status: {response.status}")
        
        print("Waiting for bot response to render...")
        await asyncio.sleep(2)
        
        print("Taking chat screenshot...")
        await page.screenshot(path="docs/assets/ui-chat.png")
        
        print("Navigating to Quality Dashboard...")
        # Click the Dashboard tab
        await page.click('button[data-tab="dashboard"]')
        await asyncio.sleep(1)
        
        print("Refreshing dashboard stats...")
        await page.click('#dashboardRefresh')
        await asyncio.sleep(2)
        
        print("Taking dashboard screenshot...")
        await page.screenshot(path="docs/assets/ui-dashboard.png")
        
        await browser.close()
        print("Done!")

if __name__ == "__main__":
    asyncio.run(run())
