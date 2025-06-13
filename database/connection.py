"""
Supabase database connection and helper functions
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv
from functools import wraps
from flask import jsonify
import logging

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Initialize Supabase clients
try:
    url = os.getenv('SUPABASE_URL', '')
    anon_key = os.getenv('SUPABASE_KEY', '')
    service_key = os.getenv('SUPABASE_SERVICE_KEY', '')
    
    if url and anon_key:
        # Create client with anon key for general use
        supabase: Client = create_client(url, anon_key)
        logger.info("Supabase client initialized successfully")
        
        # Create service client if service key is available
        if service_key:
            supabase_admin: Client = create_client(url, service_key)
            logger.info("Supabase admin client initialized successfully")
        else:
            supabase_admin = None
            logger.warning("No service key provided - some operations may fail")
    else:
        logger.error("Missing Supabase URL or KEY")
        supabase = None
        supabase_admin = None
except Exception as e:
    logger.error(f"Failed to initialize Supabase client: {str(e)}")
    logger.error(f"Error type: {type(e).__name__}")
    logger.error(f"Error args: {e.args}")
    import traceback
    logger.error(f"Traceback: {traceback.format_exc()}")
    supabase = None


def check_supabase_connection():
    """Check if Supabase connection is working"""
    if not supabase:
        return False
    
    try:
        # Try a simple query to check connection
        result = supabase.table('exercises').select('id').limit(1).execute()
        return True
    except Exception as e:
        logger.error(f"Supabase connection check failed: {str(e)}")
        return False


def handle_db_errors(f):
    """Decorator to handle database errors consistently"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Database error in {f.__name__}: {str(e)}")
            # Return None instead of Flask response for database methods
            # The calling route should handle the error response
            return None
    return decorated_function


class WorkoutDB:
    """Database operations for workouts"""
    
    @staticmethod
    @handle_db_errors
    def create_workout(user_id, date, notes=None):
        """Create a new workout session"""
        data = {
            'user_id': user_id,
            'date': date,
            'notes': notes
        }
        
        result = supabase.table('workouts').insert(data).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    @handle_db_errors
    def get_workout_by_date(user_id, date):
        """Get workout for a specific date"""
        result = supabase.table('workouts')\
            .select('*, workout_sets(*, exercises(*))')\
            .eq('user_id', user_id)\
            .eq('date', date)\
            .execute()
        
        return result.data[0] if result.data else None
    
    @staticmethod
    @handle_db_errors
    def get_recent_workouts(user_id, limit=10):
        """Get recent workouts for a user"""
        result = supabase.table('workouts')\
            .select('*, workout_sets(*, exercises(*))')\
            .eq('user_id', user_id)\
            .order('date', desc=True)\
            .limit(limit)\
            .execute()
        
        return result.data
    
    @staticmethod
    @handle_db_errors
    def add_workout_set(workout_id, exercise_id, set_number, weight, reps, rpe=None, rest_seconds=None, notes=None):
        """Add a set to a workout"""
        data = {
            'workout_id': workout_id,
            'exercise_id': exercise_id,
            'set_number': set_number,
            'weight': weight,
            'reps': reps,
            'rpe': rpe,
            'rest_seconds': rest_seconds,
            'notes': notes
        }
        
        result = supabase.table('workout_sets').upsert(data).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    @handle_db_errors
    def update_personal_record(user_id, exercise_id, weight, reps, date):
        """Update or create a personal record"""
        # First check if PR exists
        existing = supabase.table('personal_records')\
            .select('*')\
            .eq('user_id', user_id)\
            .eq('exercise_id', exercise_id)\
            .execute()
        
        if existing.data:
            # Update if new PR is better (higher weight or more reps at same weight)
            current_pr = existing.data[0]
            if weight > current_pr['weight'] or (weight == current_pr['weight'] and reps > current_pr['reps']):
                data = {
                    'weight': weight,
                    'reps': reps,
                    'date_achieved': date
                }
                result = supabase.table('personal_records')\
                    .update(data)\
                    .eq('user_id', user_id)\
                    .eq('exercise_id', exercise_id)\
                    .execute()
                return result.data[0] if result.data else None
        else:
            # Create new PR
            data = {
                'user_id': user_id,
                'exercise_id': exercise_id,
                'weight': weight,
                'reps': reps,
                'date_achieved': date
            }
            result = supabase.table('personal_records').insert(data).execute()
            return result.data[0] if result.data else None
        
        return None
    
    @staticmethod
    @handle_db_errors
    def get_exercise_history(user_id, exercise_id, limit=10):
        """Get history for a specific exercise"""
        result = supabase.table('workout_sets')\
            .select('*, workouts!inner(date, user_id)')\
            .eq('exercise_id', exercise_id)\
            .eq('workouts.user_id', user_id)\
            .order('workouts.date', desc=True)\
            .limit(limit)\
            .execute()
        
        return result.data


