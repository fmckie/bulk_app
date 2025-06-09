from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from flask_cors import CORS
from dotenv import load_dotenv
import os
from datetime import datetime
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

# Enable CORS for API endpoints
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Check if we're in demo mode (no Supabase configured)
DEMO_MODE = not os.getenv('SUPABASE_URL') or not os.getenv('SUPABASE_KEY')

if DEMO_MODE:
    logger.warning("Running in DEMO MODE - No Supabase connection")
    # Import demo routes
    from demo_routes import demo_bp
    app.register_blueprint(demo_bp)
else:
    # Import database modules and auth
    from database.connection import (
        check_supabase_connection, 
        WorkoutDB, 
        ExerciseDB, 
        ProfileDB, 
        NutritionDB, 
        MeasurementDB
    )
    from auth import login_required, get_current_user_id, AuthService

# Routes
@app.route('/')
def index():
    """Home page - Dashboard"""
    current_date = datetime.now().strftime('%A, %B %d, %Y')
    return render_template('index.html', current_date=current_date)

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    if DEMO_MODE:
        return jsonify({
            'status': 'healthy',
            'message': 'Kinobody Tracker API is running',
            'mode': 'demo',
            'database': 'demo mode - no database'
        })
    else:
        db_status = check_supabase_connection()
        return jsonify({
            'status': 'healthy' if db_status else 'degraded',
            'message': 'Kinobody Tracker API is running',
            'mode': 'production',
            'database': 'connected' if db_status else 'disconnected'
        })

@app.route('/api/test')
def test_endpoint():
    """Test API endpoint"""
    return jsonify({
        'message': 'API is working!',
        'app_name': 'Kinobody Greek God Program Tracker',
        'version': '1.0.0'
    })

# Page Routes
@app.route('/workout')
def workout():
    """Workout logging page"""
    current_date = datetime.now().strftime('%A, %B %d, %Y')
    return render_template('workout.html', current_date=current_date)

@app.route('/nutrition')
def nutrition():
    """Nutrition tracking page"""
    return render_template('nutrition.html')

@app.route('/progress')
def progress():
    """Progress visualization page"""
    return render_template('progress.html')

@app.route('/profile')
def profile():
    """User profile page"""
    return render_template('profile.html')

@app.route('/measurements')
def measurements():
    """Body measurements page"""
    return render_template('measurements.html')

# API Routes for Workout
if not DEMO_MODE:
    @app.route('/api/workouts', methods=['POST'])
    @login_required
    def log_workout():
        """Save a workout session"""
        try:
            user_id = get_current_user_id()
            data = request.json
            
            # Create or get workout for today
            date = data.get('date', datetime.now().date().isoformat())
            notes = data.get('notes', '')
            
            # Check if workout already exists for this date
            existing_workout = WorkoutDB.get_workout_by_date(user_id, date)
            
            if existing_workout:
                workout_id = existing_workout['id']
            else:
                workout = WorkoutDB.create_workout(user_id, date, notes)
                workout_id = workout['id']
            
            # Add workout sets
            sets = data.get('sets', [])
            for set_data in sets:
                # Get exercise ID from slug
                exercise = ExerciseDB.get_exercise_by_slug(set_data['exercise_slug'])
                if exercise:
                    WorkoutDB.add_workout_set(
                        workout_id=workout_id,
                        exercise_id=exercise['id'],
                        set_number=set_data['set_number'],
                        weight=set_data['weight'],
                        reps=set_data['reps'],
                        rpe=set_data.get('rpe'),
                        rest_seconds=set_data.get('rest_seconds'),
                        notes=set_data.get('notes')
                    )
                    
                    # Check for personal record
                    WorkoutDB.update_personal_record(
                        user_id=user_id,
                        exercise_id=exercise['id'],
                        weight=set_data['weight'],
                        reps=set_data['reps'],
                        date=date
                    )
            
            return jsonify({
                'status': 'success',
                'message': 'Workout saved successfully',
                'workout_id': workout_id
            })
        except Exception as e:
            logger.error(f"Error logging workout: {str(e)}")
            return jsonify({'error': str(e)}), 400

