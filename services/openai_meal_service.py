"""
OpenAI GPT-4 Mini Service for AI-powered meal planning
"""
import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from copy import deepcopy
import openai
from openai import OpenAI

from services.usda_fooddata_service import USDAFoodDataService
from services.redis_cache import default_cache
from database.recipe_storage_db import RecipeStorageDB

logger = logging.getLogger(__name__)


class OpenAIMealService:
    """Service for generating personalized meal plans using OpenAI GPT-4 Mini"""
    
    def __init__(self):
        """Initialize OpenAI client with API key from environment"""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            logger.warning("OpenAI API key not found. AI features will be disabled.")
            self.client = None
        else:
            self.client = OpenAI(api_key=api_key)
            self.model = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')  # Using 3.5 for faster response
        
        # Initialize USDA service for nutrition validation
        self.usda_service = USDAFoodDataService()
    
    def is_available(self) -> bool:
        """Check if OpenAI service is available"""
        return self.client is not None
    
    def generate_single_day_meal_plan(self, user_data: Dict[str, Any], day_date: str = None, is_training_day: bool = True) -> Dict[str, Any]:
        """
        Generate a single day meal plan with exact nutritional targets
        
        Args:
            user_data: Dictionary containing user profile and preferences
            day_date: Specific date for the meal plan (optional)
            is_training_day: Whether this is a training day or rest day
            
        Returns:
            Dictionary containing the single day meal plan
        """
        if not self.is_available():
            return self._get_demo_single_day_plan(user_data, is_training_day)
        
        try:
            # Calculate exact nutritional targets
            body_weight = user_data.get('body_weight', 175)
            maintenance_calories = body_weight * 15
            
            if is_training_day:
                total_calories = maintenance_calories + 500
                day_type = "training day"
            else:
                total_calories = maintenance_calories + 100
                day_type = "rest day"
            
            # Calculate macros
            protein_g = body_weight  # 1g per lb
            fats_calories = total_calories * 0.25
            fats_g = round(fats_calories / 9)
            protein_calories = protein_g * 4
            carbs_calories = total_calories - protein_calories - fats_calories
            carbs_g = round(carbs_calories / 4)
            
            # Get recent recipes to avoid repetition
            recent_recipes = self._get_recent_recipes(user_data.get('user_id'))
            
            # Track this generation request
            if 'user_id' in user_data:
                self._track_generation_request(user_data['user_id'])
            
            # Build optimized prompt for single day
            prompt = self._build_single_day_prompt(
                body_weight=body_weight,
                total_calories=round(total_calories),
                protein_g=protein_g,
                carbs_g=carbs_g,
                fats_g=fats_g,
                day_type=day_type,
                dietary_requirements=user_data.get('dietary_requirements', []),
                recent_recipes=recent_recipes
            )
            
            # Generate meal plan with AI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": """You are an expert nutritionist specializing in the Kinobody Greek God program and meal prep planning.
Your TOP priorities are:
1. Creating DIVERSE meal plans with MAXIMUM VARIETY - this is CRITICAL
2. Achieving EXACT nutritional accuracy using USDA FoodData Central values

Key principles:
1. VARIETY FIRST: Every meal must be unique with different proteins, carbs, and cooking methods
2. EXACT MACROS: Every meal plan must hit the exact calorie and macro targets provided (within 2% tolerance)
3. REAL RECIPES: Use only real, practical recipes with common ingredients
4. PRECISE MEASUREMENTS: Every ingredient must have exact measurements in grams or standard units
5. INTERMITTENT FASTING: All meals must fit within 12pm-8pm eating window
6. MEAL PREP FRIENDLY: Foods that store well for 3-5 days

CRITICAL VARIETY REQUIREMENTS:
- NEVER repeat the same protein source in one day
- NEVER use generic recipe names like "Chicken & Rice" or "Beef & Sweet Potato"
- Use specific, appetizing recipe names with cuisines/cooking methods
- Rotate through different cuisines: Mediterranean, Asian, Mexican, Italian, American
- Vary cooking methods: grilled, baked, stir-fried, slow-cooked, pan-seared
- Generate COMPLETELY DIFFERENT recipes from any previous suggestions
- Each meal must have a unique flavor profile and cooking style

RECIPE NAMING EXAMPLES:
- GOOD: "Mediterranean Herb-Crusted Salmon with Quinoa Tabbouleh"
- GOOD: "Thai Basil Beef Stir-Fry with Jasmine Rice"
- GOOD: "Mexican Chipotle Turkey Bowl with Cilantro Lime Rice"
- BAD: "Chicken with Rice"
- BAD: "Beef and Sweet Potato"

CRITICAL - Use USDA-verified nutritional values:
- ALL nutritional values will be validated against USDA FoodData Central
- Use specific USDA food names (e.g., "Chicken, breast, meat only, cooked, grilled")
- Include preparation method: "raw", "cooked", "grilled", "baked"
- Be specific: "chicken breast, boneless, skinless, cooked" not just "chicken"

Common USDA-verified values per 100g:
- Chicken breast, cooked: 165 cal, 31g protein, 0g carbs, 3.6g fat
- Chicken thighs, cooked: 209 cal, 26g protein, 0g carbs, 10.9g fat
- Ground beef 90% lean: 217 cal, 26g protein, 0g carbs, 12g fat
- Salmon, cooked: 206 cal, 22g protein, 0g carbs, 13g fat
- Rice, white, cooked: 130 cal, 2.7g protein, 28g carbs, 0.3g fat
- Quinoa, cooked: 120 cal, 4.1g protein, 21g carbs, 1.9g fat
- Sweet potato, baked: 90 cal, 2g protein, 21g carbs, 0.1g fat
- Oil, olive: 884 cal, 0g protein, 0g carbs, 100g fat

