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
            
            # Build optimized prompt for single day
            prompt = self._build_single_day_prompt(
                body_weight=body_weight,
                total_calories=round(total_calories),
                protein_g=protein_g,
                carbs_g=carbs_g,
                fats_g=fats_g,
                day_type=day_type,
                dietary_requirements=user_data.get('dietary_requirements', [])
            )
            
            # Generate meal plan with AI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": """You are an expert nutritionist specializing in the Kinobody Greek God program and meal prep planning.
Your #1 priority is creating meal plans with EXACT nutritional accuracy using USDA FoodData Central values.

Key principles:
1. EXACT MACROS: Every meal plan must hit the exact calorie and macro targets provided (within 2% tolerance)
2. REAL RECIPES: Use only real, practical recipes with common ingredients
3. PRECISE MEASUREMENTS: Every ingredient must have exact measurements in grams or standard units
4. INTERMITTENT FASTING: All meals must fit within 12pm-8pm eating window
5. MEAL PREP FRIENDLY: Foods that store well for 3-5 days

CRITICAL - Use USDA-verified nutritional values:
- ALL nutritional values will be validated against USDA FoodData Central
- Use specific USDA food names (e.g., "Chicken, breast, meat only, cooked, grilled")
- Include preparation method: "raw", "cooked", "grilled", "baked"
- Be specific: "chicken breast, boneless, skinless, cooked" not just "chicken"
- Your values MUST match USDA data within 10% or they will be corrected

Common USDA-verified values per 100g:
- Chicken breast, cooked: 165 cal, 31g protein, 0g carbs, 3.6g fat
- Rice, white, cooked: 130 cal, 2.7g protein, 28g carbs, 0.3g fat
- Sweet potato, baked: 90 cal, 2g protein, 21g carbs, 0.1g fat
- Oil, olive: 884 cal, 0g protein, 0g carbs, 100g fat

You must return ONLY valid JSON with exact nutritional breakdowns. No other text."""
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent nutritional accuracy
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
            
            # Build the prompt
            prompt = self._build_meal_plan_prompt(user_data, maintenance_calories, training_days)
            
            # Generate meal plan with AI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": """You are an expert nutritionist specializing in the Kinobody Greek God program and meal prep planning.
Your #1 priority is creating meal plans with EXACT nutritional accuracy using USDA FoodData Central values.

Key principles:
1. EXACT MACROS: Every meal plan must hit the exact calorie and macro targets provided (within 2% tolerance)
2. REAL RECIPES: Use only real, practical recipes with common ingredients
3. PRECISE MEASUREMENTS: Every ingredient must have exact measurements in grams or standard units
4. INTERMITTENT FASTING: All meals must fit within 12pm-8pm eating window
5. MEAL PREP FRIENDLY: Foods that store well for 3-5 days

CRITICAL - Use USDA-verified nutritional values:
- ALL nutritional values will be validated against USDA FoodData Central
- Use specific USDA food names (e.g., "Chicken, breast, meat only, cooked, grilled")
- Include preparation method: "raw", "cooked", "grilled", "baked"
- Be specific: "chicken breast, boneless, skinless, cooked" not just "chicken"
- Your values MUST match USDA data within 10% or they will be corrected

Common USDA-verified values per 100g:
- Chicken breast, cooked: 165 cal, 31g protein, 0g carbs, 3.6g fat
- Rice, white, cooked: 130 cal, 2.7g protein, 28g carbs, 0.3g fat
- Sweet potato, baked: 90 cal, 2g protein, 21g carbs, 0.1g fat
- Oil, olive: 884 cal, 0g protein, 0g carbs, 100g fat

You must return ONLY valid JSON with exact nutritional breakdowns. No other text."""
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent nutritional accuracy
                max_tokens=4000,
                response_format={"type": "json_object"}
            )
            
            # Parse the response
            meal_plan_data = json.loads(response.choices[0].message.content)
            
            # Validate and enhance the meal plan
            meal_plan = self._validate_and_enhance_meal_plan(meal_plan_data, user_data)
            
            return meal_plan
            
        except Exception as e:
            logger.error(f"Error generating meal plan with AI: {str(e)}")
            # Fall back to demo meal plan
            return self._get_demo_meal_plan(user_data)
    
    def _build_single_day_prompt(self, body_weight: int, total_calories: int, 
                                          protein_g: int, carbs_g: int, fats_g: int, 
                                          day_type: str, dietary_requirements: List[str]) -> str:
        """Build optimized prompt for single day meal generation"""
        
        restrictions = ', '.join(dietary_requirements) if dietary_requirements else 'None'
        
        return f"""Create 3 meals for a {day_type} with EXACT macros:
Calories: {total_calories} | Protein: {protein_g}g | Carbs: {carbs_g}g | Fats: {fats_g}g

Schedule (Intermittent Fasting):
- Meal 1: 12:00 PM (~30% calories)
- Meal 2: 4:30 PM (~35% calories)  
- Meal 3: 7:30 PM (~35% calories)