@app.route('/api/workouts/recent', methods=['GET'])
@login_required
def get_recent_workouts():
    """Get recent workout history"""
    try:
        user_id = get_current_user_id()
        limit = request.args.get('limit', 10, type=int)
        
        workouts = WorkoutDB.get_recent_workouts(user_id, limit)
        
        # Format the response
        formatted_workouts = []
        for workout in workouts:
            formatted_workout = {
                'id': workout['id'],
                'date': workout['date'],
                'notes': workout.get('notes', ''),
                'exercises': []
            }
            
            # Group sets by exercise
            exercise_sets = {}
            for set_data in workout.get('workout_sets', []):
                exercise_name = set_data['exercises']['name']
                exercise_slug = set_data['exercises']['slug']
                
                if exercise_slug not in exercise_sets:
                    exercise_sets[exercise_slug] = {
                        'name': exercise_name,
                        'slug': exercise_slug,
                        'sets': []
                    }
                
                exercise_sets[exercise_slug]['sets'].append({
                    'set_number': set_data['set_number'],
                    'weight': float(set_data['weight']),
                    'reps': set_data['reps'],
                    'rpe': float(set_data['rpe']) if set_data.get('rpe') else None
                })
            
            formatted_workout['exercises'] = list(exercise_sets.values())
            formatted_workouts.append(formatted_workout)
        
        return jsonify(formatted_workouts)
    except Exception as e:
        logger.error(f"Error getting recent workouts: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/exercises', methods=['GET'])
def get_exercises():
    """Get list of exercises"""
    try:
        all_exercises = ExerciseDB.get_all_exercises()
        
        # Group by category
        exercises = {
            'indicator': [],
            'assistance': []
        }
        
        for exercise in all_exercises:
            exercise_data = {
                'id': exercise['id'],
                'name': exercise['name'],
                'slug': exercise['slug'],
                'category': exercise['muscle_group'],
                'instructions': exercise.get('instructions', '')
            }
            
            if exercise['category'] == 'indicator':
                exercises['indicator'].append(exercise_data)
            else:
                exercises['assistance'].append(exercise_data)
        
        return jsonify(exercises)
    except Exception as e:
        logger.error(f"Error getting exercises: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/personal-records', methods=['GET'])
@login_required
def get_personal_records():
    """Get personal records for exercises"""
    try:
        user_id = get_current_user_id()
        
        # Get all exercises first
        exercises = ExerciseDB.get_all_exercises()
        
        # Get user's PRs from database
        from database.connection import supabase
        result = supabase.table('personal_records')\
            .select('*, exercises(slug)')\
            .eq('user_id', user_id)\
            .execute()
        
        # Format as dict with exercise slug as key
        prs = {}
        for pr in result.data:
            if pr.get('exercises') and pr['exercises'].get('slug'):
                prs[pr['exercises']['slug']] = {
                    'weight': float(pr['weight']),
                    'reps': pr['reps'],
                    'date': pr['date_achieved']
                }
        
        return jsonify(prs)
    except Exception as e:
        logger.error(f"Error getting personal records: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/warmup-calculator', methods=['POST'])
def calculate_warmup():
    """Calculate warm-up sets"""
    try:
        data = request.json
        working_weight = data.get('working_weight', 0)
        
        warmup_sets = [
            {'percentage': 60, 'weight': round(working_weight * 0.6 / 5) * 5, 'reps': 5},
            {'percentage': 75, 'weight': round(working_weight * 0.75 / 5) * 5, 'reps': 3},
            {'percentage': 90, 'weight': round(working_weight * 0.9 / 5) * 5, 'reps': 1}
        ]
        
        return jsonify(warmup_sets)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# Authentication Routes
@app.route('/api/auth/signup', methods=['POST'])
def signup():
    """Sign up a new user"""
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email and password required'}), 400
        
        # Profile data
        profile_data = {
            'username': data.get('username'),
            'full_name': data.get('full_name'),
            'body_weight': data.get('body_weight')
        }
        
        result = AuthService.sign_up(email, password, profile_data)
        
        if result['success']:
            # Store session
            if result.get('session'):
                session['access_token'] = result['session'].access_token
                session['refresh_token'] = result['session'].refresh_token
            
            return jsonify({
                'success': True,
                'message': 'Account created successfully',
                'user': {
                    'id': result['user'].id,
                    'email': result['user'].email
                }
            })
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logger.error(f"Signup error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/signin', methods=['POST'])
def signin():
    """Sign in a user"""
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email and password required'}), 400
        
        result = AuthService.sign_in(email, password)
        
        if result['success']:
            # Store session
            if result.get('session'):
                session['access_token'] = result['session'].access_token
                session['refresh_token'] = result['session'].refresh_token
            
            return jsonify({
                'success': True,
                'message': 'Signed in successfully',
                'user': {
                    'id': result['user'].id,
                    'email': result['user'].email
                }
            })
        else:
            return jsonify({'error': result['error']}), 401
            
    except Exception as e:
        logger.error(f"Signin error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/signout', methods=['POST'])
def signout():
    """Sign out the current user"""
    try:
        token = session.get('access_token')
        result = AuthService.sign_out(token)
        
        # Clear session
        session.clear()
        
        return jsonify({
            'success': True,
            'message': 'Signed out successfully'
        })
    except Exception as e:
        logger.error(f"Signout error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/user', methods=['GET'])
@login_required
def get_user():
    """Get current user info"""
    try:
        user_id = get_current_user_id()
        profile = ProfileDB.get_profile(user_id)
        
        return jsonify({
            'id': user_id,
            'profile': profile
        })
    except Exception as e:
        logger.error(f"Get user error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Run development server
    app.run(debug=True, host='0.0.0.0', port=8000)