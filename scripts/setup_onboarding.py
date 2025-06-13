#!/usr/bin/env python3
"""
Setup script for the enhanced onboarding feature.
Run this after deploying to apply database migrations.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import supabase
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """Run the onboarding migration"""
    try:
        # Read migration file
        migration_path = os.path.join(os.path.dirname(__file__), '../migrations/002_enhanced_profile_onboarding.sql')
        
        with open(migration_path, 'r') as f:
            migration_sql = f.read()
        
        # Note: Supabase doesn't support direct SQL execution through the client
        # You'll need to run this migration through the Supabase dashboard or CLI
        
        logger.info("Migration SQL loaded successfully")
        logger.info("Please run the following migration in your Supabase SQL editor:")
        logger.info("-" * 80)
        print(migration_sql)
        logger.info("-" * 80)
        
        return True
        
    except Exception as e:
        logger.error(f"Error loading migration: {str(e)}")
        return False

def verify_setup():
    """Verify the onboarding setup"""
    try:
        # Check if fitness_goals table exists
        result = supabase.table('fitness_goals').select('*').limit(1).execute()
        logger.info(f"✓ fitness_goals table exists with {len(result.data)} sample records")
        
        # Check if onboarding_sessions table exists
        result = supabase.table('onboarding_sessions').select('*').limit(1).execute()
        logger.info("✓ onboarding_sessions table exists")
        
        # Check if profiles table has new columns
        result = supabase.table('profiles').select('onboarding_completed').limit(1).execute()
        logger.info("✓ profiles table has onboarding columns")
        
        logger.info("\n✅ Onboarding setup verified successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Setup verification failed: {str(e)}")
        logger.error("Please ensure you've run the migration SQL in Supabase")
        return False

if __name__ == "__main__":
    logger.info("Enhanced Profile Onboarding Setup")
    logger.info("=================================\n")
    
    # Load and display migration
    if run_migration():
        logger.info("\n📝 Migration SQL loaded. Please execute it in Supabase SQL editor.")
        logger.info("🔗 Go to: https://app.supabase.com/project/YOUR_PROJECT/sql/new")
        
        # Optionally verify setup
        input("\nPress Enter after running the migration to verify setup...")
        verify_setup()
    else:
        logger.error("Failed to load migration")