You must return ONLY valid JSON with exact nutritional breakdowns. No other text."""
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,  # Balanced temperature for variety while maintaining accuracy
                max_tokens=2500
                # Note: Removed response_format due to timeout issues
            )
            
            # Parse and validate the response
            response_content = response.choices[0].message.content
            
            # Strip markdown code blocks if present
            if response_content.startswith('```'):
                # Find the actual JSON content
                lines = response_content.split('\n')
                json_start = -1
                json_end = -1
                
                for i, line in enumerate(lines):
                    if line.startswith('```') and json_start == -1:
                        json_start = i + 1
                    elif line.startswith('```') and json_start != -1:
                        json_end = i
                        break
                
                if json_start != -1 and json_end != -1:
                    response_content = '\n'.join(lines[json_start:json_end])
            
            try:
                meal_plan_data = json.loads(response_content)
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {str(e)}")
                logger.error(f"Response content: {response_content[:500]}...")
                raise
            
            # Validate with USDA data if enabled
            if os.getenv('USDA_VALIDATION_ENABLED', 'true').lower() == 'true':
                meal_plan_data = self.validate_with_usda(meal_plan_data)
            
            # Save recipes to cache for variety tracking
            if 'user_id' in user_data:
                self._save_recipes_to_cache(user_data['user_id'], meal_plan_data)
            
            # Auto-save recipes to database
            if user_data.get('auto_save_recipes', True) and 'user_id' in user_data:
                self._save_recipes_to_database(user_data['user_id'], meal_plan_data, is_single_day=True)
            
            return meal_plan_data
            
        except Exception as e:
            logger.error(f"Error generating single day meal plan: {str(e)}")
            return self._get_demo_single_day_plan(user_data, is_training_day)
    
    def generate_meal_plan(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a complete 7-day meal plan based on user requirements
        
        Args:
            user_data: Dictionary containing user profile, requirements, and preferences
            
        Returns:
            Dictionary containing the generated meal plan
        """
        if not self.is_available():
            return self._get_demo_meal_plan(user_data)
        
        try:
            # Calculate nutritional targets
            body_weight = user_data.get('body_weight', 175)
            maintenance_calories = body_weight * 15
            training_days = user_data.get('training_days', ['Monday', 'Wednesday', 'Friday'])
            
            # Get user preferences to enhance variety
            preferences = user_data.get('preferences', {})
            favorite_ingredients = preferences.get('favorite_ingredients', [])
            avoided_ingredients = preferences.get('avoided_ingredients', [])
            
            # Get recent recipes to avoid repetition
            recent_recipes = self._get_recent_recipes(user_data.get('user_id'))
            
            # Track this generation request
            if 'user_id' in user_data:
                self._track_generation_request(user_data['user_id'])
            
            # Build the prompt with preferences
            prompt = self._build_meal_plan_prompt(user_data, maintenance_calories, training_days, recent_recipes)
            
            # Add preference information to prompt if available
            if favorite_ingredients or avoided_ingredients:
                prompt += f"\n\nUSER PREFERENCES:\n"
                if favorite_ingredients:
                    prompt += f"- Favorite ingredients to include: {', '.join(favorite_ingredients)}\n"
                if avoided_ingredients:
                    prompt += f"- Ingredients to avoid: {', '.join(avoided_ingredients)}\n"
            
            # Generate meal plan with AI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": """You are an expert nutritionist specializing in the Kinobody Greek God program and meal prep planning.
Your TOP priorities are:
1. Creating DIVERSE meal plans with MAXIMUM VARIETY - this is CRITICAL
2. Achieving EXACT nutritional accuracy using USDA FoodData Central values

Key principles:
1. VARIETY FIRST: Every meal must be unique with different proteins, carbs, and cooking methods
2. EXACT MACROS: Every meal plan must hit the exact calorie and macro targets provided (within 2% tolerance)
3. REAL RECIPES: Use only real, practical recipes with common ingredients
4. PRECISE MEASUREMENTS: Every ingredient must have exact measurements in grams or standard units
5. INTERMITTENT FASTING: All meals must fit within 12pm-8pm eating window
6. MEAL PREP FRIENDLY: Foods that store well for 3-5 days

CRITICAL VARIETY REQUIREMENTS:
- NEVER repeat the same protein source in one day
- NEVER use generic recipe names like "Chicken & Rice" or "Beef & Sweet Potato"
- Use specific, appetizing recipe names with cuisines/cooking methods
- Rotate through different cuisines: Mediterranean, Asian, Mexican, Italian, American
- Vary cooking methods: grilled, baked, stir-fried, slow-cooked, pan-seared
- Generate COMPLETELY DIFFERENT recipes from any previous suggestions
- Each meal must have a unique flavor profile and cooking style

RECIPE NAMING EXAMPLES:
- GOOD: "Mediterranean Herb-Crusted Salmon with Quinoa Tabbouleh"
- GOOD: "Thai Basil Beef Stir-Fry with Jasmine Rice"
- GOOD: "Mexican Chipotle Turkey Bowl with Cilantro Lime Rice"
- BAD: "Chicken with Rice"
- BAD: "Beef and Sweet Potato"

CRITICAL - Use USDA-verified nutritional values:
- ALL nutritional values will be validated against USDA FoodData Central
- Use specific USDA food names (e.g., "Chicken, breast, meat only, cooked, grilled")
- Include preparation method: "raw", "cooked", "grilled", "baked"
- Be specific: "chicken breast, boneless, skinless, cooked" not just "chicken"

Common USDA-verified values per 100g:
- Chicken breast, cooked: 165 cal, 31g protein, 0g carbs, 3.6g fat
- Chicken thighs, cooked: 209 cal, 26g protein, 0g carbs, 10.9g fat
- Ground beef 90% lean: 217 cal, 26g protein, 0g carbs, 12g fat
- Salmon, cooked: 206 cal, 22g protein, 0g carbs, 13g fat
- Rice, white, cooked: 130 cal, 2.7g protein, 28g carbs, 0.3g fat
- Quinoa, cooked: 120 cal, 4.1g protein, 21g carbs, 1.9g fat
- Sweet potato, baked: 90 cal, 2g protein, 21g carbs, 0.1g fat
- Oil, olive: 884 cal, 0g protein, 0g carbs, 100g fat

You must return ONLY valid JSON with exact nutritional breakdowns. No other text."""
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,  # Balanced temperature for variety while maintaining accuracy
                max_tokens=4000,
                response_format={"type": "json_object"}
            )
            
            # Parse the response
            meal_plan_data = json.loads(response.choices[0].message.content)
            
            # Validate and enhance the meal plan
            meal_plan = self._validate_and_enhance_meal_plan(meal_plan_data, user_data)
            
            # Auto-save all recipes to database
            if user_data.get('auto_save_recipes', True) and 'user_id' in user_data:
                generation_start = datetime.now()
                saved_recipe_ids = self._save_recipes_to_database(user_data['user_id'], meal_plan)
                generation_time_ms = int((datetime.now() - generation_start).total_seconds() * 1000)
                
                # Save generation history
                if saved_recipe_ids:
                    self._save_generation_history(user_data['user_id'], meal_plan, saved_recipe_ids, generation_time_ms)
            
            return meal_plan
            
        except Exception as e:
            logger.error(f"Error generating meal plan with AI: {str(e)}")
            # Fall back to demo meal plan
            return self._get_demo_meal_plan(user_data)
    
    def _build_single_day_prompt(self, body_weight: int, total_calories: int, 
                                          protein_g: int, carbs_g: int, fats_g: int, 
                                          day_type: str, dietary_requirements: List[str], 
                                          recent_recipes: List[str] = None) -> str:
        """Build optimized prompt for single day meal generation with variety"""
        
        restrictions = ', '.join(dietary_requirements) if dietary_requirements else 'None'
        
        # Format recent recipes to show only last 10 for context
        if recent_recipes and len(recent_recipes) > 0:
            # Take last 10 recipes
            recent_10 = recent_recipes[-10:] if len(recent_recipes) > 10 else recent_recipes
            recent_recipes_str = '\n'.join([f"- {recipe}" for recipe in recent_10])
        else:
            recent_recipes_str = 'None'
        
        # Add time-based variety seed
        current_time = datetime.now()
        variety_seed = f"{current_time.strftime('%Y-%m-%d %H:%M')}"
        
        return f"""Create 3 VARIED and DIVERSE meals for a {day_type} with EXACT macros:
