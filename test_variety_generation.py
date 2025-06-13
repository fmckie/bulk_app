#!/usr/bin/env python3
"""
Test script to verify meal prep variety improvements
"""
import os
import json
from datetime import datetime
from services.openai_meal_service import OpenAIMealService
from services.redis_cache import default_cache

def test_variety_generation():
    """Test the enhanced variety in meal generation"""
    
    # Initialize service
    ai_service = OpenAIMealService()
    
    # Test user data
    test_user_id = "test-variety-user"
    user_data = {
        'user_id': test_user_id,
        'body_weight': 175,
        'age': 28,
        'gender': 'male',
        'dietary_requirements': [],
        'budget': 150,
        'training_days': ['Monday', 'Wednesday', 'Friday'],
        'preferences': {
            'favorite_ingredients': ['salmon', 'quinoa', 'sweet potato'],
            'avoided_ingredients': ['shellfish', 'pork']
        }
    }
    
    print("🔬 Testing Meal Prep Variety Generation")
    print("=" * 50)
    
    # Clear any existing recipe history for clean test
    cache_key = f'recent_recipes:{test_user_id}'
    default_cache.delete(cache_key)
    
    # Test 1: Generate first single day meal plan
    print("\n📅 Test 1: First Single Day Generation")
    print("-" * 30)
    
    # Force demo mode for testing
    meal_plan_1 = ai_service._get_demo_single_day_plan(user_data, is_training_day=True)
    
    if 'day_plan' in meal_plan_1:
        print("✅ Successfully generated first meal plan")
        print("\nMeals generated:")
        for meal in meal_plan_1['day_plan']['meals']:
            print(f"  - {meal['name']}")
    else:
        print("❌ Failed to generate meal plan")
        return
    
    # Test 2: Generate second single day meal plan
    print("\n📅 Test 2: Second Single Day Generation (should be different)")
    print("-" * 30)
    
    # Force demo mode for testing
    meal_plan_2 = ai_service._get_demo_single_day_plan(user_data, is_training_day=False)
    
    if 'day_plan' in meal_plan_2:
        print("✅ Successfully generated second meal plan")
        print("\nMeals generated:")
        for meal in meal_plan_2['day_plan']['meals']:
            print(f"  - {meal['name']}")
        
        # Check for variety
        recipes_1 = {meal['name'] for meal in meal_plan_1['day_plan']['meals']}
        recipes_2 = {meal['name'] for meal in meal_plan_2['day_plan']['meals']}
        
        overlap = recipes_1.intersection(recipes_2)
        if overlap:
            print(f"\n⚠️  Warning: Found repeated recipes: {overlap}")
        else:
            print("\n✅ Good variety: No repeated recipes between generations")
    
    # Test 3: Check recipe history tracking
    print("\n📊 Test 3: Recipe History Tracking")
    print("-" * 30)
    
    cached_recipes = default_cache.get(cache_key)
    if cached_recipes:
        print(f"✅ Recipe history tracked: {len(cached_recipes)} recipes saved")
        print("\nRecent recipes:")
        for recipe in cached_recipes[-5:]:
            print(f"  - {recipe}")
    else:
        print("❌ Recipe history not tracked")
    
    # Test 4: Check variety in proteins and carbs
    print("\n🥗 Test 4: Ingredient Variety Analysis")
    print("-" * 30)
    
    all_meals = []
    if 'day_plan' in meal_plan_1:
        all_meals.extend(meal_plan_1['day_plan']['meals'])
    if 'day_plan' in meal_plan_2:
        all_meals.extend(meal_plan_2['day_plan']['meals'])
    
    proteins = set()
    carbs = set()
    
    for meal in all_meals:
        # Simple extraction based on common patterns
        meal_name = meal['name'].lower()
        
        # Check for proteins
        protein_sources = ['chicken', 'beef', 'salmon', 'turkey', 'cod', 'tilapia', 'eggs', 'greek yogurt']
        for protein in protein_sources:
            if protein in meal_name:
                proteins.add(protein)
        
        # Check for carbs
        carb_sources = ['rice', 'quinoa', 'sweet potato', 'pasta', 'oats', 'potato']
        for carb in carb_sources:
            if carb in meal_name:
                carbs.add(carb)
    
    print(f"✅ Protein variety: {len(proteins)} different sources")
    print(f"   Sources found: {', '.join(proteins)}")
    print(f"\n✅ Carb variety: {len(carbs)} different sources")
    print(f"   Sources found: {', '.join(carbs)}")
    
    # Test 5: Check user preferences integration
    print("\n👤 Test 5: User Preferences Integration")
    print("-" * 30)
    
    favorite_found = False
    avoided_found = False
    
    for meal in all_meals:
        meal_text = json.dumps(meal).lower()
        
        # Check if favorites are included
        for fav in user_data['preferences']['favorite_ingredients']:
            if fav.lower() in meal_text:
                favorite_found = True
                print(f"✅ Found favorite ingredient '{fav}' in meals")
                break
        
        # Check if avoided ingredients are excluded
        for avoid in user_data['preferences']['avoided_ingredients']:
            if avoid.lower() in meal_text:
                avoided_found = True
                print(f"❌ Found avoided ingredient '{avoid}' in meals")
                break
    
    if not avoided_found:
        print("✅ Successfully avoided all restricted ingredients")
    
    print("\n" + "=" * 50)
    print("✅ Variety testing complete!")
    
    # Cleanup test data
    default_cache.delete(cache_key)
    default_cache.delete(f'generation_history:{test_user_id}')

if __name__ == "__main__":
    # Check if OpenAI API key is set
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        print("Using demo mode instead...")
    
    test_variety_generation()