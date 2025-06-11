"""
Meal Prep Service for managing meal plans and recipes
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from decimal import Decimal

logger = logging.getLogger(__name__)


class MealPrepService:
    """Service for meal plan management and generation"""
    
    def __init__(self, supabase_client=None):
        """Initialize with Supabase client"""
        self.supabase = supabase_client
    
    def calculate_nutritional_targets(self, user_profile: Dict[str, Any], date: str) -> Dict[str, Any]:
        """
        Calculate daily nutritional targets based on Kinobody principles
        
        Args:
            user_profile: User profile data including body weight
            date: Date to check if it's a training day
            
        Returns:
            Dictionary with nutritional targets
        """
        body_weight = float(user_profile.get('body_weight', 175))
        
        # Base calculations
        maintenance_calories = body_weight * 15
        protein_target = body_weight  # 1g per lb
        
        # Check if it's a training day (this would check workout schedule)
        is_training_day = self._is_training_day(user_profile.get('id'), date)
        
        if is_training_day:
            total_calories = maintenance_calories + 500  # +500 surplus on training days
        else:
            total_calories = maintenance_calories + 100  # +100 surplus on rest days
        
        # Calculate macros
        fats_calories = total_calories * 0.25  # 25% from fats
        fats_grams = fats_calories / 9
        
        protein_calories = protein_target * 4
        
        carbs_calories = total_calories - protein_calories - fats_calories
        carbs_grams = carbs_calories / 4
        
        return {
            'date': date,
            'is_training_day': is_training_day,
            'body_weight': body_weight,
            'maintenance_calories': round(maintenance_calories),
            'total_calories': round(total_calories),
            'protein_g': round(protein_target),
            'carbs_g': round(carbs_grams),
            'fats_g': round(fats_grams),
            'calorie_surplus': round(total_calories - maintenance_calories)
        }
    
    def create_meal_plan(self, user_id: str, meal_plan_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new meal plan in the database
        
        Args:
            user_id: User ID
            meal_plan_data: Meal plan data from AI or manual creation
            
        Returns:
            Created meal plan with ID
        """
        if not self.supabase:
            return self._create_demo_meal_plan(user_id, meal_plan_data)
        
        try:
            # Extract metadata
            start_date = datetime.now().date()
            end_date = start_date + timedelta(days=6)
            
            # Create meal plan record
            meal_plan = {
                'user_id': user_id,
                'name': meal_plan_data.get('name', f'Meal Plan - {start_date.strftime("%b %d")}'),
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'dietary_requirements': meal_plan_data.get('dietary_requirements', []),
                'budget': meal_plan_data.get('budget'),
                'store_preference': meal_plan_data.get('store_preference'),
                'ai_generated': meal_plan_data.get('ai_generated', True),
                'total_cost': meal_plan_data.get('total_estimated_cost'),
                'status': 'draft'
            }
            
            result = self.supabase.table('meal_plans').insert(meal_plan).execute()
            meal_plan_id = result.data[0]['id']
            
            # Create recipes and meal associations
            if 'meal_plan' in meal_plan_data:
                self._create_meal_associations(meal_plan_id, meal_plan_data['meal_plan'])
            
            # Create shopping list
            if 'shopping_list' in meal_plan_data:
                self._create_shopping_list(meal_plan_id, meal_plan_data['shopping_list'], 
                                         meal_plan_data.get('total_estimated_cost'))
            
            return {
                'success': True,
                'meal_plan_id': meal_plan_id,
                'data': result.data[0]
            }
            
        except Exception as e:
            logger.error(f"Error creating meal plan: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_meal_plan(self, meal_plan_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a complete meal plan with all associated data
        
        Args:
            meal_plan_id: Meal plan ID
            user_id: User ID for authorization
            
        Returns:
            Complete meal plan data or None
        """
        if not self.supabase:
            return None
        
        try:
            # Get meal plan
            meal_plan = self.supabase.table('meal_plans')\
                .select('*')\
                .eq('id', meal_plan_id)\
                .eq('user_id', user_id)\
                .single()\
                .execute()
            
            if not meal_plan.data:
                return None
            
            # Get associated meals with recipes
            meals = self.supabase.table('meal_plan_meals')\
                .select('*, recipes(*)')\
                .eq('meal_plan_id', meal_plan_id)\
                .order('day_number', desc=False)\
                .order('order_index', desc=False)\
                .execute()
            
            # Get shopping list
            shopping_list = self.supabase.table('shopping_lists')\
                .select('*')\
                .eq('meal_plan_id', meal_plan_id)\
                .single()\
                .execute()
            
            # Organize data by day
            organized_plan = self._organize_meal_plan_by_day(meal_plan.data, meals.data)
            
            return {
                'meal_plan': organized_plan,
                'shopping_list': shopping_list.data if shopping_list.data else None
            }
            
        except Exception as e:
            logger.error(f"Error getting meal plan: {str(e)}")
            return None
    
    def get_user_meal_plans(self, user_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all meal plans for a user
        
        Args:
            user_id: User ID
            status: Optional status filter
            
        Returns:
            List of meal plans
        """
        if not self.supabase:
            return []
        
        try:
            query = self.supabase.table('meal_plans')\
                .select('*')\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)
            
            if status:
                query = query.eq('status', status)
            
            result = query.execute()
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error getting user meal plans: {str(e)}")
            return []
    
    def update_meal_plan_status(self, meal_plan_id: str, user_id: str, status: str) -> bool:
        """
        Update meal plan status
        
        Args:
            meal_plan_id: Meal plan ID
            user_id: User ID for authorization
            status: New status (draft, active, completed, archived)
            
        Returns:
            Success boolean
        """
        if not self.supabase:
            return False
        
        try:
            result = self.supabase.table('meal_plans')\
                .update({'status': status})\
                .eq('id', meal_plan_id)\
                .eq('user_id', user_id)\
                .execute()
            
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Error updating meal plan status: {str(e)}")
            return False
    
    def save_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """
        Save or update user meal preferences
        
        Args:
            user_id: User ID
            preferences: Preference data
            
        Returns:
            Success boolean
        """
        if not self.supabase:
            return False
        
        try:
            # Check if preferences exist
            existing = self.supabase.table('user_meal_preferences')\
                .select('id')\
                .eq('user_id', user_id)\
                .single()\
                .execute()
            
            preferences_data = {
                'user_id': user_id,
                'liked_recipes': preferences.get('liked_recipes', []),
                'disliked_recipes': preferences.get('disliked_recipes', []),
                'favorite_ingredients': preferences.get('favorite_ingredients', []),
                'avoided_ingredients': preferences.get('avoided_ingredients', []),
                'cuisine_preferences': preferences.get('cuisine_preferences', []),
                'cooking_skill_level': preferences.get('cooking_skill_level', 'intermediate')
            }
            
            if existing.data:
                # Update existing
                result = self.supabase.table('user_meal_preferences')\
                    .update(preferences_data)\
                    .eq('user_id', user_id)\
                    .execute()
            else:
                # Create new
                result = self.supabase.table('user_meal_preferences')\
                    .insert(preferences_data)\
                    .execute()
            
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Error saving user preferences: {str(e)}")
            return False
    
    def get_user_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user meal preferences
        
        Args:
            user_id: User ID
            
        Returns:
            User preferences or None
        """
        if not self.supabase:
            return None
        
        try:
            result = self.supabase.table('user_meal_preferences')\
                .select('*')\
                .eq('user_id', user_id)\
                .single()\
                .execute()
            
            return result.data if result.data else None
            
        except Exception as e:
            logger.error(f"Error getting user preferences: {str(e)}")
            return None
    
    def add_recipe_feedback(self, user_id: str, recipe_id: str, rating: int, comments: str = "") -> bool:
        """
        Add feedback for a recipe
        
        Args:
            user_id: User ID
            recipe_id: Recipe ID
            rating: Rating 1-5
            comments: Optional comments
            
        Returns:
            Success boolean
        """
        if not self.supabase:
            return False
        
        try:
            # Get current preferences
            prefs = self.get_user_preferences(user_id)
            if not prefs:
                # Create new preferences
                prefs = {
                    'meal_feedback': []
                }
                self.save_user_preferences(user_id, prefs)
            
            # Add feedback
            feedback = {
                'recipe_id': recipe_id,
                'rating': rating,
                'comments': comments,
                'date': datetime.now().isoformat()
            }
            
            meal_feedback = prefs.get('meal_feedback', [])
            meal_feedback.append(feedback)
            
            # Update liked/disliked recipes based on rating
            if rating >= 4:
                liked = prefs.get('liked_recipes', [])
                if recipe_id not in liked:
                    liked.append(recipe_id)
                prefs['liked_recipes'] = liked
            elif rating <= 2:
                disliked = prefs.get('disliked_recipes', [])
                if recipe_id not in disliked:
                    disliked.append(recipe_id)
                prefs['disliked_recipes'] = disliked
            
            prefs['meal_feedback'] = meal_feedback
            
            return self.save_user_preferences(user_id, prefs)
            
        except Exception as e:
            logger.error(f"Error adding recipe feedback: {str(e)}")
            return False
    
    def _is_training_day(self, user_id: str, date: str) -> bool:
        """Check if a given date is a training day for the user"""
        # This would check the workout schedule
        # For now, assume MWF are training days
        day_of_week = datetime.fromisoformat(date).weekday()
        return day_of_week in [0, 2, 4]  # Monday, Wednesday, Friday
    
    def _create_meal_associations(self, meal_plan_id: str, meal_plan_days: Dict[str, Any]):
        """Create meal-recipe associations for a meal plan"""
        try:
            for day_key, day_data in meal_plan_days.items():
                if not day_key.startswith('day_'):
                    continue
                
                day_number = int(day_key.split('_')[1])
                
                for meal_key, meal_data in day_data.get('meals', {}).items():
                    # First, create or get the recipe
                    recipe_id = self._create_or_get_recipe(meal_data)
                    
                    if recipe_id:
                        # Create meal association
                        meal_association = {
                            'meal_plan_id': meal_plan_id,
                            'recipe_id': recipe_id,
                            'day_number': day_number,
                            'meal_type': meal_data.get('meal_type', 'meal'),
                            'servings': meal_data.get('servings', 1),
                            'order_index': self._get_meal_order_index(meal_data.get('meal_type'))
                        }
                        
                        self.supabase.table('meal_plan_meals').insert(meal_association).execute()
                        
        except Exception as e:
            logger.error(f"Error creating meal associations: {str(e)}")
    
    def _create_or_get_recipe(self, meal_data: Dict[str, Any]) -> Optional[str]:
        """Create a new recipe or get existing one"""
        try:
            # Check if recipe already exists
            existing = self.supabase.table('recipes')\
                .select('id')\
                .eq('name', meal_data.get('name'))\
                .single()\
                .execute()
            
            if existing.data:
                return existing.data['id']
            
            # Create new recipe
            recipe = {
                'name': meal_data.get('name'),
                'description': meal_data.get('description'),
                'meal_type': meal_data.get('meal_type'),
                'prep_time': meal_data.get('prep_time'),
                'cook_time': meal_data.get('cook_time'),
                'servings': meal_data.get('servings', 1),
                'calories': meal_data.get('calories'),
                'protein_g': meal_data.get('protein_g'),
                'carbs_g': meal_data.get('carbs_g'),
                'fats_g': meal_data.get('fats_g'),
                'fiber_g': meal_data.get('fiber_g'),
                'ingredients': meal_data.get('ingredients', []),
                'instructions': meal_data.get('instructions', []),
                'ai_generated': True,
                'tags': meal_data.get('tags', [])
            }
            
            result = self.supabase.table('recipes').insert(recipe).execute()
            return result.data[0]['id'] if result.data else None
            
        except Exception as e:
            logger.error(f"Error creating recipe: {str(e)}")
            return None
    
    def _create_shopping_list(self, meal_plan_id: str, shopping_list_data: Dict[str, Any], total_cost: float):
        """Create shopping list for meal plan"""
        try:
            # Organize items by category
            organized_items = []
            for category, items in shopping_list_data.items():
                if isinstance(items, list):
                    for item in items:
                        organized_items.append({
                            'category': category,
                            'name': item.get('name'),
                            'amount': item.get('amount'),
                            'unit': item.get('unit'),
                            'estimated_cost': item.get('estimated_cost', 0)
                        })
            
            shopping_list = {
                'meal_plan_id': meal_plan_id,
                'items': organized_items,
                'estimated_cost': total_cost
            }
            
            self.supabase.table('shopping_lists').insert(shopping_list).execute()
            
        except Exception as e:
            logger.error(f"Error creating shopping list: {str(e)}")
    
    def _organize_meal_plan_by_day(self, meal_plan: Dict[str, Any], meals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Organize meal plan data by day"""
        organized = {
            'id': meal_plan['id'],
            'name': meal_plan['name'],
            'start_date': meal_plan['start_date'],
            'end_date': meal_plan['end_date'],
            'status': meal_plan['status'],
            'dietary_requirements': meal_plan['dietary_requirements'],
            'budget': meal_plan['budget'],
            'days': {}
        }
        
        # Group meals by day
        for meal in meals:
            day_key = f"day_{meal['day_number']}"
            if day_key not in organized['days']:
                organized['days'][day_key] = {
                    'day_number': meal['day_number'],
                    'meals': []
                }
            
            organized['days'][day_key]['meals'].append({
                'meal_type': meal['meal_type'],
                'recipe': meal['recipes'],
                'servings': meal['servings'],
                'customizations': meal['customizations']
            })
        
        return organized
    
    def _get_meal_order_index(self, meal_type: str) -> int:
        """Get order index for meal type"""
        order_map = {
            'breakfast': 1,
            'lunch': 2,
            'snack': 3,
            'dinner': 4
        }
        return order_map.get(meal_type, 5)
    
    def _create_demo_meal_plan(self, user_id: str, meal_plan_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a demo meal plan when database is not available"""
        import uuid
        meal_plan_id = str(uuid.uuid4())
        
        return {
            'success': True,
            'meal_plan_id': meal_plan_id,
            'data': {
                'id': meal_plan_id,
                'user_id': user_id,
                'name': meal_plan_data.get('name', 'Demo Meal Plan'),
                'status': 'draft',
                'demo_mode': True
            }
        }