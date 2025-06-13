import asyncio
import os
from pyppeteer import launch

async def take_screenshots():
    browser = await launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
    page = await browser.newPage()
    
    # Set viewport to mobile width as specified in CLAUDE.md
    await page.setViewport({'width': 425, 'height': 800})
    
    screenshots_dir = 'screenshots'
    os.makedirs(screenshots_dir, exist_ok=True)
    
    try:
        # Homepage
        print("Navigating to homepage...")
        await page.goto('http://localhost:8000/', waitUntil='networkidle2', timeout=30000)
        await page.screenshot({'path': f'{screenshots_dir}/homepage_mobile.png', 'fullPage': False})
        print(f"✓ Homepage screenshot saved to {screenshots_dir}/homepage_mobile.png")
        
        # Epic Dashboard
        print("Navigating to epic dashboard...")
        await page.goto('http://localhost:8000/dashboard-epic', waitUntil='networkidle2', timeout=30000)
        await page.screenshot({'path': f'{screenshots_dir}/epic_dashboard_mobile.png', 'fullPage': False})
        print(f"✓ Epic dashboard screenshot saved to {screenshots_dir}/epic_dashboard_mobile.png")
        
        # Main app page
        print("Navigating to main app...")
        await page.goto('http://localhost:8000/app', waitUntil='networkidle2', timeout=30000)
        await page.screenshot({'path': f'{screenshots_dir}/main-app.png', 'fullPage': True})
        print(f"✓ Main app screenshot saved to {screenshots_dir}/main-app.png")
        
        # Meal prep page
        print("Navigating to meal prep page...")
        response = await page.goto('http://localhost:8000/meal-prep', waitUntil='networkidle2', timeout=30000)
        if response and response.status == 200:
            await page.screenshot({'path': f'{screenshots_dir}/meal-prep.png', 'fullPage': True})
            print(f"✓ Meal prep page screenshot saved to {screenshots_dir}/meal-prep.png")
        else:
            print(f"✗ Meal prep page returned status: {response.status if response else 'No response'}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await browser.close()

asyncio.run(take_screenshots())