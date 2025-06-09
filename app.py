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

# Authentication Page Routes
@app.route('/login')
def login():
    """Login page"""
    # If already logged in, redirect to home
    if 'access_token' in session:
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/register')
def register():
    """Registration page"""
    # If already logged in, redirect to home
    if 'access_token' in session:
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/password-reset')
def password_reset():
    """Password reset page"""
    return render_template('password-reset.html')

@app.route('/logout')
def logout():
    """Logout and redirect to home"""
    session.clear()
    return redirect(url_for('index'))

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
    from auth import login_required, get_current_user_id, AuthService
    
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
    if DEMO_MODE:
        return redirect('/api/demo/exercises')
    
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
def get_personal_records():
    """Get personal records for exercises"""
    if DEMO_MODE:
        return redirect('/api/demo/personal-records')
    
    from auth import login_required, get_current_user_id
    
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

# Nutrition API Routes
@app.route('/api/nutrition', methods=['POST'])
def save_nutrition():
    """Save daily nutrition data"""
    if DEMO_MODE:
        return redirect('/api/demo/nutrition', code=307)  # 307 preserves POST method
    
    from auth import login_required, get_current_user_id
    user_id = get_current_user_id()
    data = request.json
    
    date = data.get('date', datetime.now().date().isoformat())
    
    # Check if workout exists for this date to determine if it's a training day
    workout = WorkoutDB.get_workout_by_date(user_id, date)
    is_training_day = workout is not None
    
    nutrition_data = {
        'calories': data.get('calories'),
        'protein_g': data.get('protein'),
        'carbs_g': data.get('carbs'),
        'fats_g': data.get('fats'),
        'notes': data.get('notes', ''),
        'is_training_day': is_training_day
    }
    
    result = NutritionDB.log_nutrition(user_id, date, nutrition_data)
    
    return jsonify({
        'status': 'success',
        'message': 'Nutrition data saved successfully',
        'data': result
    })

@app.route('/api/nutrition/<date>', methods=['GET'])
def get_nutrition(date):
    """Get nutrition data for a specific date"""
    if DEMO_MODE:
        return redirect(f'/api/demo/nutrition/{date}')
    
    from auth import login_required, get_current_user_id
    user_id = get_current_user_id()
    
    nutrition = NutritionDB.get_nutrition_by_date(user_id, date)
    
    if nutrition:
        # Also check if it's a training day
        workout = WorkoutDB.get_workout_by_date(user_id, date)
        nutrition['is_training_day'] = workout is not None
        
        return jsonify(nutrition)
    else:
        # Check if it's a training day even if no nutrition logged
        workout = WorkoutDB.get_workout_by_date(user_id, date)
        return jsonify({
            'date': date,
            'is_training_day': workout is not None,
            'calories': None,
            'protein_g': None,
            'carbs_g': None,
            'fats_g': None
        })

@app.route('/api/nutrition/history', methods=['GET'])
def get_nutrition_history():
    """Get nutrition history"""
    if DEMO_MODE:
        return redirect('/api/demo/nutrition/history')
    
    from auth import login_required, get_current_user_id
    user_id = get_current_user_id()
    days = request.args.get('days', 7, type=int)
    
    history = NutritionDB.get_nutrition_history(user_id, days)
    
    # Add training day info to each entry
    for entry in history:
        workout = WorkoutDB.get_workout_by_date(user_id, entry['date'])
        entry['is_training_day'] = workout is not None
    
    return jsonify(history)

@app.route('/api/nutrition/targets', methods=['GET'])
def get_nutrition_targets():
    """Calculate daily nutrition targets based on user profile and workout schedule"""
    if DEMO_MODE:
        return redirect('/api/demo/nutrition/targets')
    
    from auth import login_required, get_current_user_id
    user_id = get_current_user_id()
    date = request.args.get('date', datetime.now().date().isoformat())
    
    # Get user profile for body weight
    profile = ProfileDB.get_profile(user_id)
    if not profile or not profile.get('body_weight'):
        return jsonify({
            'error': 'Please update your body weight in your profile to calculate targets'
        }), 400
    
    body_weight = float(profile['body_weight'])
    
    # Check if today is a training day
    workout = WorkoutDB.get_workout_by_date(user_id, date)
    is_training_day = workout is not None
    
    # Calculate targets based on Kinobody protocol
    maintenance = body_weight * 15  # 15 calories per pound
    
    if is_training_day:
        calories = maintenance + 500  # +500 on training days
    else:
        calories = maintenance + 100  # +100 on rest days
    
    # Macro calculations
    protein = body_weight * 1.0  # 1g per lb body weight (Kinobody recommendation)
    fats = calories * 0.25 / 9  # 25% of calories from fats (9 cal per gram)
    carbs = (calories - (protein * 4) - (fats * 9)) / 4  # Remaining calories from carbs
    
    return jsonify({
        'is_training_day': is_training_day,
        'body_weight': body_weight,
        'maintenance_calories': round(maintenance),
        'targets': {
            'calories': round(calories),
            'protein': round(protein),
            'carbs': round(carbs),
            'fats': round(fats)
        },
        'calorie_surplus': round(calories - maintenance)
    })


