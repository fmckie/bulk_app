#!/usr/bin/env python3
import os
import time
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

prompt = """Return this exact JSON for a meal plan:
{
    "day_plan": {
        "date": "2024-01-15",
        "day_type": "training day",
        "total_targets": {"calories": 3125, "protein_g": 175, "carbs_g": 411, "fats_g": 87},
        "meals": [
            {
                "meal_number": 1,
                "time": "12:00 PM",
                "name": "Chicken Rice Bowl",
                "calories": 937,
                "protein_g": 53,
                "carbs_g": 123,
                "fats_g": 26,
                "ingredients": [
                    {"name": "chicken", "amount": 200, "unit": "g", "calories": 330, "protein_g": 62, "carbs_g": 0, "fats_g": 7}
                ],
                "instructions": ["Cook and eat"]
            }
        ],
        "daily_totals": {"calories": 937, "protein_g": 53, "carbs_g": 123, "fats_g": 26}
    }
}"""

print("Sending...")
start = time.time()

response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": prompt}],
    temperature=0,
    max_tokens=1000
)

print(f"Response in {time.time()-start:.1f}s")
print(response.choices[0].message.content[:200])