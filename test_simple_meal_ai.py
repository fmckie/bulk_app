#!/usr/bin/env python3
"""
Simple test for meal generation
"""
import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

def test_simple():
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    prompt = """Create a simple meal plan for 1 day with these exact macros:
    - Calories: 3125
    - Protein: 175g
    - Carbs: 411g
    - Fats: 87g
    
    Return a JSON object with this structure:
    {
        "meals": [
            {
                "name": "Meal 1",
                "time": "12:00 PM",
                "calories": 937,
                "protein_g": 53,
                "carbs_g": 123,
                "fats_g": 26
            }
        ]
    }
    
    Include exactly 3 meals that sum to the daily targets."""
    
    try:
        print("Sending request to OpenAI...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a nutrition expert. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1000,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        print("\nResponse received!")
        print(json.dumps(result, indent=2))
        
        # Validate totals
        totals = {'calories': 0, 'protein_g': 0, 'carbs_g': 0, 'fats_g': 0}
        for meal in result.get('meals', []):
            for key in totals:
                totals[key] += meal.get(key, 0)
        
        print("\nTotals:")
        for key, value in totals.items():
            print(f"  {key}: {value}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_simple()