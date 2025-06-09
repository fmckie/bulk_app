-- Kinobody Greek God Program Database Schema

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table (extends Supabase Auth)
CREATE TABLE IF NOT EXISTS profiles (
    id UUID REFERENCES auth.users ON DELETE CASCADE PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    username TEXT UNIQUE,
    full_name TEXT,
    body_weight DECIMAL(5,2),
    body_fat_percentage DECIMAL(4,2),
    program_start_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Exercise library
CREATE TABLE IF NOT EXISTS exercises (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    category TEXT NOT NULL CHECK (category IN ('indicator', 'assistance')),
    muscle_group TEXT NOT NULL,
    instructions TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Workouts table
CREATE TABLE IF NOT EXISTS workouts (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
    date DATE NOT NULL,
    notes TEXT,
    duration_minutes INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, date)
);

-- Workout sets (for RPT tracking)
CREATE TABLE IF NOT EXISTS workout_sets (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    workout_id UUID REFERENCES workouts(id) ON DELETE CASCADE NOT NULL,
    exercise_id UUID REFERENCES exercises(id) NOT NULL,
    set_number INTEGER NOT NULL CHECK (set_number BETWEEN 1 AND 10),
    weight DECIMAL(6,2) NOT NULL,
    reps INTEGER NOT NULL CHECK (reps > 0),
    rpe DECIMAL(3,1) CHECK (rpe BETWEEN 0 AND 10), -- Rate of Perceived Exertion
    rest_seconds INTEGER,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(workout_id, exercise_id, set_number)
);

-- Personal records
CREATE TABLE IF NOT EXISTS personal_records (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
    exercise_id UUID REFERENCES exercises(id) NOT NULL,
    weight DECIMAL(6,2) NOT NULL,
    reps INTEGER NOT NULL,
    date_achieved DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, exercise_id)
);

-- Nutrition tracking
CREATE TABLE IF NOT EXISTS nutrition_logs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
    date DATE NOT NULL,
    calories INTEGER,
    protein_g DECIMAL(6,2),
    carbs_g DECIMAL(6,2),
    fats_g DECIMAL(6,2),
    notes TEXT,
    is_training_day BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, date)
);

-- Body measurements
CREATE TABLE IF NOT EXISTS measurements (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
    date DATE NOT NULL,
    weight DECIMAL(5,2),
    body_fat_percentage DECIMAL(4,2),
    waist_inches DECIMAL(4,2),
    chest_inches DECIMAL(4,2),
    arms_inches DECIMAL(4,2),
    shoulders_inches DECIMAL(4,2),
    neck_inches DECIMAL(4,2),
    thighs_inches DECIMAL(4,2),
    calves_inches DECIMAL(4,2),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, date)
);

-- Strength standards tracking
CREATE TABLE IF NOT EXISTS strength_levels (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
    exercise_id UUID REFERENCES exercises(id) NOT NULL,
    current_level TEXT CHECK (current_level IN ('beginner', 'good', 'great', 'godlike')),
    achieved_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, exercise_id)
);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add updated_at triggers
CREATE TRIGGER update_profiles_updated_at BEFORE UPDATE ON profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_workouts_updated_at BEFORE UPDATE ON workouts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_nutrition_logs_updated_at BEFORE UPDATE ON nutrition_logs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_strength_levels_updated_at BEFORE UPDATE ON strength_levels
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security (RLS) Policies
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE workouts ENABLE ROW LEVEL SECURITY;
ALTER TABLE workout_sets ENABLE ROW LEVEL SECURITY;
ALTER TABLE personal_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE nutrition_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE measurements ENABLE ROW LEVEL SECURITY;
ALTER TABLE strength_levels ENABLE ROW LEVEL SECURITY;

-- Profiles policies
CREATE POLICY "Users can view own profile" ON profiles
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON profiles
    FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Users can insert own profile" ON profiles
    FOR INSERT WITH CHECK (auth.uid() = id);

-- Workouts policies
CREATE POLICY "Users can view own workouts" ON workouts
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own workouts" ON workouts
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own workouts" ON workouts
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own workouts" ON workouts
    FOR DELETE USING (auth.uid() = user_id);

-- Workout sets policies (inherit from workout access)
CREATE POLICY "Users can view workout sets" ON workout_sets
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM workouts 
            WHERE workouts.id = workout_sets.workout_id 
            AND workouts.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert workout sets" ON workout_sets
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM workouts 
            WHERE workouts.id = workout_sets.workout_id 
            AND workouts.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can update workout sets" ON workout_sets
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM workouts 
            WHERE workouts.id = workout_sets.workout_id 
            AND workouts.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can delete workout sets" ON workout_sets
    FOR DELETE USING (
        EXISTS (
            SELECT 1 FROM workouts 
            WHERE workouts.id = workout_sets.workout_id 
            AND workouts.user_id = auth.uid()
        )
    );

