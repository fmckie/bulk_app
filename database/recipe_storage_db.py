"""
Database module for storing AI-generated recipes and ingredients
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import uuid

logger = logging.getLogger(__name__)


class RecipeStorageDB:
    """Database operations for AI-generated recipes storage"""
    
    @staticmethod
    def save_ai_recipe(supabase_client, recipe_data: Dict[str, Any], user_id: str = None) -> Optional[str]:
        """
        Save an AI-generated recipe to the database
        
        Args:
            supabase_client: Supabase client instance
            recipe_data: Recipe data from AI generation
            user_id: User ID who generated the recipe
            
        Returns:
            Recipe ID if successful, None otherwise
        """
        try:
            # Prepare recipe data
            recipe = {
                'user_id': user_id,
                'name': recipe_data.get('name'),
                'description': recipe_data.get('description'),
                'meal_type': recipe_data.get('meal_type'),
                'cuisine_type': recipe_data.get('cuisine_type'),
                'prep_time': recipe_data.get('prep_time'),
                'cook_time': recipe_data.get('cook_time'),
                'servings': recipe_data.get('servings', 1),
                'difficulty': recipe_data.get('difficulty', 'medium'),
                'calories': recipe_data.get('calories'),
                'protein_g': recipe_data.get('protein_g'),
                'carbs_g': recipe_data.get('carbs_g'),
                'fats_g': recipe_data.get('fats_g'),
                'fiber_g': recipe_data.get('fiber_g'),
                'instructions': json.dumps(recipe_data.get('instructions', [])) if isinstance(recipe_data.get('instructions'), list) else recipe_data.get('instructions'),
                'tips': recipe_data.get('tips'),
                'tags': recipe_data.get('tags', []),
                'source': 'ai_generated'
            }
            
            # Remove None values
            recipe = {k: v for k, v in recipe.items() if v is not None}
            
            # Check if recipe already exists (by name and user)
            if user_id:
                existing = supabase_client.table('ai_generated_recipes')\
                    .select('id, times_generated')\
                    .eq('name', recipe['name'])\
                    .eq('user_id', user_id)\
                    .execute()
                
                if existing.data:
                    # Update times_generated counter
                    recipe_id = existing.data[0]['id']
                    times_generated = existing.data[0]['times_generated'] + 1
                    
                    supabase_client.table('ai_generated_recipes')\
                        .update({'times_generated': times_generated})\
                        .eq('id', recipe_id)\
                        .execute()
                    
                    logger.info(f"Recipe '{recipe['name']}' already exists, updated generation count to {times_generated}")
                    return recipe_id
            
            # Insert new recipe
            result = supabase_client.table('ai_generated_recipes').insert(recipe).execute()
            
            if result.data:
                recipe_id = result.data[0]['id']
                logger.info(f"Saved recipe '{recipe['name']}' with ID: {recipe_id}")
                return recipe_id
            else:
                logger.error("Failed to save recipe - no data returned")
                return None
                
        except Exception as e:
            logger.error(f"Error saving AI recipe: {str(e)}")
            return None
    
    @staticmethod
    def save_recipe_ingredients(supabase_client, recipe_id: str, ingredients: List[Dict[str, Any]]) -> bool:
        """
        Save ingredients for a recipe
        
        Args:
            supabase_client: Supabase client instance
            recipe_id: Recipe ID
            ingredients: List of ingredient dictionaries
            
        Returns:
            Success boolean
        """
        try:
            # Prepare ingredients data
            ingredients_data = []
            for ingredient in ingredients:
                if isinstance(ingredient, dict):
                    ingredient_data = {
                        'recipe_id': recipe_id,
                        'name': ingredient.get('name') or ingredient.get('item'),
                        'quantity': ingredient.get('quantity') or ingredient.get('amount'),
                        'unit': ingredient.get('unit'),
                        'category': ingredient.get('category'),
                        'notes': ingredient.get('notes'),
                        'is_optional': ingredient.get('is_optional', False)
                    }
                elif isinstance(ingredient, str):
                    # Parse string ingredients (e.g., "2 cups rice")
                    parts = ingredient.split(' ', 2)
                    ingredient_data = {
                        'recipe_id': recipe_id,
                        'name': parts[-1] if len(parts) > 1 else ingredient,
                        'quantity': float(parts[0]) if len(parts) > 1 and parts[0].replace('.', '').isdigit() else None,
                        'unit': parts[1] if len(parts) > 2 else None
                    }
                else:
                    continue
                
                # Remove None values
                ingredient_data = {k: v for k, v in ingredient_data.items() if v is not None}
                ingredients_data.append(ingredient_data)
            
            if ingredients_data:
                result = supabase_client.table('recipe_ingredients').insert(ingredients_data).execute()
                logger.info(f"Saved {len(ingredients_data)} ingredients for recipe {recipe_id}")
                return bool(result.data)
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving recipe ingredients: {str(e)}")
            return False
    
    @staticmethod
    def save_generation_history(supabase_client, user_id: str, meal_plan_data: Dict[str, Any], 
                              recipe_ids: List[str], generation_time_ms: int = None) -> Optional[str]:
        """
        Save meal generation history
        
        Args:
            supabase_client: Supabase client instance
            user_id: User ID
            meal_plan_data: Complete meal plan data
            recipe_ids: List of generated recipe IDs
            generation_time_ms: Time taken to generate in milliseconds
            
        Returns:
            History ID if successful, None otherwise
        """
        try:
            history_data = {
                'user_id': user_id,
                'generation_type': '7_day' if 'day_7' in str(meal_plan_data) else 'single_day',
                'dietary_requirements': meal_plan_data.get('dietary_requirements', []),
                'budget': meal_plan_data.get('budget'),
                'recipe_ids': recipe_ids,
                'total_recipes': len(recipe_ids),
                'metadata': json.dumps({
                    'store_preference': meal_plan_data.get('store_preference'),
                    'training_days': meal_plan_data.get('training_days', []),
                    'total_cost': meal_plan_data.get('total_estimated_cost')
                }),
                'ai_model': 'gpt-3.5-turbo',
                'generation_time_ms': generation_time_ms
            }
            
            result = supabase_client.table('user_meal_generation_history').insert(history_data).execute()
            
            if result.data:
                history_id = result.data[0]['id']
                logger.info(f"Saved generation history with ID: {history_id}")
                return history_id
            
            return None
            
        except Exception as e:
            logger.error(f"Error saving generation history: {str(e)}")
            return None
    
    @staticmethod
    def get_recipe_by_id(supabase_client, recipe_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a recipe by ID with all ingredients
        
        Args:
            supabase_client: Supabase client instance
            recipe_id: Recipe ID
            
        Returns:
            Recipe data with ingredients or None
        """
        try:
            # Get recipe
            recipe_result = supabase_client.table('ai_generated_recipes')\
                .select('*')\
                .eq('id', recipe_id)\
                .single()\
                .execute()
            
            if not recipe_result.data:
                return None
            
            recipe = recipe_result.data
            
            # Get ingredients
            ingredients_result = supabase_client.table('recipe_ingredients')\
                .select('*')\
                .eq('recipe_id', recipe_id)\
                .order('created_at')\
                .execute()
            
            recipe['ingredients'] = ingredients_result.data if ingredients_result.data else []
            
            # Parse instructions if stored as JSON string
            if recipe.get('instructions') and isinstance(recipe['instructions'], str):
                try:
                    recipe['instructions'] = json.loads(recipe['instructions'])
                except:
                    pass
            
            return recipe
            
        except Exception as e:
            logger.error(f"Error getting recipe: {str(e)}")
            return None
    
    @staticmethod
    def search_recipes(supabase_client, user_id: str = None, search_params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Search for recipes based on various parameters
        
        Args:
            supabase_client: Supabase client instance
            user_id: User ID to filter by (optional)
            search_params: Dictionary with search parameters
                - name: Recipe name (partial match)
                - meal_type: Meal type filter
                - cuisine_type: Cuisine type filter
                - max_calories: Maximum calories
                - min_protein: Minimum protein
                - tags: List of tags to match
                - ingredient: Ingredient to search for
                
        Returns:
            List of matching recipes
        """
        try:
            query = supabase_client.table('ai_generated_recipes').select('*')
            
            # Apply filters
            if user_id:
                query = query.eq('user_id', user_id)
            
            if search_params:
                if search_params.get('name'):
                    query = query.ilike('name', f"%{search_params['name']}%")
                
                if search_params.get('meal_type'):
                    query = query.eq('meal_type', search_params['meal_type'])
                
                if search_params.get('cuisine_type'):
                    query = query.eq('cuisine_type', search_params['cuisine_type'])
                
                if search_params.get('max_calories'):
                    query = query.lte('calories', search_params['max_calories'])
                
                if search_params.get('min_protein'):
                    query = query.gte('protein_g', search_params['min_protein'])
                
                if search_params.get('tags'):
                    # Search for recipes containing any of the specified tags
                    query = query.contains('tags', search_params['tags'])
            
            # Order by creation date (newest first)
            query = query.order('created_at', desc=True)
            
            # Limit results
            query = query.limit(search_params.get('limit', 50) if search_params else 50)
            
            result = query.execute()
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error searching recipes: {str(e)}")
            return []
    
    @staticmethod
    def get_user_generation_history(supabase_client, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get user's meal generation history
        
        Args:
            supabase_client: Supabase client instance
            user_id: User ID
            limit: Maximum number of records to return
            
        Returns:
            List of generation history records
        """
        try:
            result = supabase_client.table('user_meal_generation_history')\
                .select('*')\
                .eq('user_id', user_id)\
                .order('generation_date', desc=True)\
                .limit(limit)\
                .execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error getting generation history: {str(e)}")
            return []
    
    @staticmethod
    def add_recipe_to_collection(supabase_client, user_id: str, recipe_id: str, 
                               collection_name: str = 'favorites', notes: str = None) -> bool:
        """
        Add a recipe to user's collection (e.g., favorites)
        
        Args:
            supabase_client: Supabase client instance
            user_id: User ID
            recipe_id: Recipe ID
            collection_name: Name of the collection
            notes: Optional notes
            
        Returns:
            Success boolean
        """
        try:
            collection_data = {
                'user_id': user_id,
                'recipe_id': recipe_id,
                'collection_name': collection_name,
                'notes': notes
            }
            
            result = supabase_client.table('user_recipe_collections').insert(collection_data).execute()
            return bool(result.data)
            
        except Exception as e:
            # Check if it's a unique constraint violation (already in collection)
            if 'duplicate key' in str(e).lower():
                logger.info(f"Recipe {recipe_id} already in {collection_name} collection")
                return True
            logger.error(f"Error adding recipe to collection: {str(e)}")
            return False