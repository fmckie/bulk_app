# AI Recipe Storage Feature

## Overview
The meal prep feature now automatically saves all AI-generated recipes and ingredients to a Supabase database whenever a meal plan is generated. This enables recipe search, history tracking, and building a personalized recipe library.

## Database Schema

### Tables Created

1. **ai_generated_recipes**
   - Stores complete recipe information
   - Tracks nutrition, cooking times, difficulty
   - Supports tags and cuisine types
   - Includes rating system

2. **recipe_ingredients**
   - Stores ingredients for each recipe
   - Includes quantities, units, and categories
   - Supports optional ingredients

3. **user_meal_generation_history**
   - Tracks when users generate meal plans
   - Records dietary requirements and budget
   - Links to generated recipes

4. **recipe_ratings**
   - User ratings and feedback
   - Difficulty feedback
   - Would make again indicator

5. **user_recipe_collections**
   - Save recipes to collections (favorites, etc.)
   - User notes on recipes

## Automatic Saving Process

When a meal plan is generated:

1. AI generates the meal plan with recipes
2. Each recipe is automatically saved to `ai_generated_recipes`
3. Ingredients are parsed and saved to `recipe_ingredients`
4. Generation history is recorded
5. Recipe IDs are linked to the user

## New API Endpoints

### Search Recipes
```
GET /api/recipes/search
Query params:
- name: Recipe name (partial match)
- meal_type: breakfast/lunch/dinner/snack
- cuisine_type: mediterranean/asian/mexican/etc
- max_calories: Maximum calories
- min_protein: Minimum protein grams
- tags[]: Array of tags to match
- limit: Max results (default 20)
```

### Get Recipe Details
```
GET /api/recipes/<recipe_id>
Returns complete recipe with ingredients and instructions
```

### Add to Favorites
```
POST /api/recipes/<recipe_id>/favorite
Body: { "notes": "optional notes" }
```

### Generation History
```
GET /api/recipes/generation-history
Query params:
- limit: Max results (default 10)
```

## Features

### Auto-Save
- Enabled by default when generating meal plans
- Tracks recipe generation frequency
- Prevents duplicate recipes for same user

### Recipe Tags
- Automatically generated based on:
  - Nutrition content (high-protein, low-carb)
  - Prep time (quick recipes under 30 min)
  - Dietary preferences
  - Meal type

### Cuisine Detection
- Automatically detects cuisine type from recipe name
- Categories: Mediterranean, Asian, Mexican, American, Indian, Middle Eastern, International

### Search Capabilities
- Search by recipe name
- Filter by meal type
- Filter by cuisine
- Nutrition-based search
- Tag-based filtering

## Database Setup

1. Run the SQL script to create tables:
```bash
psql -h <supabase-host> -U postgres -d postgres -f database/meal_prep_tables.sql
```

2. Tables include:
   - Row Level Security (RLS) enabled
   - Automatic timestamp updates
   - Performance indexes
   - Data validation constraints

## Usage in Code

### Generate with Auto-Save
```python
# In meal generation request
user_data = {
    'user_id': user_id,
    'auto_save_recipes': True,  # Enable auto-save
    # ... other data
}
meal_plan = ai_service.generate_meal_plan(user_data)
```

### Search Saved Recipes
```python
# Search for high-protein Mediterranean recipes
recipes = RecipeStorageDB.search_recipes(
    supabase,
    user_id,
    {
        'cuisine_type': 'mediterranean',
        'min_protein': 30,
        'tags': ['meal-prep']
    }
)
```

### Get Recipe with Ingredients
```python
recipe = RecipeStorageDB.get_recipe_by_id(supabase, recipe_id)
# Returns recipe with ingredients[] array
```

## Benefits

1. **Recipe Library**: Build a personal collection of AI-generated recipes
2. **Avoid Repetition**: Track which recipes have been generated
3. **Search & Filter**: Find recipes based on various criteria
4. **Meal Prep Planning**: Access previously generated successful recipes
5. **Nutrition Tracking**: Search by nutritional requirements
6. **User Feedback**: Rate recipes and track favorites

## Privacy & Security

- Row Level Security ensures users can only access their own recipes
- Recipes can be marked as public for sharing (future feature)
- All data is isolated per user
- Secure authentication required for all endpoints

## Future Enhancements

1. **Recipe Sharing**: Allow users to share recipes publicly
2. **Community Ratings**: Aggregate ratings from multiple users
3. **Smart Recommendations**: Suggest recipes based on history
4. **Meal Plan Templates**: Save and reuse successful meal plans
5. **Shopping List Integration**: Generate shopping lists from saved recipes
6. **Recipe Variations**: Track modifications and variations of recipes