-- Personal records policies
CREATE POLICY "Users can view own PRs" ON personal_records
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own PRs" ON personal_records
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own PRs" ON personal_records
    FOR UPDATE USING (auth.uid() = user_id);

-- Nutrition logs policies
CREATE POLICY "Users can view own nutrition" ON nutrition_logs
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own nutrition" ON nutrition_logs
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own nutrition" ON nutrition_logs
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own nutrition" ON nutrition_logs
    FOR DELETE USING (auth.uid() = user_id);

-- Measurements policies
CREATE POLICY "Users can view own measurements" ON measurements
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own measurements" ON measurements
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own measurements" ON measurements
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own measurements" ON measurements
    FOR DELETE USING (auth.uid() = user_id);

-- Strength levels policies
CREATE POLICY "Users can view own strength levels" ON strength_levels
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own strength levels" ON strength_levels
    FOR ALL USING (auth.uid() = user_id);

-- Exercises are public read (no user-specific data)
CREATE POLICY "Everyone can view exercises" ON exercises
    FOR SELECT USING (true);

-- Insert initial exercise data
INSERT INTO exercises (name, slug, category, muscle_group, instructions) VALUES
-- Indicator Exercises
('Incline Barbell Bench Press', 'incline-bench', 'indicator', 'chest', 'Set bench to 30-45 degree incline. Grip bar slightly wider than shoulders. Lower to upper chest, press up powerfully.'),
('Standing Shoulder Press', 'standing-press', 'indicator', 'shoulders', 'Clean bar to shoulders or use a rack. Press overhead while maintaining tight core. Full lockout at top.'),
('Weighted Chin-ups', 'weighted-chins', 'indicator', 'back', 'Use weight belt or hold dumbbell between feet. Pull up until chin clears bar. Control the descent.'),
('Power Cleans (Hang)', 'power-cleans', 'indicator', 'legs', 'Start with bar at hip level. Explosively pull and catch in front rack position. Focus on hip drive.'),

-- Assistance Exercises
('Weighted Dips', 'weighted-dips', 'assistance', 'chest', 'Add weight with belt or hold between feet. Lean forward slightly for chest emphasis. Full range of motion.'),
('Close Grip Bench Press', 'close-grip-bench', 'assistance', 'triceps', 'Grip bar at shoulder width or narrower. Keep elbows tucked. Focus on tricep contraction.'),
('Skull Crushers', 'skull-crushers', 'assistance', 'triceps', 'Lower bar to forehead or behind head. Keep elbows stationary. Extend forcefully.'),
('Rope Extensions', 'rope-extensions', 'assistance', 'triceps', 'Cable rope attachment. Keep elbows at sides. Spread rope at bottom of movement.'),
('Barbell Curls', 'barbell-curls', 'assistance', 'biceps', 'Stand with feet hip-width. Keep elbows at sides. No swinging or momentum.'),
('Incline Dumbbell Curls', 'incline-db-curls', 'assistance', 'biceps', 'Set bench to 45-60 degrees. Let arms hang. Curl without rotating shoulders forward.'),
('Cable Rows', 'cable-rows', 'assistance', 'back', 'Seated or standing position. Pull to lower chest/upper abdomen. Squeeze shoulder blades together.'),
('Lateral Raises', 'lateral-raises', 'assistance', 'shoulders', 'Slight bend in elbows. Raise to parallel or slightly above. Control the weight.'),
('Bent Over Flyes', 'bent-over-flyes', 'assistance', 'shoulders', 'Hinge at hips, maintain flat back. Raise dumbbells out to sides. Focus on rear delts.'),
('Pistol Squats', 'pistol-squats', 'assistance', 'legs', 'Single leg squat with other leg extended. Use assistance if needed. Full depth.'),
('Single Leg Calf Raises', 'calf-raises', 'assistance', 'legs', 'Hold dumbbell in same hand as working leg. Full range of motion. Pause at top.')
ON CONFLICT (slug) DO NOTHING;

-- Create indexes for performance
CREATE INDEX idx_workouts_user_date ON workouts(user_id, date DESC);
CREATE INDEX idx_workout_sets_workout ON workout_sets(workout_id);
CREATE INDEX idx_personal_records_user_exercise ON personal_records(user_id, exercise_id);
CREATE INDEX idx_nutrition_logs_user_date ON nutrition_logs(user_id, date DESC);
CREATE INDEX idx_measurements_user_date ON measurements(user_id, date DESC);