"""
Database migration runner
"""
import os
import logging
from typing import List, Dict
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class MigrationRunner:
    """Handles database migrations"""
    
    def __init__(self, migrations_dir: str = None):
        self.migrations_dir = Path(migrations_dir or 'migrations')
        
    def get_migration_files(self) -> List[Dict]:
        """Get all migration files sorted by timestamp"""
        migrations = []
        
        for file in self.migrations_dir.glob('*.sql'):
            if file.name == 'migration_runner.py':
                continue
                
            # Parse filename: YYYYMMDD_HHMMSS_description.sql
            parts = file.stem.split('_', 2)
            if len(parts) >= 2:
                timestamp = f"{parts[0]}_{parts[1]}"
                name = file.stem
                
                with open(file, 'r') as f:
                    content = f.read()
                
                migrations.append({
                    'name': name,
                    'timestamp': timestamp,
                    'file': str(file),
                    'content': content
                })
        
        # Sort by timestamp
        migrations.sort(key=lambda x: x['timestamp'])
        return migrations
    
    async def apply_migrations(self, supabase_mcp, dry_run: bool = False):
        """Apply pending migrations"""
        # Get applied migrations from database
        applied = await supabase_mcp.list_migrations()
        applied_names = {m['name'] for m in applied}
        
        # Get pending migrations
        all_migrations = self.get_migration_files()
        pending = [m for m in all_migrations if m['name'] not in applied_names]
        
        if not pending:
            logger.info("No pending migrations")
            return 0
        
        logger.info(f"Found {len(pending)} pending migrations")
        
        # Apply each migration
        for migration in pending:
            logger.info(f"Applying migration: {migration['name']}")
            
            if not dry_run:
                try:
                    await supabase_mcp.apply_migration(
                        migration['name'],
                        migration['content']
                    )
                    logger.info(f"Successfully applied: {migration['name']}")
                except Exception as e:
                    logger.error(f"Failed to apply {migration['name']}: {e}")
                    raise
            else:
                logger.info(f"[DRY RUN] Would apply: {migration['name']}")
        
        return len(pending)
    
    def create_migration(self, name: str, content: str) -> str:
        """Create new migration file"""
        # Generate timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Clean name
        clean_name = name.lower().replace(' ', '_').replace('-', '_')
        
        # Create filename
        filename = f"{timestamp}_{clean_name}.sql"
        filepath = self.migrations_dir / filename
        
        # Write migration
        with open(filepath, 'w') as f:
            f.write(f"-- Migration: {name}\n")
            f.write(f"-- Created: {datetime.now().isoformat()}\n\n")
            f.write(content)
        
        logger.info(f"Created migration: {filename}")
        return str(filepath)


# Example migration creation
def create_initial_schema_migration():
    """Create initial schema migration"""
    runner = MigrationRunner()
    
    content = """
-- Create initial schema for Kinobody Tracker

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table (extends Supabase auth.users)
CREATE TABLE IF NOT EXISTS public.user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    username TEXT UNIQUE,
    full_name TEXT,
    avatar_url TEXT,
    program_type TEXT DEFAULT 'greek_god',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW())
);

-- Workouts table
CREATE TABLE IF NOT EXISTS public.workouts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    workout_type TEXT NOT NULL,
    duration_minutes INTEGER,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
    UNIQUE(user_id, date, workout_type)
);

-- Exercises table
CREATE TABLE IF NOT EXISTS public.exercises (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workout_id UUID NOT NULL REFERENCES public.workouts(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    sets JSONB NOT NULL DEFAULT '[]',
    notes TEXT,
    order_index INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW())
);

-- Nutrition table
CREATE TABLE IF NOT EXISTS public.nutrition (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    calories INTEGER,
    protein_g NUMERIC(6,2),
    carbs_g NUMERIC(6,2),
    fats_g NUMERIC(6,2),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
    UNIQUE(user_id, date)
);

-- Measurements table
CREATE TABLE IF NOT EXISTS public.measurements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    weight_kg NUMERIC(5,2),
    body_fat_percent NUMERIC(4,2),
    measurements JSONB DEFAULT '{}',
    photos JSONB DEFAULT '[]',
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
    UNIQUE(user_id, date)
);

-- Create indexes
CREATE INDEX idx_workouts_user_date ON public.workouts(user_id, date DESC);
CREATE INDEX idx_exercises_workout ON public.exercises(workout_id);
CREATE INDEX idx_nutrition_user_date ON public.nutrition(user_id, date DESC);
CREATE INDEX idx_measurements_user_date ON public.measurements(user_id, date DESC);

-- Enable Row Level Security
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.workouts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.exercises ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.nutrition ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.measurements ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Users can view own profile" ON public.user_profiles
    FOR ALL USING (auth.uid() = id);

CREATE POLICY "Users can manage own workouts" ON public.workouts
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own exercises" ON public.exercises
    FOR ALL USING (
        auth.uid() = (SELECT user_id FROM public.workouts WHERE id = workout_id)
    );

CREATE POLICY "Users can manage own nutrition" ON public.nutrition
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own measurements" ON public.measurements
    FOR ALL USING (auth.uid() = user_id);
"""
    
    return runner.create_migration("initial_schema", content)