#!/usr/bin/env python3
"""
Test OpenAI API connection
"""
import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

def test_connection():
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        print("❌ No API key found in environment")
        return
    
    print(f"✓ API key found: {api_key[:10]}...")
    
    try:
        client = OpenAI(api_key=api_key)
        
        # Simple test
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Say 'API working' in 3 words"}
            ],
            max_tokens=10
        )
        
        print(f"✓ API Response: {response.choices[0].message.content}")
        
    except Exception as e:
        print(f"❌ API Error: {str(e)}")

if __name__ == "__main__":
    test_connection()