#!/usr/bin/env python3
"""
Direct test of meal generation
"""
import os
import json
import time
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

def test_direct():
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    prompt = """Create a single day meal plan with these exact targets:
Calories: 3125 | Protein: 175g | Carbs: 411g | Fats: 87g

Create 3 meals:
1. 12:00 PM - First meal (~937 cal)
2. 4:30 PM - Second meal (~1094 cal)
3. 7:30 PM - Third meal (~1094 cal)

For each meal provide:
- Name
- Calories, protein, carbs, fats
- Main ingredients with amounts

Make sure the 3 meals sum exactly to the daily targets."""
    
    try:
        print("Sending request...")
        start = time.time()
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a nutrition expert. Be precise with numbers."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1500
        )
        
        elapsed = time.time() - start
        print(f"Response received in {elapsed:.1f} seconds")
        
        content = response.choices[0].message.content
        print("\nResponse:")
        print(content)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_direct()