class ExerciseDB:
    """Database operations for exercises"""
    
    @staticmethod
    @handle_db_errors
    def get_all_exercises():
        """Get all exercises from the database"""
        result = supabase.table('exercises')\
            .select('*')\
            .order('category', desc=False)\
            .order('name')\
            .execute()
        
        return result.data
    
    @staticmethod
    @handle_db_errors
    def get_exercise_by_slug(slug):
        """Get exercise by slug"""
        result = supabase.table('exercises')\
            .select('*')\
            .eq('slug', slug)\
            .execute()
        
        return result.data[0] if result.data else None
    
    @staticmethod
    @handle_db_errors
    def get_exercises_by_category(category):
        """Get exercises by category"""
        result = supabase.table('exercises')\
            .select('*')\
            .eq('category', category)\
            .order('name')\
            .execute()
        
        return result.data


class ProfileDB:
    """Database operations for user profiles"""
    
    @staticmethod
    @handle_db_errors
    def create_or_update_profile(user_id, data):
        """Create or update user profile"""
        # Ensure user_id is in the data
        data['id'] = user_id
        
        result = supabase.table('profiles').upsert(data).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    @handle_db_errors
    def get_profile(user_id):
        """Get user profile"""
        result = supabase.table('profiles')\
            .select('*')\
            .eq('id', user_id)\
            .execute()
        
        return result.data[0] if result.data else None
    
    @staticmethod
    @handle_db_errors
    def update_body_weight(user_id, weight):
        """Update user's body weight"""
        data = {'body_weight': weight}
        
        result = supabase.table('profiles')\
            .update(data)\
            .eq('id', user_id)\
            .execute()
        
        return result.data[0] if result.data else None
    
    @staticmethod
    @handle_db_errors
    def check_username_available(username):
        """Check if a username is available"""
        result = supabase.rpc('check_username_available', {
            'username_input': username
        }).execute()
        
        return result.data if result.data is not None else False
    
    @staticmethod
    @handle_db_errors
    def is_username_allowed(username):
        """Check if a username is allowed (valid format and not reserved)"""
        result = supabase.rpc('is_username_allowed', {
            'username_input': username
        }).execute()
        
        return result.data if result.data is not None else False
    
    @staticmethod
    @handle_db_errors
    def update_onboarding_status(user_id, completed=True):
        """Update user's onboarding completion status"""
        from datetime import datetime
        
        data = {
            'onboarding_completed': completed,
            'onboarding_completed_at': datetime.now().isoformat() if completed else None
        }
        
        result = supabase.table('profiles')\
            .update(data)\
            .eq('id', user_id)\
            .execute()
        
        return result.data[0] if result.data else None
    
    @staticmethod
    @handle_db_errors
    def start_onboarding(user_id):
        """Mark the start of onboarding process"""
        from datetime import datetime
        
        data = {
            'onboarding_started_at': datetime.now().isoformat()
        }
        
        result = supabase.table('profiles')\
            .update(data)\
            .eq('id', user_id)\
            .execute()
        
        return result.data[0] if result.data else None
    
    @staticmethod
    @handle_db_errors
    def update_profile_with_validation(user_id, data):
        """Update profile with validation for required onboarding fields"""
        # Validate required fields for onboarding
        required_fields = ['username', 'body_weight', 'primary_goal']
        for field in required_fields:
            if field in data and not data[field]:
                return None, f"{field} is required"
        
        # Validate username if provided
        if 'username' in data:
            if not ProfileDB.is_username_allowed(data['username']):
                return None, "Username is invalid or already taken"
        
        # Validate weight if provided
        if 'body_weight' in data:
            weight = float(data['body_weight'])
            if weight < 50 or weight > 500:
                return None, "Weight must be between 50 and 500 lbs"
        
        # Update profile
        result = ProfileDB.create_or_update_profile(user_id, data)
        return result, None


