#!/usr/bin/env python3
"""
Test raw response without JSON parsing
"""
import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from services.openai_meal_service import OpenAIMealService

load_dotenv()

def test_raw():
    service = OpenAIMealService()
    
    if not service.is_available():
        print("API not available")
        return
    
    user_data = {'body_weight': 175}
    
    try:
        print("Generating meal plan...")
        # Call the internal method directly
        body_weight = 175
        total_calories = 175 * 15 + 500  # Training day
        protein_g = 175
        fats_calories = total_calories * 0.25
        fats_g = round(fats_calories / 9)
        protein_calories = protein_g * 4
        carbs_calories = total_calories - protein_calories - fats_calories
        carbs_g = round(carbs_calories / 4)
        
        prompt = service._build_single_day_prompt(
            body_weight=body_weight,
            total_calories=total_calories,
            protein_g=protein_g,
            carbs_g=carbs_g,
            fats_g=fats_g,
            day_type="training day",
            dietary_requirements=[]
        )
        
        print(f"Prompt length: {len(prompt)} chars")
        print("\nSending to API...")
        
        response = service.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Return ONLY valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        
        content = response.choices[0].message.content
        print(f"\nRaw response ({len(content)} chars):")
        print(content[:500] + "..." if len(content) > 500 else content)
        
        # Try to parse
        import json
        try:
            data = json.loads(content)
            print("\n✓ Valid JSON!")
        except:
            print("\n✗ Invalid JSON")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_raw()