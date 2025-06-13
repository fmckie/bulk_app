import asyncio
import os
from pyppeteer import launch

async def test_meal_prep():
    browser = await launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
    page = await browser.newPage()
    
    # Capture console logs
    page.on('console', lambda msg: print(f'Console {msg.type}: {msg.text}'))
    page.on('pageerror', lambda err: print(f'Page error: {err}'))
    
    # Set viewport to mobile width as specified in CLAUDE.md
    await page.setViewport({'width': 425, 'height': 800})
    
    screenshots_dir = 'screenshots/meal-prep-test'
    os.makedirs(screenshots_dir, exist_ok=True)
    
    try:
        # 1. Navigate to meal prep page
        print("1. Navigating to meal prep page...")
        await page.goto('http://localhost:8000/meal-prep', waitUntil='networkidle2', timeout=30000)
        await page.screenshot({'path': f'{screenshots_dir}/1-initial-page.png', 'fullPage': True})
        print(f"✓ Initial page screenshot saved")
        
        # 2. Check dietary options
        print("2. Selecting dietary preferences...")
        # Check vegetarian option
        vegetarian_checkbox = await page.querySelector('input[type="checkbox"][value="vegetarian"]')
        if vegetarian_checkbox:
            await vegetarian_checkbox.click()
            await page.screenshot({'path': f'{screenshots_dir}/2-vegetarian-selected.png', 'fullPage': True})
            print(f"✓ Vegetarian option selected")
        
        # 3. Set budget
        print("3. Setting weekly budget...")
        budget_input = await page.querySelector('input#budget')
        if budget_input:
            await budget_input.click({'clickCount': 3})  # Triple-click to select all
            await budget_input.type('200')
            await page.screenshot({'path': f'{screenshots_dir}/3-budget-set.png', 'fullPage': True})
            print(f"✓ Budget set to $200")
        
        # 3.5 Disable AI to use demo meal plan
        print("3.5. Disabling AI to use demo meal plan...")
        ai_toggle = await page.querySelector('input#aiAssistant')
        if ai_toggle:
            # Check if it's currently checked
            is_checked = await page.evaluate('(element) => element.checked', ai_toggle)
            if is_checked:
                await ai_toggle.click()
                print(f"✓ AI assistant disabled - will use demo meal plan")
        
        # 4. Click generate meal plan button
        print("4. Clicking generate meal plan button...")
        generate_button = await page.querySelector('button[type="submit"]')
        if generate_button:
            await generate_button.click()
            print("✓ Generate button clicked")
            
            # 5. Wait for loading to complete and meals to appear
            print("5. Waiting for meal plan generation...")
            try:
                # Wait for the meal plan section to become visible
                await page.waitForSelector('#mealPlanSection', {
                    'timeout': 30000,
                    'visible': True
                })
                
                # Give it a moment for all cards to render
                await page.waitFor(2000)
                
                # 6. Take screenshot of generated meals
                await page.screenshot({'path': f'{screenshots_dir}/4-generated-meals.png', 'fullPage': True})
                print(f"✓ Generated meals screenshot saved")
                
                # 7. Count the number of meal cards
                meal_cards = await page.querySelectorAll('.meal-card')
                print(f"✓ Found {len(meal_cards)} meal cards")
                
                # 8. Click on first meal's recipe button if available
                if meal_cards:
                    # Scroll to first meal card
                    await page.evaluate('(element) => element.scrollIntoView({behavior: "smooth", block: "center"})', meal_cards[0])
                    await page.waitFor(500)
                    
                    recipe_button = await meal_cards[0].querySelector('.recipe-btn')
                    if recipe_button:
                        await recipe_button.click()
                        await page.waitFor(1000)
                        await page.screenshot({'path': f'{screenshots_dir}/5-recipe-modal.png', 'fullPage': True})
                        print(f"✓ Recipe modal screenshot saved")
                        
                        # Close modal
                        close_button = await page.querySelector('.modal .close')
                        if close_button:
                            await close_button.click()
                            await page.waitFor(500)
                
                # 9. Scroll to saved meal plans section
                saved_meals_section = await page.querySelector('#saved-meal-plans')
                if saved_meals_section:
                    await page.evaluate('(element) => element.scrollIntoView()', saved_meals_section)
                    await page.waitFor(500)
                    await page.screenshot({'path': f'{screenshots_dir}/6-saved-plans.png', 'fullPage': True})
                    print(f"✓ Saved meal plans section screenshot saved")
                    
            except Exception as e:
                print(f"✗ Error waiting for meal generation: {e}")
                # Take error screenshot
                await page.screenshot({'path': f'{screenshots_dir}/error-state.png', 'fullPage': True})
                
                # Check for error messages
                error_message = await page.querySelector('.error-message')
                if error_message:
                    error_text = await page.evaluate('(element) => element.textContent', error_message)
                    print(f"Error message found: {error_text}")
        else:
            print("✗ Generate button not found")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await browser.close()

asyncio.run(test_meal_prep())