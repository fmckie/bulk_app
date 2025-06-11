# USDA FoodData Central API Integration Plan

## Overview
This document outlines the comprehensive plan to integrate the USDA FoodData Central API into the Kinobody meal prep service to provide fact-checked, accurate nutritional data for all generated meal plans.

## API Credentials
- **API Key**: `Y8QYvY3Dci7cARGZGxa9Fzy8edTz9BD2V2Iyu5QB`
- **Base URL**: `https://api.nal.usda.gov/fdc/v1`
- **Rate Limit**: 1,000 requests per hour per IP address

## Implementation Plan

### Phase 1: Create USDA FoodData Service Module

#### File: `services/usda_fooddata_service.py`

```python
class USDAFoodDataService:
    """Service for interacting with USDA FoodData Central API"""
    
    BASE_URL = "https://api.nal.usda.gov/fdc/v1"
    API_KEY = "Y8QYvY3Dci7cARGZGxa9Fzy8edTz9BD2V2Iyu5QB"
    
    # Standard USDA Nutrient IDs
    NUTRIENT_IDS = {
        'calories': 208,      # Energy (KCAL)
        'protein': 203,       # Protein (g)
        'carbohydrates': 205, # Carbohydrate, by difference (g)
        'fat': 204,          # Total lipid (fat) (g)
        'fiber': 291,        # Fiber, total dietary (g)
        'sugar': 269,        # Sugars, total (g)
        'sodium': 307        # Sodium (mg)
    }
    
    # Preferred data types for whole foods
    PREFERRED_DATA_TYPES = ['Foundation', 'SR Legacy']
```

#### Core Methods to Implement:

1. **Food Search**
   ```python
   def search_foods(self, query: str, data_type: List[str] = None, page_size: int = 10) -> Dict
   ```
   - Search USDA database for foods
   - Filter by data type (prefer Foundation/SR Legacy for whole foods)
   - Handle pagination if needed

2. **Get Food Details**
   ```python
   def get_food_nutrients(self, fdc_id: int) -> Dict
   ```
   - Retrieve detailed nutritional data for specific food
   - Extract only needed nutrients using NUTRIENT_IDS

3. **Smart Food Matching**
   ```python
   def find_best_match(self, ingredient_name: str, search_results: List[Dict]) -> Dict
   ```
   - Implement fuzzy matching logic
   - Prioritize whole foods over branded
   - Consider preparation methods (raw, cooked, etc.)

4. **Macro Calculation**
   ```python
   def calculate_macros_for_amount(self, food_data: Dict, amount: float, unit: str) -> Dict
   ```
   - Convert serving sizes (g, oz, cups, etc.)
   - Calculate proportional macros
   - Return standardized macro dictionary

### Phase 2: Redis Caching Integration

#### Cache Strategy:
```python
# Cache keys format
CACHE_KEYS = {
    'food_search': 'usda:search:{query_hash}',     # TTL: 24 hours
    'food_details': 'usda:food:{fdc_id}',          # TTL: 7 days
    'common_foods': 'usda:common:{ingredient_key}'  # TTL: 30 days
}

# Pre-cache common Kinobody foods
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
```

### Phase 3: OpenAI Meal Service Integration

#### Update `services/openai_meal_service.py`:

1. **Import USDA Service**
   ```python
   from services.usda_fooddata_service import USDAFoodDataService
   from services.redis_cache import default_cache
   ```

2. **Enhanced System Prompt**
   ```python
   SYSTEM_PROMPT = """You are an expert nutritionist using USDA FoodData Central for accuracy.
   
   CRITICAL REQUIREMENTS:
   1. All nutritional values will be verified against USDA database
   2. Use specific food names that match USDA nomenclature:
      - Include preparation method: "raw", "cooked", "grilled", "baked"
      - Be specific: "chicken breast, boneless, skinless, raw"
      - Use standard units: grams (g), ounces (oz), cups
   
   3. Your macro calculations will be validated to ensure:
      - Calories = (Protein × 4) + (Carbs × 4) + (Fat × 9)
      - All values within 5% of USDA verified data
   
   4. Common USDA food names:
      - "Chicken, breast, meat only, raw"
      - "Rice, white, long-grain, regular, cooked"
      - "Sweet potato, cooked, baked in skin"
      - "Oil, olive, salad or cooking"
   """
   ```

3. **Validation Workflow**
   ```python
   def validate_with_usda(self, meal_plan: Dict) -> Dict:
       """Validate and correct meal plan with USDA data"""
       usda = USDAFoodDataService()
       validated_plan = deepcopy(meal_plan)
       
       for meal in validated_plan['day_plan']['meals']:
           verified_totals = {
               'calories': 0,
               'protein_g': 0,
               'carbs_g': 0,
               'fats_g': 0
           }
           
           for ingredient in meal['ingredients']:
               try:
                   # Search USDA database
                   usda_food = usda.search_and_match(
                       ingredient['name'],
                       amount=ingredient['amount'],
                       unit=ingredient['unit']
                   )
                   
                   # Get verified nutrition
                   verified_nutrition = usda.get_proportional_nutrition(
                       usda_food,
                       ingredient['amount'],
                       ingredient['unit']
                   )
                   
                   # Check variance
                   variance = self.calculate_variance(
                       ingredient,
                       verified_nutrition
                   )
                   
                   if variance > 0.10:  # 10% threshold
                       logger.info(f"Correcting {ingredient['name']}: "
                                 f"{variance:.1%} variance")
                       ingredient.update(verified_nutrition)
                   
                   # Add USDA reference
                   ingredient['usda_fdc_id'] = usda_food['fdcId']
                   ingredient['usda_verified'] = True
                   
               except Exception as e:
                   logger.warning(f"USDA validation failed for "
                                f"{ingredient['name']}: {str(e)}")
                   ingredient['usda_verified'] = False
               
               # Update totals
               for macro in verified_totals:
                   verified_totals[macro] += ingredient.get(macro, 0)
           
           # Update meal totals
           meal.update(verified_totals)
       
       return validated_plan
   ```

