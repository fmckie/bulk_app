#!/usr/bin/env python3
"""
Save full API response for analysis
"""
import os
import sys
import json
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from services.openai_meal_service import OpenAIMealService

load_dotenv()

def test_and_save():
    service = OpenAIMealService()
    
    if not service.is_available():
        print("API not available")
        return
    
    user_data = {'body_weight': 175, 'dietary_requirements': []}
    
    try:
        print("Generating training day meal plan...")
        result = service.generate_single_day_meal_plan(user_data, is_training_day=True)
        
        # Save to file
        with open('api_response_training.json', 'w') as f:
            json.dump(result, f, indent=2)
        print("✓ Saved to api_response_training.json")
        
        # Quick validation
        if 'day_plan' in result:
            day_plan = result['day_plan']
            targets = day_plan.get('total_targets', {})
            print(f"\nTargets: {targets['calories']} cal, {targets['protein_g']}g P")
            
            # Calculate actuals
            meals = day_plan.get('meals', [])
            totals = {'calories': 0, 'protein_g': 0, 'carbs_g': 0, 'fats_g': 0}
            for meal in meals:
                for key in totals:
                    totals[key] += meal.get(key, 0)
            
            print(f"Actuals: {totals['calories']} cal, {totals['protein_g']}g P")
            
            # Check accuracy
            cal_accuracy = (totals['calories'] / targets['calories'] * 100)
            print(f"Accuracy: {cal_accuracy:.1f}%")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_and_save()