#!/usr/bin/env python3
"""
Test single day AI meal generation with real API
"""
import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.openai_meal_service import OpenAIMealService

# Load environment variables
load_dotenv()


def validate_meal_plan(meal_plan: dict, expected_targets: dict):
    """Validate the accuracy of generated meal plan"""
    day_plan = meal_plan.get('day_plan', {})
    targets = day_plan.get('total_targets', {})
    meals = day_plan.get('meals', [])
    
    # Calculate actual totals
    actual = {'calories': 0, 'protein_g': 0, 'carbs_g': 0, 'fats_g': 0}
    
    for meal in meals:
        actual['calories'] += meal.get('calories', 0)
        actual['protein_g'] += meal.get('protein_g', 0)
        actual['carbs_g'] += meal.get('carbs_g', 0)
        actual['fats_g'] += meal.get('fats_g', 0)
    
    # Check accuracy
    print("\nValidation Results:")
    print("-" * 50)
    
    all_accurate = True
    for macro in ['calories', 'protein_g', 'carbs_g', 'fats_g']:
        target = targets.get(macro, 0)
        actual_val = actual[macro]
        if target > 0:
            accuracy = (actual_val / target) * 100
            tolerance = 2 if macro == 'calories' else 5
            is_accurate = abs(100 - accuracy) <= tolerance
            
            status = "✓" if is_accurate else "✗"
            print(f"{status} {macro}: {actual_val} / {target} ({accuracy:.1f}%)")
            
            if not is_accurate:
                all_accurate = False
    
    return all_accurate


def main():
    print("=== Single Day AI Meal Generation Test ===\n")
    
    # Initialize service
    service = OpenAIMealService()
    
    if not service.is_available():
        print("❌ OpenAI API not available. Check your API key.")
        return
    
    # Test data
    user_data = {
        'body_weight': 175,
        'age': 25,
        'gender': 'male',
        'dietary_requirements': []
    }
    
    print(f"User Profile:")
    print(f"- Body weight: {user_data['body_weight']} lbs")
    print(f"- Maintenance: {user_data['body_weight'] * 15} calories")
    
    # Test training day
    print(f"\n{'='*50}")
    print("Testing TRAINING DAY (+500 calorie surplus)")
    print(f"{'='*50}")
    
    try:
        result = service.generate_single_day_meal_plan(
            user_data=user_data,
            is_training_day=True
        )
        
        # Save output
        output_file = 'single_day_training.json'
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\n✓ Saved to {output_file}")
        
        # Display results
        day_plan = result.get('day_plan', {})
        targets = day_plan.get('total_targets', {})
        
        print(f"\nTargets:")
        print(f"- Calories: {targets.get('calories')}")
        print(f"- Protein: {targets.get('protein_g')}g")
        print(f"- Carbs: {targets.get('carbs_g')}g")
        print(f"- Fats: {targets.get('fats_g')}g")
        
        # Validate
        is_accurate = validate_meal_plan(result, targets)
        
        # Display meals
        print(f"\nGenerated Meals:")
        print("-" * 50)
        meals = day_plan.get('meals', [])
        for meal in meals:
            print(f"\nMeal {meal.get('meal_number', '')} @ {meal.get('time', '')}")
            print(f"  {meal.get('name', 'Unknown')}")
            print(f"  {meal.get('calories', 0)} cal | P: {meal.get('protein_g', 0)}g | C: {meal.get('carbs_g', 0)}g | F: {meal.get('fats_g', 0)}g")
            
            # Show key ingredients
            ingredients = meal.get('ingredients', [])[:3]
            if ingredients:
                print("  Key ingredients:")
                for ing in ingredients:
                    print(f"    - {ing.get('amount', '')}{ing.get('unit', '')} {ing.get('name', '')}")
        
        print(f"\n{'✓ PASS' if is_accurate else '✗ FAIL'}: Nutritional accuracy {'within tolerance' if is_accurate else 'outside tolerance'}")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test rest day
    print(f"\n\n{'='*50}")
    print("Testing REST DAY (+100 calorie surplus)")
    print(f"{'='*50}")
    
    try:
        result = service.generate_single_day_meal_plan(
            user_data=user_data,
            is_training_day=False
        )
        
        # Save output
        output_file = 'single_day_rest.json'
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\n✓ Saved to {output_file}")
        
        # Quick validation
        day_plan = result.get('day_plan', {})
        targets = day_plan.get('total_targets', {})
        
        print(f"\nTargets:")
        print(f"- Calories: {targets.get('calories')} (should be ~{175*15 + 100})")
        
        is_accurate = validate_meal_plan(result, targets)
        print(f"\n{'✓ PASS' if is_accurate else '✗ FAIL'}: Rest day accuracy")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")


if __name__ == "__main__":
    main()