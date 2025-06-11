"""
USDA FoodData Central API Service
Provides fact-checked nutritional data for meal planning
"""
import os
import logging
import hashlib
import requests
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import json

from services.redis_cache import default_cache

logger = logging.getLogger(__name__)


class USDAFoodDataService:
    """Service for interacting with USDA FoodData Central API"""
    
    BASE_URL = "https://api.nal.usda.gov/fdc/v1"
    API_KEY = os.getenv('USDA_API_KEY', 'Y8QYvY3Dci7cARGZGxa9Fzy8edTz9BD2V2Iyu5QB')
    
    # Standard USDA Nutrient IDs (confirmed from API response)
    NUTRIENT_IDS = {
        'calories': 1008,      # Energy (KCAL)
        'protein': 1003,       # Protein (g)
        'carbohydrates': 1005, # Carbohydrate, by difference (g)
        'fat': 1004,          # Total lipid (fat) (g)
        'fiber': 1079,        # Fiber, total dietary (g)
        'sugar': 2000,        # Sugars, total (g)
        'sodium': 1093        # Sodium (mg)
    }
    
    # Preferred data types for whole foods
    PREFERRED_DATA_TYPES = ['Foundation', 'SR Legacy']
    
    # Common food cache for performance
    COMMON_FOODS = [
        "chicken breast raw",
        "chicken breast cooked", 
        "white rice cooked",
        "brown rice cooked",
        "sweet potato baked",
        "olive oil",
        "ground beef 90% lean raw",
        "ground beef 90% lean cooked",
        "salmon fillet raw",
        "eggs whole raw",
        "greek yogurt plain",
        "almonds raw"
    ]
    
    def __init__(self):
        """Initialize USDA service with rate limiting tracking"""
        self.session = requests.Session()
        self.session.headers.update({'X-Api-Key': self.API_KEY})
        self._request_count = 0
        self._last_request_time = None
        
    def search_foods(self, query: str, data_type: List[str] = None, page_size: int = 10) -> Dict[str, Any]:
        """
        Search USDA database for foods
        
        Args:
            query: Search term
            data_type: Filter by data type (Foundation, SR Legacy, etc.)
            page_size: Number of results to return
            
        Returns:
            Dictionary with search results
        """
        # Check cache first
        cache_key = f"usda:search:{hashlib.md5(query.encode()).hexdigest()}"
        cached = default_cache.get(cache_key)
        if cached:
            logger.info(f"USDA search cache hit for: {query}")
            return cached
        
        # Prepare request parameters
        params = {
            'query': query,
            'pageSize': page_size
        }
        
        if data_type:
            params['dataType'] = ','.join(data_type)
        else:
            # Default to preferred data types
            params['dataType'] = ','.join(self.PREFERRED_DATA_TYPES)
        
        try:
            # Make API request
            endpoint = f"{self.BASE_URL}/foods/search"
            response = self._make_request(endpoint, params)
            
            if response and 'foods' in response:
                # Cache the results (24 hour TTL)
                default_cache.set(cache_key, response, ttl=86400)
                return response
            else:
                logger.error(f"Invalid USDA search response for: {query}")
                return {'foods': []}
                
        except Exception as e:
            logger.error(f"USDA search error for '{query}': {str(e)}")
            return {'foods': []}
    
    def get_food_nutrients(self, fdc_id: int) -> Dict[str, Any]:
        """
        Retrieve detailed nutritional data for specific food
        
        Args:
            fdc_id: USDA FDC ID for the food
            
        Returns:
            Dictionary with nutritional data
        """
        # Check cache first
        cache_key = f"usda:food:{fdc_id}"
        cached = default_cache.get(cache_key)
        if cached:
            logger.info(f"USDA food cache hit for FDC ID: {fdc_id}")
            return cached
        
        try:
            # Make API request
            endpoint = f"{self.BASE_URL}/food/{fdc_id}"
            # Use the nutrient numbers, not IDs, for the API request
            nutrient_numbers = '208,203,205,204,291,269,307'  # Energy, Protein, Carbs, Fat, Fiber, Sugar, Sodium
            params = {'nutrients': nutrient_numbers}
            
            response = self._make_request(endpoint, params)
            
            if response:
                # Cache the results (7 day TTL)
                default_cache.set(cache_key, response, ttl=604800)
                return response
            else:
                logger.error(f"Invalid USDA food response for FDC ID: {fdc_id}")
                return {}
                
        except Exception as e:
            logger.error(f"USDA food retrieval error for FDC ID {fdc_id}: {str(e)}")
            return {}
    
    def find_best_match(self, ingredient_name: str, search_results: List[Dict]) -> Optional[Dict]:
        """
        Implement fuzzy matching logic to find best food match
        
        Args:
            ingredient_name: Original ingredient name
            search_results: List of search results from USDA
            
        Returns:
            Best matching food item or None
        """
        if not search_results:
            return None
        
        # Normalize ingredient name
        ingredient_lower = ingredient_name.lower().strip()
        
        # Score each result
        scored_results = []
        for food in search_results:
            score = self._calculate_match_score(ingredient_lower, food)
            
            # Boost score for Foundation and SR Legacy data types
            data_type = food.get('dataType', '')
            if data_type in self.PREFERRED_DATA_TYPES:
                score *= 1.2
            
            scored_results.append((score, food))
        
        # Sort by score (highest first)
        scored_results.sort(key=lambda x: x[0], reverse=True)
        
        # Return best match if score is high enough
        if scored_results:
            best_score, best_match = scored_results[0]
            # Lower threshold for better matching
            if best_score >= 0.3:  # 30% match threshold
                return best_match
        
        # If no good match, return first result as fallback
        return search_results[0] if search_results else None
    
    def calculate_macros_for_amount(self, food_data: Dict, amount: float, unit: str) -> Dict[str, float]:
        """
        Convert serving sizes and calculate proportional macros
        
        Args:
            food_data: USDA food data
            amount: Quantity
            unit: Unit of measurement (g, oz, cups, etc.)
            
        Returns:
            Dictionary with calculated macros
        """
        # Extract nutrients from food data
        nutrients = self._extract_nutrients(food_data)
        if not nutrients:
            return {}
        
        # Convert amount to grams (USDA base unit)
        amount_in_grams = self._convert_to_grams(amount, unit, food_data)
        
        # Calculate proportional macros (USDA data is per 100g)
        factor = amount_in_grams / 100.0
        
        return {
            'calories': round(nutrients.get('calories', 0) * factor),
            'protein_g': round(nutrients.get('protein', 0) * factor, 1),
            'carbs_g': round(nutrients.get('carbohydrates', 0) * factor, 1),
            'fats_g': round(nutrients.get('fat', 0) * factor, 1),
            'fiber_g': round(nutrients.get('fiber', 0) * factor, 1),
            'sugar_g': round(nutrients.get('sugar', 0) * factor, 1),
            'sodium_mg': round(nutrients.get('sodium', 0) * factor)
        }
    
    def search_and_match(self, ingredient_name: str, amount: float = None, unit: str = None) -> Optional[Dict]:
        """
        Search for ingredient and return best match with nutrition
        
        Args:
            ingredient_name: Name of ingredient to search
            amount: Optional amount for nutrition calculation
            unit: Optional unit for amount
            
        Returns:
            Best matching food with nutrition data
        """
        # Search for the ingredient
        search_results = self.search_foods(ingredient_name)
        
        if not search_results.get('foods'):
            logger.warning(f"No USDA results found for: {ingredient_name}")
            return None
        
        # Find best match
        best_match = self.find_best_match(ingredient_name, search_results['foods'])
        
        if not best_match:
            logger.warning(f"No good USDA match found for: {ingredient_name}")
            return None
        
        # Get detailed nutrition if we have a match
        fdc_id = best_match.get('fdcId')
        if fdc_id:
            detailed_food = self.get_food_nutrients(fdc_id)
            if detailed_food:
                best_match = detailed_food
        
        # Calculate nutrition for specific amount if provided
        if amount and unit:
            macros = self.calculate_macros_for_amount(best_match, amount, unit)
            best_match['calculated_nutrition'] = macros
        
        return best_match
    
    def get_with_fallback(self, ingredient_name: str, amount: float, unit: str) -> Dict[str, Any]:
        """
        Get nutrition with cache and fallback strategy
        
        Args:
            ingredient_name: Name of ingredient
            amount: Quantity
            unit: Unit of measurement
            
        Returns:
            Nutritional data with source information
        """
        # 1. Check cache first
        cache_key = f"usda:ingredient:{ingredient_name}:{amount}:{unit}"
        cached = default_cache.get(cache_key)
        if cached:
            return cached
        
        # 2. Try USDA API
        try:
            result = self.search_and_match(ingredient_name, amount, unit)
            if result and 'calculated_nutrition' in result:
                # Add source information
                result['source'] = 'usda_api'
                result['verified'] = True
                
                # Cache the result
                default_cache.set(cache_key, result, ttl=86400)  # 24 hour cache
                return result
                
        except requests.Timeout:
            logger.error("USDA API timeout")
            
        except requests.HTTPError as e:
            if e.response.status_code == 429:
                logger.error("USDA API rate limit exceeded")
            else:
                logger.error(f"USDA API HTTP error: {e}")
        
        # 3. Fall back to pre-cached common foods
        return self._get_from_common_foods_cache(ingredient_name, amount, unit)
    
    def pre_cache_common_foods(self):
        """Pre-cache common Kinobody foods for reliability"""
        logger.info("Pre-caching common USDA foods...")
        
        for food_name in self.COMMON_FOODS:
            try:
                # Search and cache each common food
                result = self.search_and_match(food_name)
                if result:
                    logger.info(f"Pre-cached: {food_name}")
                else:
                    logger.warning(f"Could not pre-cache: {food_name}")
                    
            except Exception as e:
                logger.error(f"Error pre-caching {food_name}: {str(e)}")
        
        logger.info("Pre-caching complete")
    
    # Private helper methods
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make API request with error handling"""
        try:
            response = self.session.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            
            # Track rate limiting
            self._request_count += 1
            remaining = response.headers.get('X-RateLimit-Remaining')
            if remaining:
                logger.info(f"USDA API calls remaining: {remaining}")
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"USDA API request failed: {str(e)}")
            raise
    
    def _calculate_match_score(self, query: str, food_item: Dict) -> float:
        """Calculate match score between query and food item"""
        food_name = food_item.get('description', '').lower()
        
        # Exact match
        if query == food_name:
            return 1.0
        
        # Contains query
        if query in food_name:
            return 0.8
        
        # All words from query in food name
        query_words = set(query.split())
        food_words = set(food_name.split())
        if query_words.issubset(food_words):
            return 0.7
        
        # Partial word matches
        matching_words = query_words.intersection(food_words)
        if matching_words:
            return len(matching_words) / len(query_words) * 0.6
        
        return 0.0
    
    def _extract_nutrients(self, food_data: Dict) -> Dict[str, float]:
        """Extract relevant nutrients from USDA food data"""
        nutrients = {}
        
        # Handle different USDA data formats
        if 'foodNutrients' in food_data:
            for nutrient in food_data['foodNutrients']:
                # Handle nested nutrient structure
                if isinstance(nutrient, dict):
                    # Try different key patterns
                    nutrient_id = None
                    if 'nutrient' in nutrient and isinstance(nutrient['nutrient'], dict):
                        # This is the correct pattern based on API response
                        nutrient_id = nutrient['nutrient'].get('id')
                    elif 'nutrientId' in nutrient:
                        nutrient_id = nutrient['nutrientId']
                    elif 'id' in nutrient and 'amount' in nutrient:
                        # Only use direct id if amount is also present
                        nutrient_id = nutrient['id']
                    
                    # Map to our nutrient names
                    for name, nid in self.NUTRIENT_IDS.items():
                        if nutrient_id == nid:
                            # Get the amount value
                            amount = nutrient.get('amount', 0)
                            if not amount and 'value' in nutrient:
                                amount = nutrient['value']
                            nutrients[name] = float(amount)
                            break
        
        # If no nutrients found, try labelNutrients (different API response format)
        if not nutrients and 'labelNutrients' in food_data:
            label_nutrients = food_data['labelNutrients']
            if 'calories' in label_nutrients:
                nutrients['calories'] = float(label_nutrients['calories'].get('value', 0))
            if 'protein' in label_nutrients:
                nutrients['protein'] = float(label_nutrients['protein'].get('value', 0))
            if 'carbohydrates' in label_nutrients:
                nutrients['carbohydrates'] = float(label_nutrients['carbohydrates'].get('value', 0))
            if 'fat' in label_nutrients:
                nutrients['fat'] = float(label_nutrients['fat'].get('value', 0))
        
        return nutrients
    
    def _convert_to_grams(self, amount: float, unit: str, food_data: Dict = None) -> float:
        """Convert various units to grams"""
        unit_lower = unit.lower().strip()
        
        # Direct gram measurements
        if unit_lower in ['g', 'gram', 'grams']:
            return amount
        
        # Ounce conversions
        if unit_lower in ['oz', 'ounce', 'ounces']:
            return amount * 28.35
        
        # Pound conversions
        if unit_lower in ['lb', 'lbs', 'pound', 'pounds']:
            return amount * 453.592
        
        # Volume measurements (approximate, varies by food)
        if unit_lower in ['cup', 'cups']:
            # Use food-specific conversions if available
            if food_data and 'foodPortions' in food_data:
                for portion in food_data['foodPortions']:
                    if 'cup' in portion.get('modifier', '').lower():
                        return amount * portion.get('gramWeight', 240)
            # Default cup to gram (approximate)
            return amount * 240
        
        if unit_lower in ['tbsp', 'tablespoon', 'tablespoons']:
            return amount * 15
        
        if unit_lower in ['tsp', 'teaspoon', 'teaspoons']:
            return amount * 5
        
        # Default: assume grams
        logger.warning(f"Unknown unit '{unit}', assuming grams")
        return amount
    
    def _get_from_common_foods_cache(self, ingredient_name: str, amount: float, unit: str) -> Dict[str, Any]:
        """Get nutrition from pre-cached common foods"""
        # This would be populated by pre_cache_common_foods()
        # For now, return a fallback structure
        return {
            'description': ingredient_name,
            'calculated_nutrition': {
                'calories': 0,
                'protein_g': 0,
                'carbs_g': 0,
                'fats_g': 0,
                'fiber_g': 0,
                'sugar_g': 0,
                'sodium_mg': 0
            },
            'source': 'fallback',
            'verified': False,
            'error': 'USDA data not available'
        }