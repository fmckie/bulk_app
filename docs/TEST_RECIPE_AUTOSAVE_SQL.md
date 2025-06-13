# SQL Commands for Testing Recipe Auto-Save

## Quick Test Setup

Run these SQL commands in your Supabase SQL Editor to enable testing:

### Option 1: Create Test Policy (Recommended)

This creates a temporary policy that allows the test user to save recipes:

```sql
-- Create a test policy for specific user
CREATE POLICY "test_user_policy" 
ON ai_generated_recipes
FOR ALL 
USING (user_id = 'cd6377de-f0bd-4ffc-a2d0-596aad21adfe')
WITH CHECK (user_id = 'cd6377de-f0bd-4ffc-a2d0-596aad21adfe');

-- Also for ingredients table
CREATE POLICY "test_user_policy" 
ON recipe_ingredients
FOR ALL 
USING (recipe_id IN (
    SELECT id FROM ai_generated_recipes 
    WHERE user_id = 'cd6377de-f0bd-4ffc-a2d0-596aad21adfe'
))
WITH CHECK (true);

-- And for generation history
CREATE POLICY "test_user_policy" 
ON user_meal_generation_history
FOR ALL 
USING (user_id = 'cd6377de-f0bd-4ffc-a2d0-596aad21adfe')
WITH CHECK (user_id = 'cd6377de-f0bd-4ffc-a2d0-596aad21adfe');
```

### Option 2: Confirm Test User Email

Go to Supabase Dashboard > Authentication > Users and manually confirm the email for:
- Email: testuser20250613135340@gmail.com
- User ID: cd6377de-f0bd-4ffc-a2d0-596aad21adfe

Then the authenticated test will work.

### Option 3: Create Public Insert Policy (Less Secure)

This allows any authenticated user to insert recipes:

```sql
-- Allow any authenticated user to insert (DEV ONLY!)
CREATE POLICY "authenticated_insert" 
ON ai_generated_recipes
FOR INSERT 
TO authenticated
WITH CHECK (auth.uid()::text = user_id::text OR user_id IS NOT NULL);

CREATE POLICY "authenticated_insert" 
ON recipe_ingredients
FOR INSERT 
TO authenticated
WITH CHECK (true);
```

## After Testing - Cleanup

### Remove Test Policies

```sql
-- Remove test policies
DROP POLICY IF EXISTS "test_user_policy" ON ai_generated_recipes;
DROP POLICY IF EXISTS "test_user_policy" ON recipe_ingredients;
DROP POLICY IF EXISTS "test_user_policy" ON user_meal_generation_history;
DROP POLICY IF EXISTS "authenticated_insert" ON ai_generated_recipes;
DROP POLICY IF EXISTS "authenticated_insert" ON recipe_ingredients;
```

### Delete Test Data

```sql
-- Delete test recipes
DELETE FROM ai_generated_recipes 
WHERE user_id = 'cd6377de-f0bd-4ffc-a2d0-596aad21adfe';

-- Delete test user (optional)
DELETE FROM auth.users 
WHERE id = 'cd6377de-f0bd-4ffc-a2d0-596aad21adfe';
```

## Check Current Policies

```sql
-- View current RLS policies
SELECT 
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual,
    with_check
FROM pg_policies 
WHERE tablename IN ('ai_generated_recipes', 'recipe_ingredients')
ORDER BY tablename, policyname;
```

## Test Query

After setting up policies, verify they work:

```sql
-- This should return empty (no recipes yet)
SELECT * FROM ai_generated_recipes 
WHERE user_id = 'cd6377de-f0bd-4ffc-a2d0-596aad21adfe';

-- After running the test, this should show saved recipes
SELECT 
    r.name,
    r.calories,
    r.protein_g,
    COUNT(i.id) as ingredient_count
FROM ai_generated_recipes r
LEFT JOIN recipe_ingredients i ON r.id = i.recipe_id
WHERE r.user_id = 'cd6377de-f0bd-4ffc-a2d0-596aad21adfe'
GROUP BY r.id, r.name, r.calories, r.protein_g
ORDER BY r.created_at DESC;
```