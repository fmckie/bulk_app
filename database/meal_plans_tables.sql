-- Missing Meal Plans Tables for Supabase
-- These tables are required for the meal prep save functionality

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Main meal plans table
CREATE TABLE IF NOT EXISTS meal_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    name VARCHAR(255) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    dietary_requirements TEXT[] DEFAULT '{}',
    budget DECIMAL(10,2),
    store_preference VARCHAR(100),
    ai_generated BOOLEAN DEFAULT true,
    total_cost DECIMAL(10,2),
    status VARCHAR(50) DEFAULT 'draft', -- draft, active, completed, archived
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Meal plan meals (links meal plans to specific meals/recipes)
CREATE TABLE IF NOT EXISTS meal_plan_meals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    meal_plan_id UUID REFERENCES meal_plans(id) ON DELETE CASCADE,
    recipe_id UUID REFERENCES ai_generated_recipes(id),
    day_number INTEGER NOT NULL CHECK (day_number >= 1 AND day_number <= 7),
    meal_type VARCHAR(50) NOT NULL, -- breakfast, lunch, dinner, snack
    order_index INTEGER DEFAULT 0,
    servings INTEGER DEFAULT 1,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Shopping lists for meal plans
CREATE TABLE IF NOT EXISTS shopping_lists (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    meal_plan_id UUID REFERENCES meal_plans(id) ON DELETE CASCADE,
    total_cost DECIMAL(10,2),
    items JSONB NOT NULL DEFAULT '{}', -- Structured shopping list data
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_meal_plans_user_id ON meal_plans(user_id);
CREATE INDEX idx_meal_plans_status ON meal_plans(status);
CREATE INDEX idx_meal_plans_dates ON meal_plans(start_date, end_date);
CREATE INDEX idx_meal_plan_meals_plan_id ON meal_plan_meals(meal_plan_id);
CREATE INDEX idx_meal_plan_meals_day ON meal_plan_meals(day_number);
CREATE INDEX idx_shopping_lists_plan_id ON shopping_lists(meal_plan_id);

-- Enable RLS
ALTER TABLE meal_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE meal_plan_meals ENABLE ROW LEVEL SECURITY;
ALTER TABLE shopping_lists ENABLE ROW LEVEL SECURITY;

-- RLS Policies for meal_plans
CREATE POLICY "Users can view their own meal plans" ON meal_plans
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own meal plans" ON meal_plans
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own meal plans" ON meal_plans
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own meal plans" ON meal_plans
    FOR DELETE USING (auth.uid() = user_id);

-- RLS Policies for meal_plan_meals
CREATE POLICY "Users can view meals for their plans" ON meal_plan_meals
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM meal_plans 
            WHERE meal_plans.id = meal_plan_meals.meal_plan_id 
            AND meal_plans.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can manage meals for their plans" ON meal_plan_meals
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM meal_plans 
            WHERE meal_plans.id = meal_plan_meals.meal_plan_id 
            AND meal_plans.user_id = auth.uid()
        )
    );

-- RLS Policies for shopping_lists
CREATE POLICY "Users can view shopping lists for their plans" ON shopping_lists
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM meal_plans 
            WHERE meal_plans.id = shopping_lists.meal_plan_id 
            AND meal_plans.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can manage shopping lists for their plans" ON shopping_lists
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM meal_plans 
            WHERE meal_plans.id = shopping_lists.meal_plan_id 
            AND meal_plans.user_id = auth.uid()
        )
    );

-- Update trigger for updated_at
CREATE TRIGGER update_meal_plans_updated_at 
    BEFORE UPDATE ON meal_plans 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_shopping_lists_updated_at 
    BEFORE UPDATE ON shopping_lists 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();