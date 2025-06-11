#!/usr/bin/env python3
"""
Demonstration of AI Meal Generation for Kinobody Program
Shows real recipes with accurate nutritional data
"""
import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from services.openai_meal_service import OpenAIMealService

load_dotenv()


def display_meal_plan(result):
    """Display meal plan in a formatted way"""
    if 'day_plan' not in result:
        print("No meal plan data found")
        return
    
    day_plan = result['day_plan']
    targets = day_plan.get('total_targets', {})
    meals = day_plan.get('meals', [])
    
    print(f"\n{'='*60}")
    print(f"KINOBODY {day_plan.get('day_type', '').upper()} MEAL PLAN")
    print(f"{'='*60}")
    
    print(f"\n📊 Daily Nutritional Targets:")
    print(f"   Calories: {targets.get('calories', 0)}")
    print(f"   Protein:  {targets.get('protein_g', 0)}g")
    print(f"   Carbs:    {targets.get('carbs_g', 0)}g")
    print(f"   Fats:     {targets.get('fats_g', 0)}g")
    
    # Calculate actual totals
    totals = {'calories': 0, 'protein_g': 0, 'carbs_g': 0, 'fats_g': 0}
    
    print(f"\n🍽️  Meal Schedule (Intermittent Fasting 12pm-8pm):")
    print(f"{'='*60}")
    
    for meal in meals:
        print(f"\n⏰ {meal.get('time', '')} - {meal.get('name', 'Meal')}")
        print(f"   {meal.get('calories', 0)} cal | P: {meal.get('protein_g', 0)}g | C: {meal.get('carbs_g', 0)}g | F: {meal.get('fats_g', 0)}g")
        
        # Update totals
        for key in totals:
            totals[key] += meal.get(key, 0)
        
        # Show ingredients
        ingredients = meal.get('ingredients', [])
        if ingredients:
            print(f"\n   Ingredients:")
            for ing in ingredients[:5]:  # Show first 5 ingredients
                print(f"   • {ing.get('amount', '')}{ing.get('unit', '')} {ing.get('name', '')}")
                if 'calories' in ing:
                    print(f"     ({ing['calories']} cal, {ing.get('protein_g', 0)}g P, {ing.get('carbs_g', 0)}g C, {ing.get('fats_g', 0)}g F)")
    
    # Validation
    print(f"\n{'='*60}")
    print(f"📈 Accuracy Check:")
    all_accurate = True
    for macro in ['calories', 'protein_g', 'carbs_g', 'fats_g']:
        target = targets.get(macro, 1)
        actual = totals[macro]
        accuracy = (actual / target * 100) if target > 0 else 0
        status = "✓" if abs(100 - accuracy) <= 5 else "✗"
        print(f"   {status} {macro}: {actual} / {target} ({accuracy:.1f}%)")
        if abs(100 - accuracy) > 5:
            all_accurate = False
    
    print(f"\n{'✅ PASS' if all_accurate else '⚠️  NEEDS ADJUSTMENT'}: Overall nutritional accuracy")


def main():
    print("🚀 Kinobody AI Meal Generation Demo")
    print("=" * 60)
    
    service = OpenAIMealService()
    
    if not service.is_available():
        print("❌ OpenAI API not available. Using demo data.")
    
    # Test profile
    user_data = {
        'body_weight': 175,
        'age': 25,
        'gender': 'male',
        'dietary_requirements': []
    }
    
    print(f"\n👤 User Profile:")
    print(f"   Body weight: {user_data['body_weight']} lbs")
    print(f"   Daily maintenance: {user_data['body_weight'] * 15} calories")
    
    # Generate training day meal plan
    print(f"\n⚡ Generating AI-Powered Training Day Meal Plan...")
    print("   (This uses real-time AI to create personalized meals)")
    
    try:
        result = service.generate_single_day_meal_plan(
            user_data=user_data,
            is_training_day=True
        )
        
        # Save the result
        with open('ai_meal_plan_demo.json', 'w') as f:
            json.dump(result, f, indent=2)
        
        # Display the meal plan
        display_meal_plan(result)
        
        print(f"\n💾 Full meal plan saved to: ai_meal_plan_demo.json")
        
        # Test rest day too
        print(f"\n\n{'='*60}")
        print("Generating Rest Day Meal Plan...")
        
        rest_result = service.generate_single_day_meal_plan(
            user_data=user_data,
            is_training_day=False
        )
        
        if 'day_plan' in rest_result:
            rest_targets = rest_result['day_plan'].get('total_targets', {})
            print(f"\n🌙 Rest Day Targets:")
            print(f"   Calories: {rest_targets.get('calories', 0)} (maintenance + 100)")
            print(f"   Protein:  {rest_targets.get('protein_g', 0)}g")
            
            with open('ai_meal_plan_rest.json', 'w') as f:
                json.dump(rest_result, f, indent=2)
            print(f"   💾 Saved to: ai_meal_plan_rest.json")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\nUsing demo meal plan instead...")
        
        # Show demo plan
        demo_result = service._get_demo_single_day_plan(user_data, True)
        display_meal_plan(demo_result)


if __name__ == "__main__":
    main()