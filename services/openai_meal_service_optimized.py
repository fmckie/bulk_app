"""
Optimized OpenAI GPT-4 Service for single-day meal planning
Focused on accuracy and Kinobody nutritional principles
"""
import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import openai
from openai import OpenAI

logger = logging.getLogger(__name__)


class OpenAIMealServiceOptimized:
    """Optimized service for generating accurate single-day meal plans"""
    
    def __init__(self):
        """Initialize OpenAI client with API key from environment"""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            logger.warning("OpenAI API key not found. AI features will be disabled.")
            self.client = None
        else:
            self.client = OpenAI(api_key=api_key)
            self.model = os.getenv('OPENAI_MODEL', 'gpt-4-0125-preview')
    
    def is_available(self) -> bool:
        """Check if OpenAI service is available"""
        return self.client is not None
    
    def generate_single_day_meal_plan(self, user_data: Dict[str, Any], is_training_day: bool) -> Dict[str, Any]:
        """
        Generate a single day meal plan with exact nutritional targets
        
        Args:
            user_data: Dictionary containing user profile and preferences
            is_training_day: Whether this is a training day or rest day
            
        Returns:
            Dictionary containing the single day meal plan
        """
        if not self.is_available():
            return self._get_demo_single_day(user_data, is_training_day)
        
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
            
            # Build optimized prompt
            prompt = self._build_optimized_single_day_prompt(
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
                        "content": self._get_optimized_system_prompt()
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent output
                max_tokens=2500,
                response_format={"type": "json_object"}
            )
            
            # Parse and validate the response
            meal_plan_data = json.loads(response.choices[0].message.content)
            
            # Ensure proper structure
            if 'day_plan' not in meal_plan_data:
                raise ValueError("Invalid meal plan structure")
            
            return {
                'success': True,
                'day_type': day_type,
                'targets': {
                    'calories': round(total_calories),
                    'protein_g': protein_g,
                    'carbs_g': carbs_g,
                    'fats_g': fats_g
                },
                'day_plan': meal_plan_data['day_plan']
            }
            
        except Exception as e:
            logger.error(f"Error generating single day meal plan: {str(e)}")
            return self._get_demo_single_day(user_data, is_training_day)
    
    def _get_optimized_system_prompt(self) -> str:
        """Get optimized system prompt focused on accuracy"""
        return """You are an expert nutritionist specializing in the Kinobody Greek God program and meal prep planning. 
Your #1 priority is creating meal plans with EXACT nutritional accuracy.

Key principles:
1. EXACT MACROS: Every meal plan must hit the exact calorie and macro targets provided (within 2% tolerance)
2. REAL RECIPES: Use only real, practical recipes with common ingredients
3. PRECISE MEASUREMENTS: Every ingredient must have exact measurements in grams or standard units
4. INTERMITTENT FASTING: All meals must fit within 12pm-8pm eating window
5. MEAL PREP FRIENDLY: Foods that store well for 3-5 days

When calculating nutrition:
- Use USDA database values for accuracy
- Account for cooking methods (e.g., oil absorption)
- Be precise with portions (e.g., "170g cooked chicken breast" not "6 oz chicken")
- Include all cooking fats and oils in calculations

You must return valid JSON with exact nutritional breakdowns."""
    
    def _build_optimized_single_day_prompt(self, body_weight: int, total_calories: int, 
                                          protein_g: int, carbs_g: int, fats_g: int, 
                                          day_type: str, dietary_requirements: List[str]) -> str:
        """Build optimized prompt for single day meal generation"""
        
        restrictions = ', '.join(dietary_requirements) if dietary_requirements else 'None'
        
        return f"""Create exactly 3 meals for ONE {day_type} following the Kinobody Greek God program.

EXACT NUTRITIONAL TARGETS (MUST HIT WITHIN 2%):
- Total Daily Calories: {total_calories}
- Protein: {protein_g}g
- Carbs: {carbs_g}g
- Fats: {fats_g}g

MEAL SCHEDULE (Intermittent Fasting 12pm-8pm):
- Meal 1: 12:00 PM (First meal, moderate size, ~30% of daily calories)
- Meal 2: 4:30 PM (Pre/post workout meal, ~35% of daily calories)
- Meal 3: 7:30 PM (Largest meal, ~35% of daily calories)

DIETARY RESTRICTIONS: {restrictions}

Return JSON with this EXACT structure:
{{
    "day_plan": {{
        "date": "2024-01-15",
        "day_type": "{day_type}",
        "total_targets": {{
            "calories": {total_calories},
            "protein_g": {protein_g},
            "carbs_g": {carbs_g},
            "fats_g": {fats_g}
        }},
        "meals": [
            {{
                "meal_number": 1,
                "time": "12:00 PM",
                "name": "Exact recipe name",
                "description": "Brief description",
                "calories": number,
                "protein_g": number,
                "carbs_g": number,
                "fats_g": number,
                "fiber_g": number,
                "ingredients": [
                    {{
                        "name": "Grilled chicken breast",
                        "amount": 170,
                        "unit": "g",
                        "calories": 280,
                        "protein_g": 52,
                        "carbs_g": 0,
                        "fats_g": 6
                    }}
                ],
                "instructions": ["Step 1", "Step 2"],
                "prep_tips": "Storage and reheating instructions"
            }},
            // ... meals 2 and 3 with same structure
        ],
        "daily_totals": {{
            "calories": sum of all meals,
            "protein_g": sum of all meals,
            "carbs_g": sum of all meals,
            "fats_g": sum of all meals
        }},
        "accuracy_check": {{
            "calories_accuracy": percentage of target,
            "protein_accuracy": percentage of target,
            "carbs_accuracy": percentage of target,
            "fats_accuracy": percentage of target
        }}
    }}
}}

CRITICAL REQUIREMENTS:
1. The sum of all 3 meals MUST equal the daily targets (within 2%)
2. Each ingredient must have exact nutritional data
3. Use realistic portions and common ingredients
4. Include cooking oils/fats in calculations
5. Ensure meals are filling and satisfying

Example ingredients with accurate nutrition per 100g:
- Chicken breast (cooked): 165 cal, 31g protein, 0g carbs, 3.6g fat
- White rice (cooked): 130 cal, 2.7g protein, 28g carbs, 0.3g fat
- Sweet potato (baked): 90 cal, 2g protein, 21g carbs, 0.1g fat
- Olive oil: 884 cal, 0g protein, 0g carbs, 100g fat
- Avocado: 160 cal, 2g protein, 9g carbs, 15g fat

Create a practical, delicious meal plan that hits these exact targets."""
    
    def _get_demo_single_day(self, user_data: Dict, is_training_day: bool) -> Dict[str, Any]:
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
            'success': True,
            'day_type': 'training day' if is_training_day else 'rest day',
            'targets': {
                'calories': round(total_calories),
                'protein_g': protein_g,
                'carbs_g': carbs_g,
                'fats_g': fats_g
            },
            'day_plan': {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'day_type': 'training day' if is_training_day else 'rest day',
                'total_targets': {
                    'calories': round(total_calories),
                    'protein_g': protein_g,
                    'carbs_g': carbs_g,
                    'fats_g': fats_g
                },
                'meals': [
                    {
                        'meal_number': 1,
                        'time': '12:00 PM',
                        'name': 'Grilled Chicken & Sweet Potato Bowl',
                        'description': 'High-protein lunch with complex carbs',
                        'calories': round(total_calories * 0.30),
                        'protein_g': round(protein_g * 0.30),
                        'carbs_g': round(carbs_g * 0.30),
                        'fats_g': round(fats_g * 0.30),
                        'fiber_g': 6,
                        'ingredients': [
                            {
                                'name': 'Grilled chicken breast',
                                'amount': 150,
                                'unit': 'g',
                                'calories': 247,
                                'protein_g': 46,
                                'carbs_g': 0,
                                'fats_g': 5
                            },
                            {
                                'name': 'Sweet potato (baked)',
                                'amount': 200,
                                'unit': 'g',
                                'calories': 180,
                                'protein_g': 4,
                                'carbs_g': 42,
                                'fats_g': 0
                            }
                        ],
                        'instructions': [
                            'Season and grill chicken breast',
                            'Bake sweet potato at 400°F for 45 minutes',
                            'Serve with steamed vegetables'
                        ],
                        'prep_tips': 'Store in containers for up to 4 days'
                    }
                ],
                'demo_mode': True
            }
        }
    
    def validate_meal_plan_accuracy(self, meal_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate the accuracy of a generated meal plan
        
        Args:
            meal_plan: Generated meal plan to validate
            
        Returns:
            Validation results with accuracy metrics
        """
        day_plan = meal_plan.get('day_plan', {})
        targets = day_plan.get('total_targets', {})
        meals = day_plan.get('meals', [])
        
        # Calculate actual totals
        actual_totals = {
            'calories': 0,
            'protein_g': 0,
            'carbs_g': 0,
            'fats_g': 0
        }
        
        for meal in meals:
            actual_totals['calories'] += meal.get('calories', 0)
            actual_totals['protein_g'] += meal.get('protein_g', 0)
            actual_totals['carbs_g'] += meal.get('carbs_g', 0)
            actual_totals['fats_g'] += meal.get('fats_g', 0)
        
        # Calculate accuracy percentages
        accuracy = {}
        issues = []
        
        for macro in ['calories', 'protein_g', 'carbs_g', 'fats_g']:
            target = targets.get(macro, 1)  # Avoid division by zero
            actual = actual_totals[macro]
            accuracy_pct = (actual / target * 100) if target > 0 else 0
            accuracy[macro] = round(accuracy_pct, 1)
            
            # Check if within 2% tolerance
            if abs(100 - accuracy_pct) > 2:
                issues.append(f"{macro}: {actual} ({accuracy_pct:.1f}% of target {target})")
        
        return {
            'valid': len(issues) == 0,
            'actual_totals': actual_totals,
            'accuracy': accuracy,
            'issues': issues
        }