Calories: {total_calories} | Protein: {protein_g}g | Carbs: {carbs_g}g | Fats: {fats_g}g

Schedule (Intermittent Fasting):
- Meal 1: 12:00 PM (~30% calories)
- Meal 2: 4:30 PM (~35% calories)  
- Meal 3: 7:30 PM (~35% calories)

Dietary restrictions: {restrictions}
Generation Time: {variety_seed}

CRITICAL VARIETY REQUIREMENTS:
1. Use DIFFERENT protein sources in each meal (vary between: chicken breast, chicken thighs, ground beef, steak, salmon, white fish, turkey, eggs, greek yogurt)
2. Use DIFFERENT carb sources in each meal (vary between: white rice, brown rice, quinoa, sweet potato, white potato, pasta, oats, ezekiel bread)
3. Use DIFFERENT cooking methods (grilled, baked, pan-seared, stir-fried, slow-cooked, roasted)
4. Include DIFFERENT vegetables and flavors in each meal
5. Be CREATIVE and UNIQUE based on the current time/date

RECIPES TO AVOID (recently generated):
{recent_recipes_str}

IMPORTANT: Do NOT repeat any of the above recipes or use similar names. Create COMPLETELY NEW recipes.

RECIPE INSPIRATION (choose different styles for variety):
- Mediterranean: Greek chicken with quinoa and tzatziki
- Asian: Teriyaki salmon with jasmine rice and stir-fried vegetables  
- Mexican: Beef burrito bowl with cilantro lime rice
- American: BBQ turkey meatballs with sweet potato wedges
- Italian: Baked cod with roasted vegetables and garlic pasta
- Power Bowls: Protein + grain + vegetables + healthy fat sauce

Return JSON:
{{
    "day_plan": {{
        "date": "2024-01-15",
        "day_type": "{day_type}",
        "total_targets": {{"calories": {total_calories}, "protein_g": {protein_g}, "carbs_g": {carbs_g}, "fats_g": {fats_g}}},
        "meals": [
            {{
                "meal_number": 1,
                "time": "12:00 PM",
                "name": "UNIQUE Recipe Name (NO generic names like 'Chicken & Rice')",
                "calories": exact_number,
                "protein_g": exact_number,
                "carbs_g": exact_number,
                "fats_g": exact_number,
                "ingredients": [
                    {{"name": "specific ingredient", "amount": exact_grams, "unit": "g", "calories": X, "protein_g": X, "carbs_g": X, "fats_g": X}}
                ],
                "instructions": ["Specific step 1", "Specific step 2"]
            }},
            // ... meal 2 and 3 with DIFFERENT proteins and carbs
        ],
        "daily_totals": {{"calories": sum, "protein_g": sum, "carbs_g": sum, "fats_g": sum}}
    }}
}}

CRITICAL: 
- Sum of 3 meals MUST equal targets within 2%
- Each meal MUST use different protein and carb sources
- Recipe names must be specific and appetizing (not generic)

Common food macros per 100g:
- Chicken breast (cooked): 165cal, 31g protein, 0g carbs, 3.6g fat
- Chicken thighs (cooked): 209cal, 26g protein, 0g carbs, 10.9g fat
- Ground beef 90% lean: 217cal, 26g protein, 0g carbs, 12g fat
- Salmon (cooked): 206cal, 22g protein, 0g carbs, 13g fat
- White rice (cooked): 130cal, 2.7g protein, 28g carbs, 0.3g fat
- Quinoa (cooked): 120cal, 4.1g protein, 21g carbs, 1.9g fat
- Sweet potato (baked): 90cal, 2g protein, 21g carbs, 0.1g fat
- Olive oil: 884cal, 0g protein, 0g carbs, 100g fat"""
    
    def _build_meal_plan_prompt(self, user_data: Dict, maintenance_calories: int, training_days: List[str], recent_recipes: List[str] = None) -> str:
        """Build detailed prompt for meal plan generation with enhanced variety"""
        dietary_requirements = user_data.get('dietary_requirements', [])
        budget = user_data.get('budget', 150)
        
        # Format recent recipes
        if recent_recipes and len(recent_recipes) > 0:
            recent_recipes_str = '\n'.join([f"- {recipe}" for recipe in recent_recipes])
        else:
            recent_recipes_str = 'None'
        
        # Add time-based variety seed
        current_time = datetime.now()
        variety_seed = f"{current_time.strftime('%Y-%m-%d %H:%M')}"
        
        prompt = f"""Create a DIVERSE 7-day meal prep plan with MAXIMUM VARIETY:

USER PROFILE:
- Body weight: {user_data.get('body_weight', 175)} lbs
- Age: {user_data.get('age', 25)} years
- Gender: {user_data.get('gender', 'male')}
- Fitness goal: Build muscle while staying lean (Greek God physique)
- Training days: {', '.join(training_days)}

NUTRITIONAL REQUIREMENTS:
- Maintenance calories: {maintenance_calories} cal/day
- Training days: {maintenance_calories + 500} calories (+500 surplus)
- Rest days: {maintenance_calories + 100} calories (+100 surplus)
- Protein target: {user_data.get('body_weight', 175)}g daily (1g per lb body weight)
- Fats: 25% of total calories
- Carbs: Fill remaining calories
- Follow intermittent fasting (eating window: 12pm-8pm)

DIETARY RESTRICTIONS:
{', '.join(dietary_requirements) if dietary_requirements else 'None'}

