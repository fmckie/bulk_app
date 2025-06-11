#!/usr/bin/env python3
"""
Debug USDA API responses to understand data structure
"""
import os
import sys
import json
import requests
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

API_KEY = os.getenv('USDA_API_KEY', 'Y8QYvY3Dci7cARGZGxa9Fzy8edTz9BD2V2Iyu5QB')
BASE_URL = "https://api.nal.usda.gov/fdc/v1"


def test_search_and_detail():
    """Test search and then get detailed food data"""
    
    # 1. Search for chicken breast
    search_url = f"{BASE_URL}/foods/search"
    params = {
        'query': 'chicken breast cooked',
        'pageSize': 2,
        'dataType': 'Foundation,SR Legacy'
    }
    headers = {'X-Api-Key': API_KEY}
    
    print("1. Searching for 'chicken breast cooked'...")
    response = requests.get(search_url, params=params, headers=headers)
    search_data = response.json()
    
    print(f"\nSearch returned {len(search_data.get('foods', []))} results")
    
    if search_data.get('foods'):
        first_food = search_data['foods'][0]
        print(f"\nFirst result:")
        print(f"  Description: {first_food.get('description', 'N/A')}")
        print(f"  FDC ID: {first_food.get('fdcId', 'N/A')}")
        print(f"  Data Type: {first_food.get('dataType', 'N/A')}")
        
        # Save search response
        with open('usda_search_response.json', 'w') as f:
            json.dump(search_data, f, indent=2)
        print("\n💾 Saved search response to: usda_search_response.json")
        
        # 2. Get detailed food data
        fdc_id = first_food.get('fdcId')
        if fdc_id:
            print(f"\n2. Getting detailed data for FDC ID: {fdc_id}")
            
            detail_url = f"{BASE_URL}/food/{fdc_id}"
            # Request specific nutrients
            detail_params = {
                'nutrients': '208,203,205,204'  # Energy, Protein, Carbs, Fat
            }
            
            detail_response = requests.get(detail_url, params=detail_params, headers=headers)
            detail_data = detail_response.json()
            
            print(f"\nDetailed food data:")
            print(f"  Description: {detail_data.get('description', 'N/A')}")
            
            # Check for nutrients
            if 'foodNutrients' in detail_data:
                print(f"  Found {len(detail_data['foodNutrients'])} nutrients")
                
                # Show first few nutrients
                for i, nutrient in enumerate(detail_data['foodNutrients'][:5]):
                    print(f"\n  Nutrient {i+1}:")
                    print(f"    Structure: {list(nutrient.keys())}")
                    if 'nutrient' in nutrient:
                        print(f"    Nutrient info: {nutrient['nutrient']}")
                    print(f"    Amount: {nutrient.get('amount', 'N/A')}")
            
            # Save detailed response
            with open('usda_detail_response.json', 'w') as f:
                json.dump(detail_data, f, indent=2)
            print("\n💾 Saved detailed response to: usda_detail_response.json")


def test_better_search():
    """Try different search terms to find better matches"""
    
    search_terms = [
        "chicken, breast, meat only, cooked",
        "Chicken, broilers or fryers, breast, meat only, cooked",
        "chicken breast",
        "rice white cooked",
        "Rice, white, long-grain, regular, cooked"
    ]
    
    print("\nTesting different search terms...")
    print("="*60)
    
    for term in search_terms:
        search_url = f"{BASE_URL}/foods/search"
        params = {
            'query': term,
            'pageSize': 1,
            'dataType': 'Foundation,SR Legacy'
        }
        headers = {'X-Api-Key': API_KEY}
        
        response = requests.get(search_url, params=params, headers=headers)
        data = response.json()
        
        print(f"\nSearch: '{term}'")
        if data.get('foods'):
            food = data['foods'][0]
            print(f"  ✓ Found: {food.get('description', 'N/A')}")
            print(f"    Type: {food.get('dataType', 'N/A')}")
            print(f"    ID: {food.get('fdcId', 'N/A')}")
        else:
            print("  ✗ No results")


if __name__ == "__main__":
    print("🔍 USDA API Debug Script")
    print("="*60)
    
    test_search_and_detail()
    test_better_search()
    
    print("\n✅ Debug complete! Check the JSON files for full responses.")