# Authentication Routes
@app.route('/api/auth/signup', methods=['POST'])
def signup():
    """Sign up a new user"""
    if DEMO_MODE:
        return jsonify({'error': 'Authentication requires Supabase configuration. Please use demo mode or configure Supabase.'}), 503
    
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
    if DEMO_MODE:
        return jsonify({'error': 'Authentication requires Supabase configuration. Please use demo mode or configure Supabase.'}), 503
    
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
    if DEMO_MODE:
        session.clear()
        return jsonify({'success': True, 'message': 'Signed out successfully'})
    
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
def get_user():
    """Get current user info"""
    if DEMO_MODE:
        return jsonify({'error': 'Authentication requires Supabase configuration.'}), 503
    
    # Apply login_required decorator conditionally
    from auth import login_required, get_current_user_id, ProfileDB
    
    @login_required
    def _get_user_impl():
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
    
    return _get_user_impl()

@app.route('/api/auth/reset-password', methods=['POST'])
def request_password_reset():
    """Request a password reset email"""
    if DEMO_MODE:
        return jsonify({'error': 'Password reset requires Supabase configuration.'}), 503
    
    try:
        data = request.json
        email = data.get('email')
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        # Generate reset token and send email
        # Note: This requires email service configuration
        from database.connection import supabase
        
        # Check if user exists
        result = supabase.table('profiles').select('*').eq('email', email).execute()
        
        if result.data:
            # In production, generate token and send email
            # For now, we'll just return success
            logger.info(f"Password reset requested for: {email}")
            
            # TODO: Implement email service
            # - Generate secure token
            # - Store token with expiration
            # - Send email with reset link
            
            return jsonify({
                'success': True,
                'message': 'If an account exists with this email, you will receive reset instructions'
            })
        else:
            # Return same message to prevent email enumeration
            return jsonify({
                'success': True,
                'message': 'If an account exists with this email, you will receive reset instructions'
            })
            
    except Exception as e:
        logger.error(f"Password reset request error: {str(e)}")
        return jsonify({'error': 'An error occurred processing your request'}), 500

@app.route('/api/auth/reset-password/confirm', methods=['POST'])
def confirm_password_reset():
    """Confirm password reset with token"""
    try:
        data = request.json
        token = data.get('token')
        new_password = data.get('password')
        
        if not token or not new_password:
            return jsonify({'error': 'Token and password are required'}), 400
        
        # TODO: Implement token validation and password update
        # - Verify token is valid and not expired
        # - Update user password
        # - Invalidate token
        
        # For now, return error as not implemented
        return jsonify({
            'error': 'Password reset functionality requires email service configuration'
        }), 501
        
    except Exception as e:
        logger.error(f"Password reset confirm error: {str(e)}")
        return jsonify({'error': 'An error occurred resetting your password'}), 500

@app.route('/api/auth/oauth/<provider>', methods=['GET'])
def get_oauth_url(provider):
    """Get OAuth provider URL"""
    if DEMO_MODE:
        return jsonify({'error': 'OAuth authentication requires Supabase configuration.'}), 503
    
    try:
        if provider not in ['google', 'github']:
            return jsonify({'error': 'Invalid provider'}), 400
        
        result = AuthService.get_oauth_url(provider)
        
        if result['success']:
            return jsonify({
                'success': True,
                'url': result['url']
            })
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logger.error(f"OAuth URL error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/auth/callback')
def auth_callback():
    """Handle OAuth callback"""
    try:
        # Get the access token from URL hash (handled client-side)
        # Redirect to home with success message
        return redirect(url_for('index', auth='success'))
    except Exception as e:
        logger.error(f"Auth callback error: {str(e)}")
        return redirect(url_for('login', error='auth_failed'))

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