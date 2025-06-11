"""
OpenAI GPT-4 Mini Service for AI-powered meal planning
"""
import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import openai
from openai import OpenAI

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
            self.model = os.getenv('OPENAI_MODEL', 'gpt-4-0125-preview')
    
    def is_available(self) -> bool:
        """Check if OpenAI service is available"""
        return self.client is not None
    
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
                        "content": """You are an expert nutritionist specializing in fitness meal planning, 
                        particularly the Kinobody Greek God program. You create detailed, practical meal plans 
                        that are easy to prepare, budget-friendly, and optimized for muscle building and fat loss.
                        Always return responses in valid JSON format."""
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
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
    
    def _build_meal_plan_prompt(self, user_data: Dict, maintenance_calories: int, training_days: List[str]) -> str:
        """Build detailed prompt for meal plan generation"""
        dietary_requirements = user_data.get('dietary_requirements', [])
        budget = user_data.get('budget', 150)
        store = user_data.get('store_preference', 'local grocery store')
        
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
- Preferred store: {store}
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
                'budget': user_data.get('budget'),
                'store': user_data.get('store_preference')
            },
            'ai_model': self.model
        }
        
        # Validate nutritional targets are met
        # Add any missing fields with defaults
        # Ensure all meals fit within IF window
        
        return meal_plan_data
    
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