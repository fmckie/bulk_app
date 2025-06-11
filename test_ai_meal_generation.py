#!/usr/bin/env python3
"""
Test script for AI meal generation optimization
Tests real OpenAI API responses for meal planning accuracy
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


def calculate_targets(body_weight: int, is_training_day: bool):
    """Calculate Kinobody nutritional targets"""
    maintenance = body_weight * 15
    
    if is_training_day:
        total_calories = maintenance + 500
    else:
        total_calories = maintenance + 100
    
    # Macros calculation
    protein_g = body_weight  # 1g per lb
    fats_calories = total_calories * 0.25
    fats_g = fats_calories / 9
    
    protein_calories = protein_g * 4
    carbs_calories = total_calories - protein_calories - fats_calories
    carbs_g = carbs_calories / 4
    
    return {
        'maintenance': maintenance,
        'total_calories': round(total_calories),
        'protein_g': round(protein_g),
        'carbs_g': round(carbs_g),
        'fats_g': round(fats_g),
        'calorie_surplus': 500 if is_training_day else 100
    }


def validate_meal_plan(meal_plan: dict, targets: dict):
    """Validate if meal plan meets nutritional targets"""
    results = {
        'valid': True,
        'errors': [],
        'warnings': [],
        'actual_totals': {
            'calories': 0,
            'protein_g': 0,
            'carbs_g': 0,
            'fats_g': 0
        },
        'accuracy': {}
    }
    
    # Extract day 1 data (since we're testing single day)
    if 'meal_plan' in meal_plan and 'day_1' in meal_plan['meal_plan']:
        day_data = meal_plan['meal_plan']['day_1']
        
        # Sum up all meals
        for meal_key, meal in day_data.get('meals', {}).items():
            if isinstance(meal, dict) and 'calories' in meal:
                results['actual_totals']['calories'] += meal.get('calories', 0)
                results['actual_totals']['protein_g'] += meal.get('protein_g', 0)
                results['actual_totals']['carbs_g'] += meal.get('carbs_g', 0)
                results['actual_totals']['fats_g'] += meal.get('fats_g', 0)
                
                # Check meal timing
                meal_time = meal.get('time', '')
                if meal_time:
                    hour = int(meal_time.split(':')[0])
                    if meal_time.endswith('AM') or (meal_time.endswith('PM') and hour < 12 and hour != 12):
                        if not (meal_time.endswith('PM') and hour >= 12):
                            results['warnings'].append(f"Meal at {meal_time} is outside IF window (12pm-8pm)")
                    elif meal_time.endswith('PM') and (hour > 8 or (hour == 8 and int(meal_time.split(':')[1].split()[0]) > 0)):
                        results['warnings'].append(f"Meal at {meal_time} is outside IF window (12pm-8pm)")
    
    # Calculate accuracy
    for macro in ['calories', 'protein_g', 'carbs_g', 'fats_g']:
        target = targets.get(macro.replace('calories', 'total_calories'), 0)
        actual = results['actual_totals'][macro]
        if target > 0:
            accuracy = (actual / target) * 100
            results['accuracy'][macro] = round(accuracy, 1)
            
            # Check if within 5% tolerance
            if abs(100 - accuracy) > 5:
                results['valid'] = False
                results['errors'].append(
                    f"{macro}: {actual} ({accuracy:.1f}% of target {target})"
                )
    
    return results


def test_single_day_generation():
    """Test single day meal plan generation"""
    print("=== Testing AI Meal Plan Generation ===\n")
    
    # Initialize service
    service = OpenAIMealService()
    
    if not service.is_available():
        print("❌ OpenAI service not available. Check API key.")
        return
    
    # Test cases
    test_cases = [
        {
            'name': 'Training Day - 175lb Male',
            'body_weight': 175,
            'is_training_day': True,
            'dietary_requirements': []
        },
        {
            'name': 'Rest Day - 175lb Male',
            'body_weight': 175,
            'is_training_day': False,
            'dietary_requirements': []
        }
    ]
    
    for test in test_cases:
        print(f"\n{'='*50}")
        print(f"Test: {test['name']}")
        print(f"{'='*50}")
        
        # Calculate targets
        targets = calculate_targets(test['body_weight'], test['is_training_day'])
        
        print(f"\nNutritional Targets:")
        print(f"  Calories: {targets['total_calories']} (maintenance: {targets['maintenance']} + {targets['calorie_surplus']})")
        print(f"  Protein: {targets['protein_g']}g")
        print(f"  Carbs: {targets['carbs_g']}g")
        print(f"  Fats: {targets['fats_g']}g")
        
        # Prepare user data
        user_data = {
            'body_weight': test['body_weight'],
            'age': 25,
            'gender': 'male',
            'dietary_requirements': test['dietary_requirements'],
            'budget': 150,
            'training_days': ['Monday', 'Wednesday', 'Friday'] if test['is_training_day'] else []
        }
        
        print(f"\nGenerating meal plan...")
        
        try:
            # Generate meal plan
            meal_plan = service.generate_meal_plan(user_data)
            
            # Save raw output for analysis
            output_file = f"test_output_{test['name'].replace(' ', '_').lower()}.json"
            with open(output_file, 'w') as f:
                json.dump(meal_plan, f, indent=2)
            print(f"✓ Saved raw output to {output_file}")
            
            # Validate the meal plan
            validation = validate_meal_plan(meal_plan, targets)
            
            print(f"\nValidation Results:")
            print(f"  Valid: {'✓' if validation['valid'] else '✗'}")
            
            print(f"\nActual Totals:")
            for macro, value in validation['actual_totals'].items():
                accuracy = validation['accuracy'].get(macro, 0)
                print(f"  {macro}: {value} ({accuracy}% of target)")
            
            if validation['errors']:
                print(f"\nErrors:")
                for error in validation['errors']:
                    print(f"  ❌ {error}")
            
            if validation['warnings']:
                print(f"\nWarnings:")
                for warning in validation['warnings']:
                    print(f"  ⚠️  {warning}")
            
            # Display meals
            if 'meal_plan' in meal_plan and 'day_1' in meal_plan['meal_plan']:
                day_data = meal_plan['meal_plan']['day_1']
                print(f"\nGenerated Meals:")
                for meal_key, meal in day_data.get('meals', {}).items():
                    if isinstance(meal, dict):
                        print(f"\n  {meal.get('name', meal_key)} @ {meal.get('time', 'N/A')}")
                        print(f"    Calories: {meal.get('calories', 0)}")
                        print(f"    Protein: {meal.get('protein_g', 0)}g")
                        print(f"    Carbs: {meal.get('carbs_g', 0)}g")
                        print(f"    Fats: {meal.get('fats_g', 0)}g")
        
        except Exception as e:
            print(f"❌ Error generating meal plan: {str(e)}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    test_single_day_generation()