class OnboardingDB:
    """Database operations for onboarding sessions"""
    
    @staticmethod
    @handle_db_errors
    def create_session(email, user_id=None):
        """Create a new onboarding session"""
        from datetime import datetime, timedelta
        
        data = {
            'email': email,
            'user_id': user_id,
            'current_step': 1,
            'data': {},
            'expires_at': (datetime.now() + timedelta(hours=24)).isoformat()
        }
        
        # Use admin client if available for bypassing RLS
        client = supabase_admin if supabase_admin else supabase
        result = client.table('onboarding_sessions').insert(data).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    @handle_db_errors
    def get_session(session_id):
        """Get an onboarding session by ID"""
        result = supabase.table('onboarding_sessions')\
            .select('*')\
            .eq('id', session_id)\
            .execute()
        
        return result.data[0] if result.data else None
    
    @staticmethod
    @handle_db_errors
    def get_session_by_email(email):
        """Get the most recent active onboarding session for an email"""
        from datetime import datetime
        
        result = supabase.table('onboarding_sessions')\
            .select('*')\
            .eq('email', email)\
            .eq('completed', False)\
            .gt('expires_at', datetime.now().isoformat())\
            .order('created_at', desc=True)\
            .limit(1)\
            .execute()
        
        return result.data[0] if result.data else None
    
    @staticmethod
    @handle_db_errors
    def update_session(session_id, step=None, data=None):
        """Update onboarding session progress"""
        from datetime import datetime
        
        update_data = {'updated_at': datetime.now().isoformat()}
        
        if step is not None:
            update_data['current_step'] = step
        
        if data is not None:
            # Merge new data with existing data
            session = OnboardingDB.get_session(session_id)
            if session:
                existing_data = session.get('data', {})
                existing_data.update(data)
                update_data['data'] = existing_data
        
        result = supabase.table('onboarding_sessions')\
            .update(update_data)\
            .eq('id', session_id)\
            .execute()
        
        return result.data[0] if result.data else None
    
    @staticmethod
    @handle_db_errors
    def complete_session(session_id):
        """Mark an onboarding session as completed"""
        from datetime import datetime
        
        data = {
            'completed': True,
            'updated_at': datetime.now().isoformat()
        }
        
        result = supabase.table('onboarding_sessions')\
            .update(data)\
            .eq('id', session_id)\
            .execute()
        
        return result.data[0] if result.data else None
    
    @staticmethod
    @handle_db_errors
    def cleanup_expired_sessions():
        """Clean up expired onboarding sessions"""
        result = supabase.rpc('cleanup_expired_onboarding_sessions').execute()
        return result.data if result.data is not None else 0
    
    @staticmethod
    @handle_db_errors
    def get_fitness_goals():
        """Get all available fitness goals"""
        result = supabase.table('fitness_goals')\
            .select('*')\
            .order('display_order')\
            .execute()
        
        return result.data


class NutritionDB:
    """Database operations for nutrition tracking"""
    
    @staticmethod
    @handle_db_errors
    def log_nutrition(user_id, date, data):
        """Log nutrition for a date"""
        nutrition_data = {
            'user_id': user_id,
            'date': date,
            **data
        }
        
        result = supabase.table('nutrition_logs').upsert(nutrition_data).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    @handle_db_errors
    def get_nutrition_by_date(user_id, date):
        """Get nutrition log for a specific date"""
        result = supabase.table('nutrition_logs')\
            .select('*')\
            .eq('user_id', user_id)\
            .eq('date', date)\
            .execute()
        
        return result.data[0] if result.data else None
    
    @staticmethod
    @handle_db_errors
    def get_nutrition_history(user_id, days=7):
        """Get nutrition history for the last N days"""
        from datetime import datetime, timedelta
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        result = supabase.table('nutrition_logs')\
            .select('*')\
            .eq('user_id', user_id)\
            .gte('date', start_date.isoformat())\
            .lte('date', end_date.isoformat())\
            .order('date', desc=True)\
            .execute()
        
        return result.data


class MeasurementDB:
    """Database operations for body measurements"""
    
    @staticmethod
    @handle_db_errors
    def log_measurement(user_id, date, data):
        """Log body measurements"""
        measurement_data = {
            'user_id': user_id,
            'date': date,
            **data
        }
        
        result = supabase.table('measurements').upsert(measurement_data).execute()
        return result.data[0] if result.data else None
    
    @staticmethod
    @handle_db_errors
    def get_measurement_history(user_id, days=30):
        """Get measurement history"""
        from datetime import datetime, timedelta
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        result = supabase.table('measurements')\
            .select('*')\
            .eq('user_id', user_id)\
            .gte('date', start_date.isoformat())\
            .lte('date', end_date.isoformat())\
            .order('date', desc=True)\
            .execute()
        
        return result.data