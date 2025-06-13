-- Meal Prep Recipe Storage Tables for Supabase
-- This file creates tables to automatically store all AI-generated recipes and ingredients

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- AI Generated Recipes Table
CREATE TABLE IF NOT EXISTS ai_generated_recipes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    meal_type VARCHAR(50), -- breakfast, lunch, dinner, snack
    cuisine_type VARCHAR(100),
    prep_time INTEGER, -- in minutes
    cook_time INTEGER, -- in minutes
    total_time INTEGER GENERATED ALWAYS AS (prep_time + cook_time) STORED,
    servings INTEGER DEFAULT 1,
    difficulty VARCHAR(50), -- easy, medium, hard
    calories INTEGER,
    protein_g DECIMAL(10,2),
    carbs_g DECIMAL(10,2),
    fats_g DECIMAL(10,2),
    fiber_g DECIMAL(10,2),
    instructions JSONB, -- Array of instruction steps
    tips TEXT,
    tags TEXT[], -- Array of tags like 'vegetarian', 'high-protein', etc.
    image_url TEXT,
    source VARCHAR(50) DEFAULT 'ai_generated', -- ai_generated, user_created, external
    is_public BOOLEAN DEFAULT false,
    times_generated INTEGER DEFAULT 1, -- Track how often this recipe is generated
    average_rating DECIMAL(3,2) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Recipe Ingredients Table
CREATE TABLE IF NOT EXISTS recipe_ingredients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    recipe_id UUID REFERENCES ai_generated_recipes(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    quantity DECIMAL(10,2),
    unit VARCHAR(50), -- cup, tbsp, oz, g, etc.
    category VARCHAR(100), -- produce, meat, dairy, pantry, etc.
    notes TEXT, -- e.g., "diced", "optional", "or substitute with..."
    is_optional BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User Meal Generation History
CREATE TABLE IF NOT EXISTS user_meal_generation_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id),
    meal_plan_id UUID, -- Reference to meal_plans table if exists
    generation_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    generation_type VARCHAR(50), -- '7_day', 'single_day', 'custom'
    dietary_requirements TEXT[],
    budget DECIMAL(10,2),
    recipe_ids UUID[], -- Array of recipe IDs generated
    total_recipes INTEGER,
    metadata JSONB, -- Store additional data like preferences, excluded ingredients
    ai_model VARCHAR(50), -- Track which AI model was used
    generation_time_ms INTEGER -- Track generation performance
);

-- Recipe Ratings and Feedback
CREATE TABLE IF NOT EXISTS recipe_ratings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    recipe_id UUID REFERENCES ai_generated_recipes(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id),
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    feedback TEXT,
    would_make_again BOOLEAN,
    difficulty_feedback VARCHAR(50), -- easier_than_expected, as_expected, harder_than_expected
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(recipe_id, user_id) -- One rating per user per recipe
);

-- Recipe Collections (for saving favorites)
CREATE TABLE IF NOT EXISTS user_recipe_collections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id),
    recipe_id UUID REFERENCES ai_generated_recipes(id) ON DELETE CASCADE,
    collection_name VARCHAR(100) DEFAULT 'favorites',
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, recipe_id, collection_name)
);

-- Create indexes for better performance
CREATE INDEX idx_recipes_user_id ON ai_generated_recipes(user_id);
CREATE INDEX idx_recipes_meal_type ON ai_generated_recipes(meal_type);
CREATE INDEX idx_recipes_cuisine_type ON ai_generated_recipes(cuisine_type);
CREATE INDEX idx_recipes_tags ON ai_generated_recipes USING GIN(tags);
CREATE INDEX idx_recipes_created_at ON ai_generated_recipes(created_at DESC);
CREATE INDEX idx_ingredients_recipe_id ON recipe_ingredients(recipe_id);
CREATE INDEX idx_ingredients_category ON recipe_ingredients(category);
CREATE INDEX idx_generation_history_user_id ON user_meal_generation_history(user_id);
CREATE INDEX idx_generation_history_date ON user_meal_generation_history(generation_date DESC);

-- Create update trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_ai_generated_recipes_updated_at 
    BEFORE UPDATE ON ai_generated_recipes 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security Policies
ALTER TABLE ai_generated_recipes ENABLE ROW LEVEL SECURITY;
ALTER TABLE recipe_ingredients ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_meal_generation_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE recipe_ratings ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_recipe_collections ENABLE ROW LEVEL SECURITY;

-- Policies for ai_generated_recipes
CREATE POLICY "Users can view their own recipes" ON ai_generated_recipes
    FOR SELECT USING (auth.uid() = user_id OR is_public = true);

CREATE POLICY "Users can insert their own recipes" ON ai_generated_recipes
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own recipes" ON ai_generated_recipes
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own recipes" ON ai_generated_recipes
    FOR DELETE USING (auth.uid() = user_id);

-- Policies for recipe_ingredients
CREATE POLICY "Users can view ingredients for accessible recipes" ON recipe_ingredients
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM ai_generated_recipes 
            WHERE ai_generated_recipes.id = recipe_ingredients.recipe_id 
            AND (ai_generated_recipes.user_id = auth.uid() OR ai_generated_recipes.is_public = true)
        )
    );

CREATE POLICY "Users can manage ingredients for their recipes" ON recipe_ingredients
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM ai_generated_recipes 
            WHERE ai_generated_recipes.id = recipe_ingredients.recipe_id 
            AND ai_generated_recipes.user_id = auth.uid()
        )
    );

-- Policies for user_meal_generation_history
CREATE POLICY "Users can view their own generation history" ON user_meal_generation_history
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own generation history" ON user_meal_generation_history
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Policies for recipe_ratings
CREATE POLICY "Users can view all ratings" ON recipe_ratings
    FOR SELECT USING (true);

CREATE POLICY "Users can manage their own ratings" ON recipe_ratings
    FOR ALL USING (auth.uid() = user_id);

-- Policies for user_recipe_collections
CREATE POLICY "Users can manage their own collections" ON user_recipe_collections
    FOR ALL USING (auth.uid() = user_id);

-- Function to update recipe average rating
CREATE OR REPLACE FUNCTION update_recipe_average_rating()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE ai_generated_recipes
    SET average_rating = (
        SELECT AVG(rating)::DECIMAL(3,2)
        FROM recipe_ratings
        WHERE recipe_id = COALESCE(NEW.recipe_id, OLD.recipe_id)
    )
    WHERE id = COALESCE(NEW.recipe_id, OLD.recipe_id);
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_recipe_rating_on_insert
    AFTER INSERT ON recipe_ratings
    FOR EACH ROW EXECUTE FUNCTION update_recipe_average_rating();

CREATE TRIGGER update_recipe_rating_on_update
    AFTER UPDATE ON recipe_ratings
    FOR EACH ROW EXECUTE FUNCTION update_recipe_average_rating();

CREATE TRIGGER update_recipe_rating_on_delete
    AFTER DELETE ON recipe_ratings
    FOR EACH ROW EXECUTE FUNCTION update_recipe_average_rating();