Dietary restrictions: {restrictions}

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
                "name": "Recipe Name",
                "calories": exact_number,
                "protein_g": exact_number,
                "carbs_g": exact_number,
                "fats_g": exact_number,
                "ingredients": [
                    {{"name": "chicken breast", "amount": 170, "unit": "g", "calories": 280, "protein_g": 52, "carbs_g": 0, "fats_g": 6}}
                ],
                "instructions": ["Step 1", "Step 2"]
            }},
            // ... meal 2 and 3
        ],
        "daily_totals": {{"calories": sum, "protein_g": sum, "carbs_g": sum, "fats_g": sum}}
    }}
}}

CRITICAL: Sum of 3 meals MUST equal targets within 2%. Include all cooking oils in calculations.

Common food macros per 100g:
- Chicken breast (cooked): 165cal, 31g protein, 0g carbs, 3.6g fat
- White rice (cooked): 130cal, 2.7g protein, 28g carbs, 0.3g fat  
- Sweet potato (baked): 90cal, 2g protein, 21g carbs, 0.1g fat
- Olive oil: 884cal, 0g protein, 0g carbs, 100g fat (NO carbs in oil!)
- Ground beef 90% lean: 217cal, 26g protein, 0g carbs, 12g fat"""
    
    def _build_meal_plan_prompt(self, user_data: Dict, maintenance_calories: int, training_days: List[str]) -> str:
        """Build detailed prompt for meal plan generation"""
        dietary_requirements = user_data.get('dietary_requirements', [])
        budget = user_data.get('budget', 150)
        
        prompt = f"""Create a 7-day meal prep plan with the following requirements:

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

CONSTRAINTS:
- Weekly budget: ${budget}
- Meals should be meal-prep friendly (can be stored 3-5 days)
- Include variety but repeat some recipes for efficiency
- Focus on whole foods and simple preparation

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
        
        return {
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
                        "name": "Grilled Chicken & Sweet Potato Bowl",
                        "description": "High-protein lunch with complex carbs",
                        "calories": round(total_calories * 0.30),
                        "protein_g": round(protein_g * 0.30),
                        "carbs_g": round(carbs_g * 0.30),
                        "fats_g": round(fats_g * 0.30),
                        "fiber_g": 6,
                        "prep_time": 15,
                        "cook_time": 25,
                        "ingredients": [
                            {
                                "name": "Grilled chicken breast",
                                "amount": 150,
                                "unit": "g",
                                "calories": 247,
                                "protein_g": 46,
                                "carbs_g": 0,
                                "fats_g": 5
                            },
                            {
                                "name": "Sweet potato (baked)",
                                "amount": 200,
                                "unit": "g",
                                "calories": 180,
                                "protein_g": 4,
                                "carbs_g": 42,
                                "fats_g": 0
                            }
                        ],
                        "instructions": [
                            "Season and grill chicken breast",
                            "Bake sweet potato at 400°F for 45 minutes",
                            "Serve with steamed vegetables"
                        ],
                        "meal_prep_tips": "Store in containers for up to 4 days"
                    },
                    {
                        "meal_number": 2,
                        "time": "4:30 PM",
                        "name": "Post-Workout Protein Bowl",
                        "description": "Recovery meal with fast-digesting carbs",
                        "calories": round(total_calories * 0.35),
                        "protein_g": round(protein_g * 0.35),
                        "carbs_g": round(carbs_g * 0.35),
                        "fats_g": round(fats_g * 0.35),
                        "fiber_g": 4,
                        "prep_time": 10,
                        "cook_time": 20,
                        "ingredients": [],
                        "instructions": [],
                        "meal_prep_tips": "Best consumed fresh after workout"
                    },
                    {
                        "meal_number": 3,
                        "time": "7:30 PM",
                        "name": "Lean Beef & Rice Dinner",
                        "description": "Satisfying dinner with balanced macros",
                        "calories": round(total_calories * 0.35),
                        "protein_g": round(protein_g * 0.35),
                        "carbs_g": round(carbs_g * 0.35),
                        "fats_g": round(fats_g * 0.35),
                        "fiber_g": 5,
                        "prep_time": 15,
                        "cook_time": 30,
                        "ingredients": [],
                        "instructions": [],
                        "meal_prep_tips": "Can be prepped in bulk for the week"
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
    
    def _get_demo_meal_plan(self, user_data: Dict) -> Dict[str, Any]:
        """Return a demo meal plan when AI is not available"""
        body_weight = user_data.get('body_weight', 175)
        maintenance = body_weight * 15
        
        # This is a simplified demo meal plan
        # In production, this would be more comprehensive
        return {
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
                            "name": "Grilled Chicken Power Bowl",
                            "meal_type": "lunch",
                            "description": "High-protein bowl with quinoa and vegetables",
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
                                "Season chicken with herbs and spices",
                                "Grill chicken for 6-7 minutes per side",
                                "Cook quinoa according to package directions",
                                "Steam broccoli until tender",
                                "Combine in bowl and drizzle with olive oil"
                            ],
                            "meal_prep_tips": "Store components separately. Reheat chicken and quinoa, add fresh vegetables."
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