### Phase 4: Error Handling & Fallbacks

```python
class USDAFoodDataService:
    def get_with_fallback(self, ingredient_name: str, amount: float, unit: str):
        """Get nutrition with cache and fallback strategy"""
        
        # 1. Check cache first
        cache_key = f"usda:ingredient:{ingredient_name}:{amount}:{unit}"
        cached = default_cache.get(cache_key)
        if cached:
            return cached
        
        # 2. Try USDA API
        try:
            result = self.search_and_get_nutrition(ingredient_name, amount, unit)
            default_cache.set(cache_key, result, ttl=86400)  # 24 hour cache
            return result
            
        except requests.Timeout:
            logger.error("USDA API timeout")
            
        except requests.HTTPError as e:
            if e.response.status_code == 429:
                logger.error("USDA API rate limit exceeded")
            
        # 3. Fall back to pre-cached common foods
        return self.get_from_common_foods_cache(ingredient_name, amount, unit)
```

### Phase 5: Testing Strategy

#### File: `tests/test_usda_integration.py`

1. **Unit Tests**
   - Test USDA API connection
   - Test food search functionality
   - Test nutrient extraction
   - Test unit conversions
   - Test caching behavior

2. **Integration Tests**
   - Test full meal plan validation
   - Test error handling and fallbacks
   - Test rate limit compliance
   - Compare AI vs USDA accuracy

3. **Accuracy Validation Tests**
   ```python
   def test_common_foods_accuracy():
       """Validate common foods have accurate USDA data"""
       test_foods = [
           ("chicken breast raw", 100, "g", 
            {"calories": 165, "protein_g": 31, "carbs_g": 0, "fats_g": 3.6}),
           ("white rice cooked", 100, "g",
            {"calories": 130, "protein_g": 2.7, "carbs_g": 28, "fats_g": 0.3}),
           # ... more test cases
       ]
   ```

### Phase 6: Monitoring & Analytics

1. **Track API Usage**
   ```python
   # Log all USDA API calls
   logger.info(f"USDA API call: {endpoint}, remaining: {rate_limit_remaining}")
   ```

2. **Accuracy Metrics**
   ```python
   # Track variance between AI and USDA
   metrics = {
       'total_validations': 0,
       'corrections_made': 0,
       'average_variance': 0,
       'foods_not_found': []
   }
   ```

3. **Performance Monitoring**
   - Cache hit rate
   - API response times
   - Validation processing time

## Implementation Timeline

### Week 1: Core Development
- [ ] Create USDAFoodDataService class
- [ ] Implement search and nutrient retrieval
- [ ] Set up Redis caching
- [ ] Write unit tests

### Week 2: Integration
- [ ] Integrate with OpenAI meal service
- [ ] Implement validation workflow
- [ ] Add error handling
- [ ] Create integration tests

### Week 3: Testing & Optimization
- [ ] Run accuracy validation tests
- [ ] Optimize caching strategy
- [ ] Performance testing
- [ ] Documentation

## Success Metrics

1. **Accuracy**: 95%+ of ingredients validated against USDA
2. **Performance**: <2 second additional processing time
3. **Reliability**: 99%+ uptime with fallback handling
4. **Cache Efficiency**: 80%+ cache hit rate for common foods

## Configuration

### Environment Variables
```bash
# .env file
USDA_API_KEY=Y8QYvY3Dci7cARGZGxa9Fzy8edTz9BD2V2Iyu5QB
USDA_API_BASE_URL=https://api.nal.usda.gov/fdc/v1
USDA_RATE_LIMIT=1000
USDA_CACHE_TTL=86400
```

### Feature Flags
```python
# Enable/disable USDA validation
FEATURES = {
    'usda_validation': True,
    'strict_validation': False,  # Fail if USDA data not found
    'log_corrections': True,
    'pre_cache_common': True
}
```

## Rollback Plan

If USDA integration causes issues:
1. Disable via feature flag
2. Fall back to AI-only generation
3. Maintain cached USDA data for future use
4. Log all issues for analysis

## Future Enhancements

1. **Expand Nutrient Tracking**
   - Add micronutrients (vitamins, minerals)
   - Track fiber, sugar, sodium
   - Calculate nutrient density scores

2. **Advanced Features**
   - Recipe nutrition calculator
   - Ingredient substitution suggestions
   - Seasonal food recommendations

3. **User Features**
   - Show USDA verification badge
   - Display nutrient sources
   - Provide food education

## Conclusion

This USDA FoodData Central integration will transform the Kinobody meal prep planner into a highly accurate, government-data-backed nutrition tool. By combining AI creativity with USDA accuracy, we'll deliver meal plans users can trust for their fitness goals.