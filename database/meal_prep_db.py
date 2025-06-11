"""
Database operations for meal prep functionality
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class MealPrepDB:
    """Database operations for meal prep feature"""
    
    def __init__(self, supabase_client):
        """Initialize with Supabase client"""
        self.supabase = supabase_client
    
    # Meal Plan Operations
    def create_meal_plan(self, user_id: str, meal_plan_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new meal plan"""
        try:
            result = self.supabase.table('meal_plans').insert({
                'user_id': user_id,
                **meal_plan_data
            }).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error creating meal plan: {str(e)}")
            return None
    
    def get_meal_plan(self, meal_plan_id: str) -> Optional[Dict[str, Any]]:
        """Get a meal plan by ID"""
        try:
            result = self.supabase.table('meal_plans')\
                .select('*')\
                .eq('id', meal_plan_id)\
                .single()\
                .execute()
            return result.data
        except Exception as e:
            logger.error(f"Error getting meal plan: {str(e)}")
            return None
    
    def get_user_meal_plans(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get all meal plans for a user"""
        try:
            result = self.supabase.table('meal_plans')\
                .select('*')\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)\
                .limit(limit)\
                .execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error getting user meal plans: {str(e)}")
            return []
    
    def update_meal_plan(self, meal_plan_id: str, updates: Dict[str, Any]) -> bool:
        """Update a meal plan"""
        try:
            result = self.supabase.table('meal_plans')\
                .update(updates)\
                .eq('id', meal_plan_id)\
                .execute()
            return bool(result.data)
        except Exception as e:
            logger.error(f"Error updating meal plan: {str(e)}")
            return False
    
    def delete_meal_plan(self, meal_plan_id: str) -> bool:
        """Delete a meal plan"""
        try:
            result = self.supabase.table('meal_plans')\
                .delete()\
                .eq('id', meal_plan_id)\
                .execute()
            return True
        except Exception as e:
            logger.error(f"Error deleting meal plan: {str(e)}")
            return False
    
    # Recipe Operations
    def create_recipe(self, recipe_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new recipe"""
        try:
            result = self.supabase.table('recipes').insert(recipe_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error creating recipe: {str(e)}")
            return None
    
    def get_recipe(self, recipe_id: str) -> Optional[Dict[str, Any]]:
        """Get a recipe by ID"""
        try:
            result = self.supabase.table('recipes')\
                .select('*')\
                .eq('id', recipe_id)\
                .single()\
                .execute()
            return result.data
        except Exception as e:
            logger.error(f"Error getting recipe: {str(e)}")
            return None
    
    def search_recipes(self, query: str = "", filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Search recipes with optional filters"""
        try:
            q = self.supabase.table('recipes').select('*')
            
            if query:
                q = q.ilike('name', f'%{query}%')
            
            if filters:
                if 'meal_type' in filters:
                    q = q.eq('meal_type', filters['meal_type'])
                if 'max_calories' in filters:
                    q = q.lte('calories', filters['max_calories'])
                if 'min_protein' in filters:
                    q = q.gte('protein_g', filters['min_protein'])
                if 'tags' in filters and filters['tags']:
                    # Filter by tags (JSONB contains)
                    for tag in filters['tags']:
                        q = q.contains('tags', [tag])
            
            result = q.order('created_at', desc=True).execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error searching recipes: {str(e)}")
            return []
    
    def update_recipe(self, recipe_id: str, updates: Dict[str, Any]) -> bool:
        """Update a recipe"""
        try:
            result = self.supabase.table('recipes')\
                .update(updates)\
                .eq('id', recipe_id)\
                .execute()
            return bool(result.data)
        except Exception as e:
            logger.error(f"Error updating recipe: {str(e)}")
            return False
    
    # Meal Plan Meals Operations
    def add_meal_to_plan(self, meal_plan_id: str, recipe_id: str, day_number: int, 
                        meal_type: str, servings: float = 1.0) -> Optional[Dict[str, Any]]:
        """Add a meal to a meal plan"""
        try:
            result = self.supabase.table('meal_plan_meals').insert({
                'meal_plan_id': meal_plan_id,
                'recipe_id': recipe_id,
                'day_number': day_number,
                'meal_type': meal_type,
                'servings': servings
            }).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error adding meal to plan: {str(e)}")
            return None
    
    def get_meal_plan_meals(self, meal_plan_id: str) -> List[Dict[str, Any]]:
        """Get all meals for a meal plan with recipe details"""
        try:
            result = self.supabase.table('meal_plan_meals')\
                .select('*, recipes(*)')\
                .eq('meal_plan_id', meal_plan_id)\
                .order('day_number')\
                .order('order_index')\
                .execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error getting meal plan meals: {str(e)}")
            return []
    
    def update_meal_in_plan(self, meal_id: str, updates: Dict[str, Any]) -> bool:
        """Update a meal in a meal plan"""
        try:
            result = self.supabase.table('meal_plan_meals')\
                .update(updates)\
                .eq('id', meal_id)\
                .execute()
            return bool(result.data)
        except Exception as e:
            logger.error(f"Error updating meal in plan: {str(e)}")
            return False
    
    def remove_meal_from_plan(self, meal_id: str) -> bool:
        """Remove a meal from a meal plan"""
        try:
            result = self.supabase.table('meal_plan_meals')\
                .delete()\
                .eq('id', meal_id)\
                .execute()
            return True
        except Exception as e:
            logger.error(f"Error removing meal from plan: {str(e)}")
            return False
    
    # Shopping List Operations
    def create_shopping_list(self, meal_plan_id: str, items: List[Dict[str, Any]], 
                           estimated_cost: float) -> Optional[Dict[str, Any]]:
        """Create a shopping list for a meal plan"""
        try:
            result = self.supabase.table('shopping_lists').insert({
                'meal_plan_id': meal_plan_id,
                'items': items,
                'estimated_cost': estimated_cost
            }).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error creating shopping list: {str(e)}")
            return None
    
    def get_shopping_list(self, meal_plan_id: str) -> Optional[Dict[str, Any]]:
        """Get shopping list for a meal plan"""
        try:
            result = self.supabase.table('shopping_lists')\
                .select('*')\
                .eq('meal_plan_id', meal_plan_id)\
                .single()\
                .execute()
            return result.data
        except Exception as e:
            logger.error(f"Error getting shopping list: {str(e)}")
            return None
    
    def update_shopping_list(self, shopping_list_id: str, updates: Dict[str, Any]) -> bool:
        """Update a shopping list"""
        try:
            result = self.supabase.table('shopping_lists')\
                .update(updates)\
                .eq('id', shopping_list_id)\
                .execute()
            return bool(result.data)
        except Exception as e:
            logger.error(f"Error updating shopping list: {str(e)}")
            return False
    
    # User Preferences Operations
    def get_user_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user meal preferences"""
        try:
            result = self.supabase.table('user_meal_preferences')\
                .select('*')\
                .eq('user_id', user_id)\
                .single()\
                .execute()
            return result.data
        except Exception as e:
            logger.error(f"Error getting user preferences: {str(e)}")
            return None
    
    def save_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """Save or update user meal preferences"""
        try:
            # Check if preferences exist
            existing = self.get_user_preferences(user_id)
            
            if existing:
                # Update existing
                result = self.supabase.table('user_meal_preferences')\
                    .update(preferences)\
                    .eq('user_id', user_id)\
                    .execute()
            else:
                # Create new
                preferences['user_id'] = user_id
                result = self.supabase.table('user_meal_preferences')\
                    .insert(preferences)\
                    .execute()
            
            return bool(result.data)
        except Exception as e:
            logger.error(f"Error saving user preferences: {str(e)}")
            return False
    
    def add_recipe_rating(self, user_id: str, recipe_id: str, rating: int, 
                         comments: str = "") -> bool:
        """Add or update a recipe rating"""
        try:
            preferences = self.get_user_preferences(user_id)
            if not preferences:
                preferences = {'user_id': user_id, 'meal_feedback': []}
            
            feedback = preferences.get('meal_feedback', [])
            
            # Add new feedback
            feedback.append({
                'recipe_id': recipe_id,
                'rating': rating,
                'comments': comments,
                'date': datetime.now().isoformat()
            })
            
            # Update liked/disliked lists based on rating
            if rating >= 4:
                liked = preferences.get('liked_recipes', [])
                if recipe_id not in liked:
                    liked.append(recipe_id)
                preferences['liked_recipes'] = liked
            elif rating <= 2:
                disliked = preferences.get('disliked_recipes', [])
                if recipe_id not in disliked:
                    disliked.append(recipe_id)
                preferences['disliked_recipes'] = disliked
            
            preferences['meal_feedback'] = feedback
            
            return self.save_user_preferences(user_id, preferences)
        except Exception as e:
            logger.error(f"Error adding recipe rating: {str(e)}")
            return False


# Static methods for use when Supabase is not initialized
class MealPrepDBStatic:
    """Static database operations for meal prep when used without instance"""
    
    @staticmethod
    def create_meal_plan(supabase, user_id: str, meal_plan_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new meal plan using provided Supabase client"""
        db = MealPrepDB(supabase)
        return db.create_meal_plan(user_id, meal_plan_data)
    
    @staticmethod
    def get_meal_plan(supabase, meal_plan_id: str) -> Optional[Dict[str, Any]]:
        """Get a meal plan by ID using provided Supabase client"""
        db = MealPrepDB(supabase)
        return db.get_meal_plan(meal_plan_id)
    
    @staticmethod
    def get_user_meal_plans(supabase, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get user meal plans using provided Supabase client"""
        db = MealPrepDB(supabase)
        return db.get_user_meal_plans(user_id, limit)
    
    @staticmethod
    def get_user_preferences(supabase, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user preferences using provided Supabase client"""
        db = MealPrepDB(supabase)
        return db.get_user_preferences(user_id)
    
    @staticmethod
    def save_user_preferences(supabase, user_id: str, preferences: Dict[str, Any]) -> bool:
        """Save user preferences using provided Supabase client"""
        db = MealPrepDB(supabase)
        return db.save_user_preferences(user_id, preferences)