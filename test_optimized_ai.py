#!/usr/bin/env python3
"""
Test the optimized AI meal generation
"""
import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.openai_meal_service_optimized import OpenAIMealServiceOptimized

# Load environment variables
load_dotenv()


def test_optimized_generation():
    """Test the optimized single-day meal generation"""
    print("=== Testing Optimized AI Meal Generation ===\n")
    
    # Initialize service
    service = OpenAIMealServiceOptimized()
    
    if not service.is_available():
        print("❌ OpenAI service not available. Check API key.")
        return
    
    # Test case: Training day for 175lb male
    user_data = {
        'body_weight': 175,
        'age': 25,
        'gender': 'male',
        'dietary_requirements': []
    }
    
    print("Generating Training Day Meal Plan...")
    print(f"Body weight: {user_data['body_weight']} lbs")
    print(f"Expected calories: {175 * 15 + 500} (maintenance + 500)")
    print(f"Expected protein: {user_data['body_weight']}g")
    
    try:
        # Generate meal plan
        result = service.generate_single_day_meal_plan(user_data, is_training_day=True)
        
        if result.get('success'):
            print("\n✓ Meal plan generated successfully!")
            
            # Save output
            with open('optimized_output.json', 'w') as f:
                json.dump(result, f, indent=2)
            print("✓ Saved to optimized_output.json")
            
            # Display targets
            targets = result.get('targets', {})
            print(f"\nTargets:")
            print(f"  Calories: {targets.get('calories')}")
            print(f"  Protein: {targets.get('protein_g')}g")
            print(f"  Carbs: {targets.get('carbs_g')}g")
            print(f"  Fats: {targets.get('fats_g')}g")
            
            # Validate accuracy
            validation = service.validate_meal_plan_accuracy(result)
            
            print(f"\nValidation:")
            print(f"  Valid: {'✓' if validation['valid'] else '✗'}")
            
            print(f"\nActual Totals:")
            for macro, value in validation['actual_totals'].items():
                accuracy = validation['accuracy'].get(macro, 0)
                print(f"  {macro}: {value} ({accuracy}% of target)")
            
            if validation['issues']:
                print(f"\nIssues:")
                for issue in validation['issues']:
                    print(f"  ⚠️  {issue}")
            
            # Display meals
            day_plan = result.get('day_plan', {})
            meals = day_plan.get('meals', [])
            
            print(f"\nMeals:")
            for meal in meals:
                print(f"\n  Meal {meal.get('meal_number')} - {meal.get('name')} @ {meal.get('time')}")
                print(f"    Calories: {meal.get('calories')}")
                print(f"    P: {meal.get('protein_g')}g, C: {meal.get('carbs_g')}g, F: {meal.get('fats_g')}g")
                
                # Show first 2 ingredients
                ingredients = meal.get('ingredients', [])
                if ingredients:
                    print(f"    Key ingredients:")
                    for ing in ingredients[:2]:
                        print(f"      - {ing['amount']}{ing['unit']} {ing['name']}")
        else:
            print("❌ Failed to generate meal plan")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_optimized_generation()