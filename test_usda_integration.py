#!/usr/bin/env python3
"""
Test USDA FoodData Central Integration
Tests the integration between AI meal generation and USDA validation
"""
import os
import sys
import json
import time
from datetime import datetime
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from services.openai_meal_service import OpenAIMealService
from services.usda_fooddata_service import USDAFoodDataService

load_dotenv()


def test_usda_search():
    """Test basic USDA food search functionality"""
    print("\n" + "="*60)
    print("TEST 1: USDA Food Search")
    print("="*60)
    
    usda = USDAFoodDataService()
    
    test_foods = [
        "chicken breast cooked",
        "white rice cooked",
        "olive oil",
        "sweet potato baked"
    ]
    
    for food in test_foods:
        print(f"\nSearching for: {food}")
        start_time = time.time()
        
        results = usda.search_foods(food, page_size=3)
        search_time = time.time() - start_time
        
        if results.get('foods'):
            print(f"✓ Found {len(results['foods'])} results in {search_time:.2f}s")
            
            # Show first result
            first = results['foods'][0]
            print(f"  Best match: {first.get('description', 'N/A')}")
            print(f"  Data type: {first.get('dataType', 'N/A')}")
            print(f"  FDC ID: {first.get('fdcId', 'N/A')}")
        else:
            print(f"✗ No results found")


def test_nutrient_extraction():
    """Test nutrient extraction from USDA data"""
    print("\n" + "="*60)
    print("TEST 2: Nutrient Extraction")
    print("="*60)
    
    usda = USDAFoodDataService()
    
    # Test with a known food (chicken breast)
    print("\nTesting nutrient extraction for 'chicken breast cooked'...")
    
    result = usda.search_and_match("chicken breast cooked", 100, "g")
    
    if result and 'calculated_nutrition' in result:
        nutrition = result['calculated_nutrition']
        print(f"\n✓ Nutrition per 100g:")
        print(f"  Calories: {nutrition.get('calories', 0)}")
        print(f"  Protein: {nutrition.get('protein_g', 0)}g")
        print(f"  Carbs: {nutrition.get('carbs_g', 0)}g")
        print(f"  Fat: {nutrition.get('fats_g', 0)}g")
        print(f"  Fiber: {nutrition.get('fiber_g', 0)}g")
        
        # Verify against known values
        expected_calories = 165  # USDA value for cooked chicken breast
        actual_calories = nutrition.get('calories', 0)
        variance = abs(actual_calories - expected_calories) / expected_calories
        
        if variance < 0.1:  # Within 10%
            print(f"\n✓ Accuracy check PASSED: {variance:.1%} variance")
        else:
            print(f"\n✗ Accuracy check FAILED: {variance:.1%} variance")
    else:
        print("✗ Failed to extract nutrition data")


def test_meal_plan_validation():
    """Test AI meal plan generation with USDA validation"""
    print("\n" + "="*60)
    print("TEST 3: AI Meal Plan with USDA Validation")
    print("="*60)
    
    # Enable USDA validation
    os.environ['USDA_VALIDATION_ENABLED'] = 'true'
    
    service = OpenAIMealService()
    
    if not service.is_available():
        print("✗ OpenAI API not available")
        return
    
    user_data = {
        'body_weight': 175,
        'age': 25,
        'gender': 'male',
        'dietary_requirements': []
    }
    
    print(f"\nGenerating training day meal plan...")
    print(f"Target: {user_data['body_weight'] * 15 + 500} calories")
    print("(This may take 15-30 seconds...)")
    
    start_time = time.time()
    
    try:
        result = service.generate_single_day_meal_plan(
            user_data=user_data,
            is_training_day=True
        )
        
        generation_time = time.time() - start_time
        print(f"\n✓ Generated in {generation_time:.1f}s")
        
        if 'day_plan' in result:
            day_plan = result['day_plan']
            meals = day_plan.get('meals', [])
            
            # Check for USDA validation
            usda_verified_count = 0
            total_ingredients = 0
            corrections_made = 0
            
            print(f"\nValidation Results:")
            print("-" * 40)
            
            for meal in meals:
                print(f"\n{meal.get('name', 'Meal')}:")
                
                for ingredient in meal.get('ingredients', []):
                    total_ingredients += 1
                    name = ingredient.get('name', 'Unknown')
                    verified = ingredient.get('usda_verified', False)
                    
                    if verified:
                        usda_verified_count += 1
                        status = "✓ USDA Verified"
                        
                        # Check if values were corrected
                        if 'usda_fdc_id' in ingredient:
                            status += f" (FDC ID: {ingredient['usda_fdc_id']})"
                    else:
                        status = "✗ Not verified"
                    
                    print(f"  - {name}: {status}")
            
            # Summary
            print(f"\n" + "="*40)
            print(f"Validation Summary:")
            print(f"  Total ingredients: {total_ingredients}")
            print(f"  USDA verified: {usda_verified_count} ({usda_verified_count/total_ingredients*100:.0f}%)")
            
            # Save the validated meal plan
            filename = 'usda_validated_meal_plan.json'
            with open(filename, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"\n💾 Saved validated meal plan to: {filename}")
            
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()


def test_common_foods_cache():
    """Test pre-caching of common foods"""
    print("\n" + "="*60)
    print("TEST 4: Pre-cache Common Foods")
    print("="*60)
    
    usda = USDAFoodDataService()
    
    print("\nPre-caching common Kinobody foods...")
    print("(This helps with rate limiting and performance)")
    
    # Pre-cache common foods
    cached_count = 0
    for food in usda.COMMON_FOODS[:5]:  # Test with first 5
        print(f"\nCaching: {food}")
        result = usda.search_and_match(food, 100, "g")
        
        if result and 'calculated_nutrition' in result:
            nutrition = result['calculated_nutrition']
            print(f"  ✓ Cached - {nutrition.get('calories', 0)} cal per 100g")
            cached_count += 1
        else:
            print(f"  ✗ Failed to cache")
    
    print(f"\n✓ Successfully cached {cached_count} foods")


def main():
    """Run all USDA integration tests"""
    print("\n🚀 USDA FoodData Central Integration Tests")
    print("Testing fact-checked nutritional data integration")
    
    # Run tests in sequence
    test_usda_search()
    test_nutrient_extraction()
    test_common_foods_cache()
    test_meal_plan_validation()
    
    print("\n" + "="*60)
    print("✅ All tests completed!")
    print("="*60)


if __name__ == "__main__":
    main()