VARIETY REQUIREMENTS (CRITICAL):
1. Use AT LEAST 5 different protein sources across the week:
   - Chicken breast, chicken thighs, ground beef, steak, ground turkey
   - Salmon, white fish (cod/tilapia), eggs, greek yogurt
2. Use AT LEAST 5 different carb sources across the week:
   - White rice, brown rice, quinoa, sweet potato, white potato
   - Pasta, oats, ezekiel bread, rice cakes
3. Each day MUST have different recipes (no exact repeats on consecutive days)
4. Maximum 2 repetitions of any recipe throughout the week
5. Include variety in cooking methods and cuisines:
   - Mediterranean, Asian, Mexican, Italian, American BBQ
   - Grilled, baked, stir-fried, slow-cooked, pan-seared

RECIPE NAME REQUIREMENTS:
- Use specific, appetizing names (e.g., "Mediterranean Herb-Crusted Salmon" not "Salmon with Rice")
- Include cooking method or cuisine in name when possible
- Make names sound restaurant-quality and appealing

EXAMPLE VARIED RECIPES:
- Greek Lemon Chicken with Quinoa Tabbouleh
- Asian Beef Stir-Fry with Jasmine Rice
- BBQ Turkey Meatballs with Sweet Potato Mash
- Teriyaki Glazed Salmon with Sesame Brown Rice
- Mexican Beef Burrito Bowl with Cilantro Lime Rice
- Italian Herb Baked Cod with Roasted Vegetables
- Power Protein Pancakes with Greek Yogurt
- Moroccan Spiced Chicken with Couscous

PREVIOUSLY GENERATED RECIPES (DO NOT REPEAT):
{recent_recipes_str}

IMPORTANT: Create COMPLETELY NEW recipes that are different from all of the above.

CONSTRAINTS:
- Weekly budget: ${budget}
- Meals should be meal-prep friendly (can be stored 3-5 days)
- Focus on whole foods and simple preparation
- Prioritize variety over repetition for better adherence
- Generation timestamp: {variety_seed}

Return a JSON object with this exact structure:
{{
    "meal_plan": {{
        "day_1": {{
            "date": "YYYY-MM-DD",
            "is_training_day": true/false,
            "target_calories": number,
            "target_protein": number,
            "target_carbs": number,
            "target_fats": number,
            "meals": {{
                "meal_1": {{
                    "time": "12:00 PM",
                    "name": "Recipe Name",
                    "meal_type": "lunch",
                    "description": "Brief description",
                    "calories": number,
                    "protein_g": number,
                    "carbs_g": number,
                    "fats_g": number,
                    "fiber_g": number,
                    "prep_time": number,
                    "cook_time": number,
                    "ingredients": [
                        {{"name": "ingredient", "amount": number, "unit": "unit", "calories": number}}
                    ],
                    "instructions": [
                        "Step 1...",
                        "Step 2..."
                    ],
                    "meal_prep_tips": "Storage and reheating instructions"
                }},
                "meal_2": {{ ... }},
                "snack": {{ ... }}
            }}
        }},
        "day_2": {{ ... }},
        ... // Continue for all 7 days
    }},
    "shopping_list": {{
        "proteins": [
            {{"name": "Chicken breast", "amount": "3", "unit": "lbs", "estimated_cost": 15.00}}
        ],
        "carbs": [...],
        "fats": [...],
        "vegetables": [...],
        "fruits": [...],
        "dairy": [...],
        "pantry": [...],
        "spices": [...]
    }},
    "total_estimated_cost": number,
    "meal_prep_schedule": {{
        "sunday": ["Prep proteins", "Cook rice", "Chop vegetables"],
        "wednesday": ["Prep fresh vegetables", "Cook additional meals"]
    }},
    "tips": [
        "Tip 1 for success",
        "Tip 2 for variety"
    ]
}}

Make sure all meals fit within the intermittent fasting window (12pm-8pm).
Ensure training days have higher calories and rest days have moderate surplus.
Include practical, tasty recipes that support muscle building."""

        return prompt
    
    def validate_with_usda(self, meal_plan: Dict) -> Dict:
        """Validate and correct meal plan with USDA data"""
        validated_plan = deepcopy(meal_plan)
        
        # Handle single day plan structure
        if 'day_plan' in validated_plan:
            day_data = validated_plan['day_plan']
            meals = day_data.get('meals', [])
            
            # Track corrections made
            corrections_made = 0
            
            for meal in meals:
                verified_totals = {
                    'calories': 0,
                    'protein_g': 0,
                    'carbs_g': 0,
                    'fats_g': 0
                }
                
                ingredients = meal.get('ingredients', [])
                for ingredient in ingredients:
                    try:
                        # Search USDA database
                        usda_result = self.usda_service.get_with_fallback(
                            ingredient['name'],
                            ingredient['amount'],
                            ingredient['unit']
                        )
                        
                        if usda_result and 'calculated_nutrition' in usda_result:
                            verified_nutrition = usda_result['calculated_nutrition']
                            
                            # Calculate variance
                            variance = self._calculate_variance(ingredient, verified_nutrition)
                            
                            if variance > 0.10:  # 10% threshold
                                logger.info(f"Correcting {ingredient['name']}: "
                                          f"{variance:.1%} variance")
                                # Update ingredient with USDA values
                                ingredient['calories'] = verified_nutrition['calories']
                                ingredient['protein_g'] = verified_nutrition['protein_g']
                                ingredient['carbs_g'] = verified_nutrition['carbs_g']
                                ingredient['fats_g'] = verified_nutrition['fats_g']
                                corrections_made += 1
                            
                            # Add USDA reference
                            if 'fdcId' in usda_result:
                                ingredient['usda_fdc_id'] = usda_result['fdcId']
                            ingredient['usda_verified'] = True
                            
                    except Exception as e:
                        logger.warning(f"USDA validation failed for "
                                     f"{ingredient['name']}: {str(e)}")
                        ingredient['usda_verified'] = False
                    
                    # Update totals with verified or original values
                    verified_totals['calories'] += ingredient.get('calories', 0)
                    verified_totals['protein_g'] += ingredient.get('protein_g', 0)
                    verified_totals['carbs_g'] += ingredient.get('carbs_g', 0)
                    verified_totals['fats_g'] += ingredient.get('fats_g', 0)
                
                # Update meal totals with recalculated values
                meal.update(verified_totals)
            
            # Recalculate daily totals
            daily_totals = {
                'calories': sum(meal.get('calories', 0) for meal in meals),
                'protein_g': sum(meal.get('protein_g', 0) for meal in meals),
                'carbs_g': sum(meal.get('carbs_g', 0) for meal in meals),
                'fats_g': sum(meal.get('fats_g', 0) for meal in meals)
            }
            day_data['daily_totals'] = daily_totals
            
            if corrections_made > 0:
                logger.info(f"Made {corrections_made} nutritional corrections using USDA data")
        
        return validated_plan
    
    def _calculate_variance(self, original: Dict, verified: Dict) -> float:
        """Calculate average variance between original and verified nutrition"""
        variances = []
        
        for key in ['calories', 'protein_g', 'carbs_g', 'fats_g']:
            original_val = original.get(key, 0)
            verified_val = verified.get(key, 0)
            
            if original_val > 0:
                variance = abs(original_val - verified_val) / original_val
                variances.append(variance)
        
        return sum(variances) / len(variances) if variances else 0
    
    def research_nutrition_facts(self, ingredients: List[str], servings: int = 1) -> Dict[str, Any]:
        """
        Research detailed nutritional information for a list of ingredients
        
        Args:
            ingredients: List of ingredient descriptions
            servings: Number of servings to calculate for
            
        Returns:
            Dictionary with nutritional breakdown
        """
        if not self.is_available():
            return {"error": "AI service not available"}
        
        try:
            prompt = f"""Analyze the nutritional content of this recipe:

Ingredients:
{chr(10).join(f"- {ing}" for ing in ingredients)}

Servings: {servings}

Provide detailed nutritional analysis in JSON format:
{{
    "total_nutrition": {{
        "calories": number,
        "protein_g": number,
        "carbs_g": number,
        "fats_g": number,
        "fiber_g": number,
        "sugar_g": number,
        "sodium_mg": number
    }},
    "per_serving": {{
        "calories": number,
        "protein_g": number,
        "carbs_g": number,
        "fats_g": number,
        "fiber_g": number,
        "sugar_g": number,
        "sodium_mg": number
    }},
    "ingredients_breakdown": [
        {{
            "ingredient": "name",
            "calories": number,
            "protein_g": number,
            "carbs_g": number,
            "fats_g": number
        }}
    ],
    "health_score": number (0-100),
    "nutritional_highlights": ["High in protein", "Good source of fiber", etc.],
    "warnings": ["High in sodium", "Contains allergens", etc.]
}}"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a nutrition expert. Provide accurate nutritional analysis."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Error researching nutrition facts: {str(e)}")
            return {"error": "Failed to analyze nutrition"}
    
    def suggest_meal_substitutions(self, meal: Dict[str, Any], restrictions: List[str]) -> Dict[str, Any]:
        """
        Suggest substitutions for a meal based on dietary restrictions
        
        Args:
            meal: Original meal data
            restrictions: List of dietary restrictions
            
        Returns:
            Dictionary with suggested substitutions
        """
        if not self.is_available():
            return {"error": "AI service not available"}
        
        try:
            prompt = f"""Suggest substitutions for this meal to accommodate dietary restrictions:

Original Meal: {meal.get('name')}
Ingredients: {json.dumps(meal.get('ingredients', []))}
Nutrition: {meal.get('calories')} cal, {meal.get('protein_g')}g protein

Dietary Restrictions: {', '.join(restrictions)}

Provide substitutions in JSON format:
{{
    "substituted_meal": {{
        "name": "Modified recipe name",
        "changes": [
            {{"original": "ingredient", "substitute": "alternative", "reason": "explanation"}}
        ],
        "new_nutrition": {{
            "calories": number,
            "protein_g": number,
            "carbs_g": number,
            "fats_g": number
        }},
        "maintains_macros": true/false,
        "additional_notes": "Any important notes"
    }}
}}"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a nutrition expert specializing in dietary substitutions."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Error suggesting substitutions: {str(e)}")
            return {"error": "Failed to generate substitutions"}
    
    def optimize_shopping_list(self, shopping_list: Dict[str, Any], store: str, budget: float) -> Dict[str, Any]:
        """
        Optimize shopping list for budget and store availability
        
        Args:
            shopping_list: Original shopping list
            store: Store name
            budget: Budget constraint
            
        Returns:
            Optimized shopping list with cost-saving suggestions
        """
        if not self.is_available():
            return shopping_list
        
        try:
            prompt = f"""Optimize this shopping list for {store} with a ${budget} budget:

Shopping List: {json.dumps(shopping_list)}

Provide optimization suggestions in JSON format:
{{
    "optimized_list": {{
        "categories": {{ ... }},
        "bulk_buy_suggestions": [
            {{"item": "name", "reason": "Save $X by buying in bulk"}}
        ],
        "substitutions": [
            {{"original": "item", "substitute": "alternative", "savings": "$X"}}
        ],
        "seasonal_recommendations": ["In-season items that are cheaper"],
        "store_brand_alternatives": ["Items where store brand is recommended"],
        "estimated_total": number,
        "estimated_savings": number
    }}
}}"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a shopping optimization expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=1500,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Error optimizing shopping list: {str(e)}")
            return shopping_list
    
    def _get_recent_recipes(self, user_id: str = None) -> List[str]:
        """Get recently generated recipes from cache to avoid repetition"""
        if not user_id:
            return []
        
        try:
            cache_key = f'recent_recipes:{user_id}'
            cached_recipes = default_cache.get(cache_key)
            return cached_recipes if cached_recipes else []
        except Exception as e:
            logger.warning(f"Could not retrieve recent recipes: {str(e)}")
            return []
    
    def _track_generation_request(self, user_id: str) -> None:
        """Track that a generation request was made for variety seed"""
        if not user_id:
            return
        
        try:
            # Add timestamp to generation history for variety
            cache_key = f'generation_history:{user_id}'
            history = default_cache.get(cache_key) or []
            history.append({
                'timestamp': datetime.now().isoformat(),
                'date': datetime.now().strftime('%Y-%m-%d')
            })
            # Keep last 10 generation requests
            if len(history) > 10:
                history = history[-10:]
            default_cache.set(cache_key, history, ttl=7 * 24 * 3600)  # 1 week
        except Exception as e:
            logger.warning(f"Could not track generation request: {str(e)}")
    
    def _save_recipes_to_cache(self, user_id: str, meal_plan: Dict) -> None:
        """Save generated recipes to cache for variety tracking"""
        if not user_id:
            return
        
        try:
            # Extract all recipe names from the meal plan
            recipe_names = []
            
            # Handle single day plan
            if 'day_plan' in meal_plan:
                for meal in meal_plan['day_plan'].get('meals', []):
                    if 'name' in meal:
                        recipe_names.append(meal['name'])
            
            # Handle 7-day plan
            elif 'meal_plan' in meal_plan:
                for day_key, day_data in meal_plan['meal_plan'].items():
                    if day_key.startswith('day_') and 'meals' in day_data:
                        for meal_key, meal_data in day_data['meals'].items():
                            if 'name' in meal_data:
                                recipe_names.append(meal_data['name'])
            
            # Get existing recipes and add new ones
            cache_key = f'recent_recipes:{user_id}'
            existing = self._get_recent_recipes(user_id)
            
            # Combine and keep last 30 unique recipes
            all_recipes = existing + recipe_names
            unique_recipes = []
            seen = set()
            for recipe in reversed(all_recipes):
                if recipe not in seen:
                    unique_recipes.append(recipe)
                    seen.add(recipe)
            
            # Keep only the most recent 30 recipes
            recent_30 = list(reversed(unique_recipes[:30]))
            
            # Cache for 2 weeks
            default_cache.set(cache_key, recent_30, ttl=14 * 24 * 3600)
            
        except Exception as e:
            logger.warning(f"Could not save recipes to cache: {str(e)}")
    
    def _validate_and_enhance_meal_plan(self, meal_plan_data: Dict, user_data: Dict) -> Dict[str, Any]:
        """Validate AI-generated meal plan and add enhancements"""
        # Add metadata
        meal_plan_data['metadata'] = {
            'generated_at': datetime.now().isoformat(),
            'user_requirements': {
                'body_weight': user_data.get('body_weight'),
                'dietary_requirements': user_data.get('dietary_requirements', []),
                'budget': user_data.get('budget')
            },
            'ai_model': self.model
        }
        
        # Save recipes to cache for variety tracking
        if 'user_id' in user_data:
            self._save_recipes_to_cache(user_data['user_id'], meal_plan_data)
        
        # Validate nutritional targets are met
        # Add any missing fields with defaults
        # Ensure all meals fit within IF window
        
        return meal_plan_data
    
    def _get_demo_single_day_plan(self, user_data: Dict, is_training_day: bool) -> Dict[str, Any]:
        """Return a demo single day meal plan"""
        body_weight = user_data.get('body_weight', 175)
        maintenance = body_weight * 15
        total_calories = maintenance + (500 if is_training_day else 100)
        
        # Calculate macros
        protein_g = body_weight
        fats_calories = total_calories * 0.25
        fats_g = round(fats_calories / 9)
        protein_calories = protein_g * 4
        carbs_calories = total_calories - protein_calories - fats_calories
        carbs_g = round(carbs_calories / 4)
        
        demo_plan = {
            "day_plan": {
                "date": datetime.now().strftime('%Y-%m-%d'),
                "day_type": "training day" if is_training_day else "rest day",
                "total_targets": {
                    "calories": round(total_calories),
                    "protein_g": protein_g,
                    "carbs_g": carbs_g,
                    "fats_g": fats_g
                },
                "meals": [
                    {
                        "meal_number": 1,
                        "time": "12:00 PM",
                        "name": "Mediterranean Grilled Chicken Quinoa Salad",
                        "description": "Fresh herb-marinated chicken with citrus quinoa",
                        "calories": round(total_calories * 0.30),
                        "protein_g": round(protein_g * 0.30),
                        "carbs_g": round(carbs_g * 0.30),
                        "fats_g": round(fats_g * 0.30),
                        "fiber_g": 7,
                        "prep_time": 15,
                        "cook_time": 25,
                        "ingredients": [
                            {
                                "name": "Chicken breast, grilled",
                                "amount": 150,
                                "unit": "g",
                                "calories": 247,
                                "protein_g": 46,
                                "carbs_g": 0,
                                "fats_g": 5
                            },
                            {
                                "name": "Quinoa, cooked",
                                "amount": 180,
                                "unit": "g",
                                "calories": 216,
                                "protein_g": 7,
                                "carbs_g": 38,
                                "fats_g": 3
                            }
                        ],
                        "instructions": [
                            "Season chicken with oregano, thyme, and lemon",
                            "Grill until internal temp reaches 165°F",
                            "Mix quinoa with diced tomatoes, cucumber, and parsley",
                            "Drizzle with olive oil and lemon juice"
                        ],
                        "meal_prep_tips": "Store chicken and quinoa separately for best texture"
                    },
                    {
                        "meal_number": 2,
                        "time": "4:30 PM",
                        "name": "Pan-Seared Salmon with Brown Rice and Asparagus",
                        "description": "Omega-rich salmon with nutty brown rice",
                        "calories": round(total_calories * 0.35),
                        "protein_g": round(protein_g * 0.35),
                        "carbs_g": round(carbs_g * 0.35),
                        "fats_g": round(fats_g * 0.35),
                        "fiber_g": 4,
                        "prep_time": 10,
                        "cook_time": 20,
                        "ingredients": [
                            {
                                "name": "Salmon fillet, baked",
                                "amount": 170,
                                "unit": "g",
                                "calories": 350,
                                "protein_g": 37,
                                "carbs_g": 0,
                                "fats_g": 22
                            },
                            {
                                "name": "White rice, cooked",
                                "amount": 200,
                                "unit": "g",
                                "calories": 260,
                                "protein_g": 5,
                                "carbs_g": 56,
                                "fats_g": 1
                            }
                        ],
                        "instructions": [
                            "Brush salmon with homemade teriyaki glaze",
                            "Bake at 400°F for 12-15 minutes",
                            "Steam rice and top with sesame seeds",
                            "Serve with steamed edamame"
                        ],
                        "meal_prep_tips": "Cook salmon fresh; rice can be prepped ahead"
                    },
                    {
                        "meal_number": 3,
                        "time": "7:30 PM",
                        "name": "BBQ Turkey Meatballs with Sweet Potato Wedges",
                        "description": "Homemade turkey meatballs with roasted sweet potatoes",
                        "calories": round(total_calories * 0.35),
                        "protein_g": round(protein_g * 0.35),
                        "carbs_g": round(carbs_g * 0.35),
                        "fats_g": round(fats_g * 0.35),
                        "fiber_g": 8,
                        "prep_time": 15,
                        "cook_time": 30,
                        "ingredients": [
                            {
                                "name": "Ground beef 90% lean, cooked",
                                "amount": 150,
                                "unit": "g",
                                "calories": 325,
                                "protein_g": 39,
                                "carbs_g": 0,
                                "fats_g": 18
                            },
                            {
                                "name": "White rice, cooked",
                                "amount": 180,
                                "unit": "g",
                                "calories": 234,
                                "protein_g": 5,
                                "carbs_g": 50,
                                "fats_g": 1
                            }
                        ],
                        "instructions": [
                            "Season beef with cumin, chili powder, and paprika",
                            "Cook rice with lime juice and chopped cilantro",
                            "Top with black beans, salsa, and Greek yogurt",
                            "Add fresh lettuce and pico de gallo"
                        ],
                        "meal_prep_tips": "Store components separately and assemble when eating"
                    }
                ],
                "daily_totals": {
                    "calories": round(total_calories),
                    "protein_g": protein_g,
                    "carbs_g": carbs_g,
                    "fats_g": fats_g
                }
            },
            "demo_mode": True
        }
        
        # Auto-save recipes to database even in demo mode
        if user_data.get('auto_save_recipes', True) and 'user_id' in user_data:
            saved_recipe_ids = self._save_recipes_to_database(user_data['user_id'], demo_plan, is_single_day=True)
            logger.info(f"Demo single day: Saved {len(saved_recipe_ids)} recipes")
        
        return demo_plan
    
    def _get_demo_meal_plan(self, user_data: Dict) -> Dict[str, Any]:
        """Return a demo meal plan when AI is not available"""
        body_weight = user_data.get('body_weight', 175)
        maintenance = body_weight * 15
        
        # This is a simplified demo meal plan
        # In production, this would be more comprehensive
        meal_plan = {
            "meal_plan": {
                "day_1": {
                    "date": datetime.now().isoformat(),
                    "is_training_day": True,
                    "target_calories": maintenance + 500,
                    "target_protein": body_weight,
                    "target_carbs": int((maintenance + 500 - body_weight * 4 - (maintenance + 500) * 0.25) / 4),
                    "target_fats": int((maintenance + 500) * 0.25 / 9),
                    "meals": {
                        "meal_1": {
                            "time": "12:00 PM",
                            "name": "Mediterranean Lemon Herb Chicken with Quinoa Pilaf",
                            "meal_type": "lunch",
                            "description": "Greek-inspired bowl with fresh herbs and citrus",
                            "calories": 650,
                            "protein_g": 45,
                            "carbs_g": 65,
                            "fats_g": 15,
                            "fiber_g": 8,
                            "prep_time": 15,
                            "cook_time": 25,
                            "ingredients": [
                                {"name": "Chicken breast", "amount": 6, "unit": "oz", "calories": 280},
                                {"name": "Quinoa", "amount": 1, "unit": "cup cooked", "calories": 220},
                                {"name": "Broccoli", "amount": 1, "unit": "cup", "calories": 30},
                                {"name": "Olive oil", "amount": 1, "unit": "tbsp", "calories": 120}
                            ],
                            "instructions": [
                                "Marinate chicken in lemon, oregano, and garlic",
                                "Grill chicken until golden and cooked through",
                                "Cook quinoa with vegetable broth for extra flavor",
                                "Roast broccoli with garlic and lemon zest",
                                "Combine in bowl with fresh herbs and feta"
                            ],
                            "meal_prep_tips": "Store components separately. Chicken stays juicy when reheated gently."
                        },
                        "meal_2": {
                            "time": "4:30 PM",
                            "name": "Asian Beef Stir-Fry with Jasmine Rice",
                            "meal_type": "snack",
                            "description": "Quick stir-fry with tender beef and crisp vegetables",
                            "calories": 580,
                            "protein_g": 38,
                            "carbs_g": 52,
                            "fats_g": 18,
                            "fiber_g": 5,
                            "prep_time": 10,
                            "cook_time": 15,
                            "ingredients": [
                                {"name": "Lean beef strips", "amount": 5, "unit": "oz", "calories": 310},
                                {"name": "Jasmine rice", "amount": 1, "unit": "cup cooked", "calories": 205},
                                {"name": "Mixed vegetables", "amount": 1.5, "unit": "cups", "calories": 45},
                                {"name": "Sesame oil", "amount": 2, "unit": "tsp", "calories": 80}
                            ],
                            "instructions": [
                                "Slice beef thinly against the grain",
                                "Stir-fry beef in hot wok until browned",
                                "Add vegetables and stir-fry sauce",
                                "Serve over fluffy jasmine rice",
                                "Garnish with sesame seeds and scallions"
                            ],
                            "meal_prep_tips": "Keep sauce separate until reheating to maintain texture."
                        },
                        "meal_3": {
                            "time": "7:30 PM",
                            "name": "Teriyaki Glazed Salmon with Sweet Potato Mash",
                            "meal_type": "dinner",
                            "description": "Omega-3 rich salmon with creamy sweet potato",
                            "calories": 720,
                            "protein_g": 42,
                            "carbs_g": 68,
                            "fats_g": 22,
                            "fiber_g": 9,
                            "prep_time": 15,
                            "cook_time": 25,
                            "ingredients": [
                                {"name": "Salmon fillet", "amount": 6, "unit": "oz", "calories": 367},
                                {"name": "Sweet potato", "amount": 1, "unit": "large", "calories": 160},
                                {"name": "Green beans", "amount": 1, "unit": "cup", "calories": 35},
                                {"name": "Teriyaki glaze", "amount": 2, "unit": "tbsp", "calories": 60}
                            ],
                            "instructions": [
                                "Brush salmon with homemade teriyaki glaze",
                                "Bake salmon at 400°F for 12-15 minutes",
                                "Steam and mash sweet potato with cinnamon",
                                "Blanch green beans until crisp-tender",
                                "Plate beautifully for an Instagram-worthy meal"
                            ],
                            "meal_prep_tips": "Cook salmon fresh; sweet potato mash reheats perfectly."
                        }
                    }
                }
            },
            "shopping_list": {
                "proteins": [
                    {"name": "Chicken breast", "amount": "3", "unit": "lbs", "estimated_cost": 15.00}
                ],
                "carbs": [
                    {"name": "Quinoa", "amount": "1", "unit": "box", "estimated_cost": 5.00}
                ],
                "vegetables": [
                    {"name": "Broccoli", "amount": "2", "unit": "heads", "estimated_cost": 4.00}
                ]
            },
            "total_estimated_cost": 120.00,
            "demo_mode": True
        }
        
        # Auto-save recipes to database even in demo mode
        if user_data.get('auto_save_recipes', True) and 'user_id' in user_data:
            saved_recipe_ids = self._save_recipes_to_database(user_data['user_id'], meal_plan)
            logger.info(f"Demo mode: Saved {len(saved_recipe_ids)} recipes")
        
        return meal_plan
    
    def _save_recipes_to_database(self, user_id: str, meal_plan: Dict, is_single_day: bool = False) -> List[str]:
        """
        Save all recipes from a meal plan to the database
        
        Args:
            user_id: User ID
            meal_plan: Complete meal plan data
            is_single_day: Whether this is a single day plan
            
        Returns:
            List of saved recipe IDs
        """
        logger.info(f"Attempting to save recipes for user: {user_id}")
        
        try:
            # Import here to avoid circular imports
            from database.connection import supabase
            
            if not supabase:
                logger.warning("Supabase client not available, skipping recipe save")
                logger.info("To enable auto-save: Configure SUPABASE_URL and SUPABASE_KEY in .env")
                
                # Log what would have been saved
                recipe_count = 0
                if is_single_day and 'day_plan' in meal_plan and 'meals' in meal_plan['day_plan']:
                    recipe_count = len(meal_plan['day_plan']['meals'])
                elif 'meal_plan' in meal_plan:
                    for day_key, day_data in meal_plan['meal_plan'].items():
                        if day_key.startswith('day_') and 'meals' in day_data:
                            recipe_count += len(day_data['meals'])
                
                logger.info(f"Would have saved {recipe_count} recipes if Supabase was connected")
                return []
            
            saved_recipe_ids = []
            
            # Handle single day plan
            if is_single_day and 'meals' in meal_plan:
                for meal_key, meal_data in meal_plan['meals'].items():
                    recipe_id = self._save_single_recipe(supabase, meal_data, user_id)
                    if recipe_id:
                        saved_recipe_ids.append(recipe_id)
            
            # Handle 7-day plan
            elif 'meal_plan' in meal_plan:
                for day_key, day_data in meal_plan['meal_plan'].items():
                    if day_key.startswith('day_') and 'meals' in day_data:
                        for meal_key, meal_data in day_data['meals'].items():
                            recipe_id = self._save_single_recipe(supabase, meal_data, user_id)
                            if recipe_id:
                                saved_recipe_ids.append(recipe_id)
            
            logger.info(f"Saved {len(saved_recipe_ids)} recipes to database for user {user_id}")
            return saved_recipe_ids
            
        except Exception as e:
            logger.error(f"Error saving recipes to database: {str(e)}")
            return []
    
    def _save_single_recipe(self, supabase_client, meal_data: Dict[str, Any], user_id: str) -> Optional[str]:
        """
        Save a single recipe and its ingredients
        
        Args:
            supabase_client: Supabase client instance
            meal_data: Recipe/meal data
            user_id: User ID
            
        Returns:
            Recipe ID if successful
        """
        try:
            # Extract cuisine type from recipe name or description
            cuisine_type = self._extract_cuisine_type(meal_data.get('name', ''))
            
            # Prepare recipe data
            recipe_data = {
                'name': meal_data.get('name'),
                'description': meal_data.get('description'),
                'meal_type': meal_data.get('meal_type', 'meal'),
                'cuisine_type': cuisine_type,
                'prep_time': meal_data.get('prep_time'),
                'cook_time': meal_data.get('cook_time'),
                'servings': meal_data.get('servings', 1),
                'difficulty': meal_data.get('difficulty', 'medium'),
                'calories': meal_data.get('calories'),
                'protein_g': meal_data.get('protein_g'),
                'carbs_g': meal_data.get('carbs_g'),
                'fats_g': meal_data.get('fats_g'),
                'fiber_g': meal_data.get('fiber_g'),
                'instructions': meal_data.get('instructions', []),
                'tips': meal_data.get('meal_prep_tips'),
                'tags': self._generate_recipe_tags(meal_data)
            }
            
            # Save recipe
            recipe_id = RecipeStorageDB.save_ai_recipe(supabase_client, recipe_data, user_id)
            
            if recipe_id and 'ingredients' in meal_data:
                # Save ingredients
                RecipeStorageDB.save_recipe_ingredients(supabase_client, recipe_id, meal_data['ingredients'])
            
            return recipe_id
            
        except Exception as e:
            logger.error(f"Error saving single recipe: {str(e)}")
            return None
    
    def _save_generation_history(self, user_id: str, meal_plan: Dict, recipe_ids: List[str], generation_time_ms: int):
        """
        Save meal generation history
        
        Args:
            user_id: User ID
            meal_plan: Complete meal plan data
            recipe_ids: List of saved recipe IDs
            generation_time_ms: Time taken to generate
        """
        try:
            from database.connection import supabase
            
            if not supabase:
                return
            
            RecipeStorageDB.save_generation_history(
                supabase, 
                user_id, 
                meal_plan, 
                recipe_ids, 
                generation_time_ms
            )
            
        except Exception as e:
            logger.error(f"Error saving generation history: {str(e)}")
    
    def _extract_cuisine_type(self, recipe_name: str) -> str:
        """Extract cuisine type from recipe name"""
        cuisine_keywords = {
            'mediterranean': ['mediterranean', 'greek', 'italian'],
            'asian': ['asian', 'thai', 'chinese', 'japanese', 'korean', 'vietnamese'],
            'mexican': ['mexican', 'tex-mex', 'chipotle', 'taco', 'burrito'],
            'american': ['american', 'bbq', 'burger', 'southern'],
            'indian': ['indian', 'curry', 'tandoori', 'masala'],
            'middle_eastern': ['middle eastern', 'lebanese', 'turkish', 'moroccan']
        }
        
        recipe_lower = recipe_name.lower()
        for cuisine, keywords in cuisine_keywords.items():
            for keyword in keywords:
                if keyword in recipe_lower:
                    return cuisine
        
        return 'international'
    
    def _generate_recipe_tags(self, meal_data: Dict[str, Any]) -> List[str]:
        """Generate tags for a recipe based on its characteristics"""
        tags = []
        
        # Dietary tags
        name_lower = meal_data.get('name', '').lower()
        if 'vegetarian' in name_lower or 'veggie' in name_lower:
            tags.append('vegetarian')
        if 'vegan' in name_lower:
            tags.append('vegan')
        
        # Nutrition tags
        if meal_data.get('protein_g', 0) > 30:
            tags.append('high-protein')
        if meal_data.get('carbs_g', 0) < 20:
            tags.append('low-carb')
        if meal_data.get('calories', 0) < 400:
            tags.append('low-calorie')
        
        # Meal type
        meal_type = meal_data.get('meal_type', '')
        if meal_type:
            tags.append(meal_type)
        
        # Prep time
        total_time = (meal_data.get('prep_time', 0) or 0) + (meal_data.get('cook_time', 0) or 0)
        if total_time > 0 and total_time <= 30:
            tags.append('quick')
        
        # Meal prep friendly
        tags.append('meal-prep')
        
        return tags