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

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'environment': os.getenv('ENVIRONMENT', 'unknown'),
        'services': {}
    }
    
    # Check Supabase connection
    if not DEMO_MODE:
        try:
            from database.connection import check_supabase_connection
            supabase_ok = check_supabase_connection()
            health_status['services']['supabase'] = 'healthy' if supabase_ok else 'unhealthy'
        except Exception as e:
            health_status['services']['supabase'] = f'error: {str(e)}'
    
    # Check Redis connection
    try:
        from services.redis_cache import default_cache
        if default_cache.client:
            test_key = 'health:check'
            if default_cache.set(test_key, 'ok', ttl=10):
                default_cache.delete(test_key)
                health_status['services']['redis'] = 'healthy'
            else:
                health_status['services']['redis'] = 'unhealthy'
        else:
            health_status['services']['redis'] = 'not configured'
    except Exception as e:
        health_status['services']['redis'] = f'error: {str(e)}'
    
    # Overall status
    if any(status != 'healthy' and status != 'not configured' 
           for status in health_status['services'].values()):
        health_status['status'] = 'degraded'
        return jsonify(health_status), 503
    
    return jsonify(health_status), 200

@app.route('/dashboard-epic')
def dashboard_epic():
    """Epic Dashboard - Forge of Gods Theme"""
    current_date = datetime.now().strftime('%A, %B %d, %Y')
    return render_template('dashboard-epic.html', current_date=current_date)

@app.route('/dashboard-pilot')
def dashboard_pilot():
    """MD Pilot Dashboard - Professional Health Analytics"""
    current_date = datetime.now().strftime('%A, %B %d, %Y')
    # In production, these would come from the database
    context = {
        'current_date': current_date,
        'username': session.get('username', 'Navigator'),
        'progress_score': 87,
        'days_active': 45,
        'strength_score': 245,
        'body_fat': 12.5,
        'consistency': 94,
        'current_weight': 175,
        'strength_level': 'Advanced',
        'next_workout_time': '8:00 AM'
    }
    return render_template('dashboard-pilot.html', **context)

@app.route('/dashboard-next')
def dashboard_next():
    """MD Pilot Next - Revolutionary Health Navigation System"""
    current_date = datetime.now().strftime('%A, %B %d, %Y')
    # In production, these would come from the database
    context = {
        'current_date': current_date,
        'username': session.get('username', 'Navigator'),
        'health_score': 92,
        'trajectory_change': '+15%',
        'strength_score': 245,
        'recovery_score': 87,
        'nutrition_score': 78,
        'stress_score': 65,
        'body_fat': 12.5,
        'consistency': 94,
        'current_weight': 175,
        'days_active': 45
    }
    return render_template('dashboard-next.html', **context)

@app.route('/api/health')
def api_health_check():
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

@app.route('/onboarding/profile')
def onboarding_profile():
    """Onboarding step 1: Profile setup"""
    # Check if user is logged in
    if 'access_token' not in session:
        return redirect(url_for('login'))
    return render_template('onboarding-step1.html')

@app.route('/onboarding/goals')
def onboarding_goals():
    """Onboarding step 2: Fitness goals"""
    # Check if user is logged in
    if 'access_token' not in session:
        return redirect(url_for('login'))
    return render_template('onboarding-step2.html')

@app.route('/onboarding/complete')
def onboarding_complete():
    """Onboarding completion page"""
    # Check if user is logged in
    if 'access_token' not in session:
        return redirect(url_for('login'))
    return render_template('onboarding-complete.html')

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
if not DEMO_MODE:
    @app.route('/api/nutrition', methods=['POST'])
    @login_required
    def save_nutrition():
        """Save daily nutrition data"""
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
else:
    @app.route('/api/nutrition', methods=['POST'])
    def save_nutrition():
        """Save daily nutrition data - redirect to demo"""
        return redirect('/api/demo/nutrition', code=307)

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

if not DEMO_MODE:
    @app.route('/api/nutrition/targets', methods=['GET'])
    @login_required
    def get_nutrition_targets():
        """Calculate daily nutrition targets based on user profile and workout schedule"""
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
else:
    @app.route('/api/nutrition/targets', methods=['GET'])
    def get_nutrition_targets():
        """Redirect to demo nutrition targets"""
        return redirect('/api/demo/nutrition/targets')


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
        
        # Initial signup only needs email/password
        # Profile data will be collected during onboarding
        result = AuthService.sign_up(email, password, {})
        
        if result['success']:
            # Store session
            if result.get('session'):
                session['access_token'] = result['session'].access_token
                session['refresh_token'] = result['session'].refresh_token
            
            # Create onboarding session
            from database.connection import OnboardingDB
            onboarding_session = OnboardingDB.create_session(
                email=result['user'].email,
                user_id=result['user'].id
            )
            
            return jsonify({
                'success': True,
                'message': 'Account created successfully',
                'user': {
                    'id': result['user'].id,
                    'email': result['user'].email
                },
                'onboarding': {
                    'required': True,
                    'session_id': onboarding_session['id'] if onboarding_session else None,
                    'current_step': 1
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
    from auth import login_required, get_current_user_id
    from database.connection import ProfileDB
    
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

# Profile API Routes
@app.route('/api/profile', methods=['GET'])
def get_profile():
    """Get current user's profile"""
    if DEMO_MODE:
        return jsonify({'error': 'Profile requires Supabase configuration.'}), 503
    
    from auth import login_required, get_current_user_id
    from database.connection import ProfileDB
    
    @login_required
    def _get_profile_impl():
        try:
            user_id = get_current_user_id()
            profile = ProfileDB.get_profile(user_id)
            
            if not profile:
                # Create default profile if none exists
                profile = ProfileDB.create_or_update_profile(user_id, {})
            
            return jsonify(profile)
        except Exception as e:
            logger.error(f"Get profile error: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    return _get_profile_impl()

@app.route('/api/profile', methods=['PUT'])
def update_profile():
    """Update current user's profile"""
    if DEMO_MODE:
        return jsonify({'error': 'Profile update requires Supabase configuration.'}), 503
    
    from auth import login_required, get_current_user_id
    from database.connection import ProfileDB
    
    @login_required
    def _update_profile_impl():
        try:
            user_id = get_current_user_id()
            data = request.json
            
            # Update profile
            profile = ProfileDB.create_or_update_profile(user_id, data)
            
            return jsonify(profile)
        except Exception as e:
            logger.error(f"Update profile error: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    return _update_profile_impl()

@app.route('/api/profile/avatar', methods=['POST'])
def upload_avatar():
    """Upload user avatar"""
    if DEMO_MODE:
        return jsonify({'error': 'Avatar upload requires Supabase configuration.'}), 503
    
    from auth import login_required, get_current_user_id
    from database.connection import ProfileDB, supabase
    import base64
    import uuid
    
    @login_required
    def _upload_avatar_impl():
        try:
            user_id = get_current_user_id()
            
            if 'avatar' not in request.files:
                return jsonify({'error': 'No file provided'}), 400
            
            file = request.files['avatar']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            # Validate file type
            allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
            file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
            if file_ext not in allowed_extensions:
                return jsonify({'error': 'Invalid file type'}), 400
            
            # Generate unique filename
            filename = f"{user_id}/{uuid.uuid4()}.{file_ext}"
            
            # Upload to Supabase Storage
            file_data = file.read()
            response = supabase.storage.from_('avatars').upload(
                path=filename,
                file=file_data,
                file_options={"content-type": file.content_type}
            )
            
            if response.error:
                raise Exception(response.error.message)
            
            # Get public URL
            avatar_url = supabase.storage.from_('avatars').get_public_url(filename)
            
            # Update profile with avatar URL
            profile = ProfileDB.create_or_update_profile(user_id, {'avatar_url': avatar_url})
            
            return jsonify({'avatar_url': avatar_url})
        except Exception as e:
            logger.error(f"Avatar upload error: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    return _upload_avatar_impl()

@app.route('/api/profile/password', methods=['PUT'])
def change_password():
    """Change user password"""
    if DEMO_MODE:
        return jsonify({'error': 'Password change requires Supabase configuration.'}), 503
    
    from auth import login_required, get_current_user_id
    from database.connection import supabase
    
    @login_required
    def _change_password_impl():
        try:
            data = request.json
            current_password = data.get('current_password')
            new_password = data.get('new_password')
            
            if not current_password or not new_password:
                return jsonify({'error': 'Current and new passwords required'}), 400
            
            # Note: Supabase doesn't provide a direct way to verify current password
            # In production, you might want to re-authenticate the user first
            
            # Update password
            response = supabase.auth.update_user({
                'password': new_password
            })
            
            if response.error:
                raise Exception(response.error.message)
            
            return jsonify({'success': True, 'message': 'Password updated successfully'})
        except Exception as e:
            logger.error(f"Password change error: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    return _change_password_impl()

@app.route('/api/profile/export', methods=['GET'])
def export_user_data():
    """Export all user data"""
    if DEMO_MODE:
        return jsonify({'error': 'Data export requires Supabase configuration.'}), 503
    
    from auth import login_required, get_current_user_id
    from database.connection import ProfileDB, WorkoutDB, NutritionDB, MeasurementDB
    from flask import Response
    import json
    
    @login_required
    def _export_data_impl():
        try:
            user_id = get_current_user_id()
            
            # Gather all user data
            export_data = {
                'export_date': datetime.now().isoformat(),
                'profile': ProfileDB.get_profile(user_id),
                'workouts': WorkoutDB.get_recent_workouts(user_id, limit=1000),
                'nutrition': NutritionDB.get_nutrition_history(user_id, days=365),
                'measurements': MeasurementDB.get_measurement_history(user_id, days=365)
            }
            
            # Return as downloadable JSON file
            json_data = json.dumps(export_data, indent=2, default=str)
            return Response(
                json_data,
                mimetype='application/json',
                headers={
                    'Content-Disposition': f'attachment; filename=kinobody_export_{datetime.now().strftime("%Y%m%d")}.json'
                }
            )
        except Exception as e:
            logger.error(f"Data export error: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    return _export_data_impl()

@app.route('/api/profile', methods=['DELETE'])
def delete_account():
    """Delete user account and all data"""
    if DEMO_MODE:
        return jsonify({'error': 'Account deletion requires Supabase configuration.'}), 503
    
    from auth import login_required, get_current_user_id
    from database.connection import supabase
    
    @login_required
    def _delete_account_impl():
        try:
            user_id = get_current_user_id()
            
            # Delete user from Supabase Auth (cascades to profile and other tables)
            # Note: This requires service role key for admin operations
            # In production, you might want to implement soft delete or a deletion queue
            
            # For now, we'll just mark the account as deleted in the profile
            from database.connection import ProfileDB
            ProfileDB.create_or_update_profile(user_id, {
                'deleted_at': datetime.now().isoformat(),
                'is_deleted': True
            })
            
            # Clear session
            session.clear()
            
            return jsonify({'success': True, 'message': 'Account deletion initiated'})
        except Exception as e:
            logger.error(f"Account deletion error: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    return _delete_account_impl()

# Onboarding API Routes
@app.route('/api/onboarding/start', methods=['POST'])
def start_onboarding():
    """Start onboarding process after signup"""
    if DEMO_MODE:
        return jsonify({'error': 'Onboarding requires Supabase configuration.'}), 503
    
    from database.connection import OnboardingDB
    
    try:
        data = request.json
        email = data.get('email')
        user_id = data.get('user_id')
        
        if not email:
            return jsonify({'error': 'Email required'}), 400
        
        # Check for existing session
        existing_session = OnboardingDB.get_session_by_email(email)
        if existing_session:
            return jsonify(existing_session)
        
        # Create new onboarding session
        session = OnboardingDB.create_session(email, user_id)
        
        if not session:
            return jsonify({'error': 'Failed to create onboarding session'}), 500
        
        return jsonify(session)
    except Exception as e:
        logger.error(f"Start onboarding error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/onboarding/check-username', methods=['POST'])
def check_username():
    """Check if username is available"""
    if DEMO_MODE:
        return jsonify({'available': True, 'valid': True})
    
    from database.connection import ProfileDB
    
    try:
        data = request.json
        username = data.get('username', '')
        
        # Check if username is valid and available
        is_allowed = ProfileDB.is_username_allowed(username)
        is_available = ProfileDB.check_username_available(username) if is_allowed else False
        
        return jsonify({
            'available': is_available,
            'valid': is_allowed,
            'message': 'Username is available' if is_available else 'Username is not available or invalid'
        })
    except Exception as e:
        logger.error(f"Username check error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/onboarding/profile', methods=['POST'])
def update_onboarding_profile():
    """Update profile during onboarding"""
    if DEMO_MODE:
        return jsonify({'success': True})
    
    from auth import login_required, get_current_user_id
    from database.connection import ProfileDB, OnboardingDB
    
    @login_required
    def _update_onboarding_profile_impl():
        try:
            user_id = get_current_user_id()
            data = request.json
            session_id = data.get('session_id')
            
            # Extract profile data
            profile_data = {
                'username': data.get('username'),
                'full_name': data.get('full_name'),
                'body_weight': data.get('body_weight'),
                'weight_unit': data.get('weight_unit', 'lbs'),
                'height': data.get('height')
            }
            
            # Validate and update profile
            result, error = ProfileDB.update_profile_with_validation(user_id, profile_data)
            
            if error:
                return jsonify({'error': error}), 400
            
            # Update onboarding session
            if session_id:
                OnboardingDB.update_session(session_id, step=2, data={'profile_completed': True})
            
            # Mark onboarding started
            ProfileDB.start_onboarding(user_id)
            
            return jsonify({'success': True, 'profile': result})
        except Exception as e:
            logger.error(f"Onboarding profile update error: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    return _update_onboarding_profile_impl()

@app.route('/api/onboarding/goals', methods=['POST'])
def update_onboarding_goals():
    """Update fitness goals during onboarding"""
    if DEMO_MODE:
        return jsonify({'success': True})
    
    from auth import login_required, get_current_user_id
    from database.connection import ProfileDB, OnboardingDB
    
    @login_required
    def _update_onboarding_goals_impl():
        try:
            user_id = get_current_user_id()
            data = request.json
            session_id = data.get('session_id')
            
            # Extract goals data
            goals_data = {
                'primary_goal': data.get('primary_goal'),
                'target_weight': data.get('target_weight'),
                'target_body_fat': data.get('target_body_fat'),
                'activity_level': data.get('activity_level', 'moderately_active'),
                'program_start_date': datetime.now().date().isoformat()
            }
            
            # Update profile with goals
            result = ProfileDB.create_or_update_profile(user_id, goals_data)
            
            if not result:
                return jsonify({'error': 'Failed to update goals'}), 500
            
            # Complete onboarding
            ProfileDB.update_onboarding_status(user_id, completed=True)
            
            # Complete onboarding session
            if session_id:
                OnboardingDB.update_session(session_id, step=3, data={'goals_completed': True})
                OnboardingDB.complete_session(session_id)
            
            return jsonify({'success': True, 'profile': result})
        except Exception as e:
            logger.error(f"Onboarding goals update error: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    return _update_onboarding_goals_impl()

@app.route('/api/onboarding/goals-list', methods=['GET'])
def get_fitness_goals():
    """Get available fitness goals"""
    if DEMO_MODE:
        return jsonify({
            'goals': [
                {'id': 'muscle_building', 'name': 'Build Muscle', 'description': 'Focus on gaining lean muscle mass', 'icon': '💪'},
                {'id': 'weight_loss', 'name': 'Lose Weight', 'description': 'Focus on fat loss', 'icon': '🔥'},
                {'id': 'body_recomposition', 'name': 'Body Recomposition', 'description': 'Build muscle and lose fat', 'icon': '⚡'}
            ]
        })
    
    from database.connection import OnboardingDB
    
    try:
        goals = OnboardingDB.get_fitness_goals()
        return jsonify({'goals': goals})
    except Exception as e:
        logger.error(f"Get fitness goals error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/onboarding/skip', methods=['POST'])
def skip_onboarding():
    """Skip onboarding (for existing users or optional flow)"""
    if DEMO_MODE:
        return jsonify({'success': True})
    
    from auth import login_required, get_current_user_id
    from database.connection import ProfileDB, OnboardingDB
    
    @login_required
    def _skip_onboarding_impl():
        try:
            user_id = get_current_user_id()
            data = request.json
            session_id = data.get('session_id')
            
            # Mark onboarding as skipped (not completed)
            ProfileDB.update_onboarding_status(user_id, completed=False)
            
            # Cancel onboarding session
            if session_id:
                OnboardingDB.complete_session(session_id)
            
            return jsonify({'success': True})
        except Exception as e:
            logger.error(f"Skip onboarding error: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    return _skip_onboarding_impl()

@app.route('/meal-prep')
def meal_prep():
    """AI-Powered Meal Prep Planner page"""
    return render_template('meal-prep.html')

@app.route('/api/news', methods=['GET'])
def get_news():
    """Get news articles from md-pilot.com"""
    try:
        from datetime import datetime, timedelta
        from services.redis_cache import default_cache
        
        # Check if we have cached news in Redis
        cache_key = 'news_articles'
        cached_news = None
        
        # Try to get from cache using the redis_cache service
        try:
            cached_news = default_cache.get(cache_key)
            if cached_news:
                logger.info("Retrieved news from cache")
        except Exception as e:
            logger.warning(f"Cache retrieval failed: {str(e)}")
        
        if cached_news:
            return jsonify(cached_news)
        
        # Fetch from md-pilot.com
        # Note: Replace with actual API endpoint when available
        # For now, we'll return mock data that looks like it came from md-pilot.com
        articles = [
            {
                'id': '1',
                'title': 'The Ancient Greek Training Method for Modern Warriors',
                'excerpt': 'Discover how the training methods of ancient Greek warriors can transform your physique and mindset in the modern world.',
                'description': 'A deep dive into the training philosophies that created legendary physiques throughout history.',
                'url': 'https://md-pilot.com/articles/ancient-greek-training',
                'published': (datetime.now() - timedelta(days=1)).isoformat(),
                'featured': True,
                'category': 'training',
                'author': 'MD Pilot'
            },
            {
                'id': '2',
                'title': 'Nutrition Secrets of the Spartans',
                'excerpt': 'Learn the dietary principles that fueled the most feared warriors in history.',
                'description': 'Understanding macronutrient timing and the warrior diet for optimal performance.',
                'url': 'https://md-pilot.com/articles/spartan-nutrition',
                'published': (datetime.now() - timedelta(days=3)).isoformat(),
                'featured': False,
                'category': 'nutrition',
                'author': 'MD Pilot'
            },
            {
                'id': '3',
                'title': 'The Psychology of Physical Transformation',
                'excerpt': 'Master your mind to unlock your body\'s true potential.',
                'description': 'Mental strategies and mindset shifts that separate champions from everyone else.',
                'url': 'https://md-pilot.com/articles/transformation-psychology',
                'published': (datetime.now() - timedelta(days=5)).isoformat(),
                'featured': False,
                'category': 'mindset',
                'author': 'MD Pilot'
            }
        ]
        
        # In production, you would fetch from the actual API:
        # try:
        #     response = requests.get('https://md-pilot.com/api/articles', 
        #                           params={'limit': 10, 'category': 'fitness'},
        #                           timeout=5)
        #     if response.status_code == 200:
        #         articles = response.json()
        # except Exception as e:
        #     logger.error(f"Failed to fetch from md-pilot.com: {str(e)}")
        
        news_data = {
            'articles': articles,
            'last_updated': datetime.now().isoformat()
        }
        
        # Cache the results using redis_cache service
        try:
            if default_cache.set(cache_key, news_data, ttl=3600):  # Cache for 1 hour
                logger.info("Cached news articles")
            else:
                logger.warning("Failed to cache news articles")
        except Exception as e:
            logger.warning(f"Failed to cache news: {str(e)}")
        
        return jsonify(news_data)
        
    except Exception as e:
        logger.error(f"Error fetching news: {str(e)}")
        return jsonify({
            'articles': [],
            'error': 'Failed to fetch news articles'
        }), 500

# Meal Prep API Routes
@app.route('/api/meal-prep/test-generate', methods=['POST'])
def test_generate_meal_plan():
    """Test endpoint for meal plan generation without auth"""
    from services.openai_meal_service import OpenAIMealService
    from services.meal_prep_service import MealPrepService
    
    data = request.json
    
    # Use test user profile
    profile = {
        'body_weight': 187,  # 85kg in lbs
        'age': 23,
        'gender': 'male'
    }
    
    # Generate meal plan
    ai_service = OpenAIMealService()
    user_data = {
        'user_id': 'test-user',  # Add user_id for recipe saving
        'body_weight': profile['body_weight'],
        'age': profile['age'],
        'gender': profile['gender'],
        'dietary_requirements': data.get('dietary_requirements', []),
        'budget': data.get('budget', 150),
        'training_days': ['Monday', 'Wednesday', 'Friday'],
        'auto_save_recipes': True  # Enable auto-save
    }
    
    # Check if AI is requested and available
    use_ai = data.get('use_ai', True)
    if use_ai and ai_service.is_available():
        meal_plan = ai_service.generate_meal_plan(user_data)
    else:
        # Use demo meal plan
        meal_plan = ai_service._get_demo_meal_plan(user_data)
    
    return jsonify(meal_plan)

@app.route('/api/meal-prep/generate', methods=['POST'])
def generate_meal_plan():
    """Generate AI-powered meal plan"""
    if DEMO_MODE:
        # Demo mode implementation
        from services.openai_meal_service import OpenAIMealService
        from services.meal_prep_service import MealPrepService
        
        user_id = 'demo-user'
        data = request.json
        
        # Get demo user profile
        profile = {
            'body_weight': 175,
            'age': 25,
            'gender': 'male'
        }
        
        # Generate meal plan
        ai_service = OpenAIMealService()
        user_data = {
            'user_id': user_id,  # Add user_id for variety tracking
            'body_weight': profile['body_weight'],
            'age': profile['age'],
            'gender': profile['gender'],
            'dietary_requirements': data.get('dietary_requirements', []),
            'budget': data.get('budget', 150),
            'training_days': ['Monday', 'Wednesday', 'Friday'],
            'auto_save_recipes': True  # Enable auto-save
        }
        
        meal_plan = ai_service.generate_meal_plan(user_data)
        return jsonify(meal_plan)
    else:
        from auth import login_required, get_current_user_id
        from database.connection import ProfileDB
        from services.openai_meal_service import OpenAIMealService
        from services.meal_prep_service import MealPrepService
        
        @login_required
        def _generate_meal_plan():
            try:
                user_id = get_current_user_id()
                data = request.json
                
                # Get user profile
                profile = ProfileDB.get_profile(user_id)
                if not profile or not profile.get('body_weight'):
                    return jsonify({
                        'error': 'Please update your body weight in your profile first'
                    }), 400
                
                # Get user preferences
                from database.meal_prep_db import MealPrepDBStatic
                from database.connection import supabase
                preferences = MealPrepDBStatic.get_user_preferences(supabase, user_id)
                
                # Prepare user data for AI
                user_data = {
                    'user_id': user_id,  # Add user_id for variety tracking
                    'body_weight': float(profile['body_weight']),
                    'age': profile.get('age', 25),
                    'gender': profile.get('gender', 'male'),
                    'dietary_requirements': data.get('dietary_requirements', []),
                    'budget': data.get('budget', 150),
                    'training_days': ['Monday', 'Wednesday', 'Friday'],  # Get from workout schedule
                    'preferences': preferences,
                    'auto_save_recipes': True  # Enable auto-save
                }
                
                # Generate meal plan with AI
                ai_service = OpenAIMealService()
                
                if data.get('use_ai', True) and ai_service.is_available():
                    meal_plan_data = ai_service.generate_meal_plan(user_data)
                else:
                    # Use demo plan if AI is disabled or unavailable
                    meal_plan_data = ai_service._get_demo_meal_plan(user_data)
                
                # Save to database if requested
                if data.get('save', False):
                    prep_service = MealPrepService(supabase)
                    result = prep_service.create_meal_plan(user_id, meal_plan_data)
                    if result['success']:
                        meal_plan_data['meal_plan_id'] = result['meal_plan_id']
                
                return jsonify(meal_plan_data)
                
            except Exception as e:
                logger.error(f"Error generating meal plan: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        return _generate_meal_plan()

@app.route('/api/meal-prep/plans', methods=['GET'])
def get_meal_plans():
    """Get user's saved meal plans"""
    if DEMO_MODE:
        # Return demo plans
        return jsonify([
            {
                'id': 'demo-plan-1',
                'name': 'Demo Meal Plan - Week 1',
                'created_at': datetime.now().isoformat(),
                'status': 'active',
                'budget': 150
            }
        ])
    else:
        from auth import login_required, get_current_user_id
        from database.meal_prep_db import MealPrepDBStatic
        from database.connection import supabase
        
        @login_required
        def _get_meal_plans():
            try:
                user_id = get_current_user_id()
                plans = MealPrepDBStatic.get_user_meal_plans(supabase, user_id)
                return jsonify(plans)
            except Exception as e:
                logger.error(f"Error getting meal plans: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        return _get_meal_plans()

@app.route('/api/meal-prep/plan/<plan_id>', methods=['GET'])
def get_meal_plan(plan_id):
    """Get specific meal plan details"""
    if DEMO_MODE:
        # Return demo plan details
        from services.openai_meal_service import OpenAIMealService
        ai_service = OpenAIMealService()
        return jsonify(ai_service._get_demo_meal_plan({'body_weight': 175}))
    else:
        from auth import login_required, get_current_user_id
        from services.meal_prep_service import MealPrepService
        from database.connection import supabase
        
        @login_required
        def _get_meal_plan():
            try:
                user_id = get_current_user_id()
                prep_service = MealPrepService(supabase)
                meal_plan = prep_service.get_meal_plan(plan_id, user_id)
                
                if meal_plan:
                    return jsonify(meal_plan)
                else:
                    return jsonify({'error': 'Meal plan not found'}), 404
                    
            except Exception as e:
                logger.error(f"Error getting meal plan: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        return _get_meal_plan()

@app.route('/api/meal-prep/save', methods=['POST'])
def save_meal_plan():
    """Save a generated meal plan"""
    if DEMO_MODE:
        return jsonify({
            'success': True,
            'meal_plan_id': 'demo-plan-' + str(datetime.now().timestamp())
        })
    else:
        from auth import login_required, get_current_user_id
        from services.meal_prep_service import MealPrepService
        from database.connection import supabase
        
        @login_required
        def _save_meal_plan():
            try:
                user_id = get_current_user_id()
                data = request.json
                
                prep_service = MealPrepService(supabase)
                result = prep_service.create_meal_plan(user_id, data['meal_plan'])
                
                if result['success']:
                    return jsonify(result)
                else:
                    return jsonify({'error': result.get('error', 'Failed to save')}), 400
                    
            except Exception as e:
                logger.error(f"Error saving meal plan: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        return _save_meal_plan()

@app.route('/api/meal-prep/research-recipe', methods=['POST'])
def research_recipe():
    """Use AI to research nutritional facts for a custom recipe"""
    from services.openai_meal_service import OpenAIMealService
    
    try:
        data = request.json
        ingredients = data.get('ingredients', [])
        servings = data.get('servings', 1)
        
        ai_service = OpenAIMealService()
        nutrition_facts = ai_service.research_nutrition_facts(ingredients, servings)
        
        return jsonify(nutrition_facts)
        
    except Exception as e:
        logger.error(f"Error researching recipe: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/meal-prep/swap-meal', methods=['POST'])
def swap_meal():
    """Swap a meal with an alternative"""
    from services.openai_meal_service import OpenAIMealService
    
    try:
        data = request.json
        current_meal = data.get('current_meal')
        meal_type = data.get('meal_type')
        dietary_requirements = data.get('dietary_requirements', [])
        
        # For now, return a simple alternative
        # In production, this would use AI to generate a suitable alternative
        new_meal = {
            'name': 'Alternative ' + current_meal.get('name', 'Meal'),
            'meal_type': meal_type,
            'calories': current_meal.get('calories', 500),
            'protein_g': current_meal.get('protein_g', 40),
            'carbs_g': current_meal.get('carbs_g', 50),
            'fats_g': current_meal.get('fats_g', 15),
            'time': current_meal.get('time', '12:00 PM'),
            'description': 'A delicious alternative meal',
            'ingredients': [
                {'name': 'Alternative protein', 'amount': 6, 'unit': 'oz'},
                {'name': 'Alternative carb', 'amount': 1, 'unit': 'cup'}
            ],
            'instructions': ['Prepare ingredients', 'Cook and enjoy'],
            'prep_time': 20,
            'cook_time': 25
        }
        
        return jsonify({'new_meal': new_meal})
        
    except Exception as e:
        logger.error(f"Error swapping meal: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/meal-prep/chat', methods=['POST'])
def meal_prep_chat():
    """AI chat assistant for meal prep"""
    from services.openai_meal_service import OpenAIMealService
    
    try:
        data = request.json
        message = data.get('message', '')
        context = data.get('context', {})
        
        # Simple response for now
        # In production, this would use OpenAI to generate contextual responses
        responses = {
            'customize': 'I can help you customize this meal. What dietary preferences or restrictions should I consider?',
            'substitute': 'I can suggest substitutions. What ingredient would you like to replace?',
            'nutrition': 'This meal provides balanced macronutrients optimized for your fitness goals.',
            'default': 'I can help with meal customization, substitutions, or nutritional information. What would you like to know?'
        }
        
        # Simple keyword matching
        response_key = 'default'
        if 'customize' in message.lower():
            response_key = 'customize'
        elif 'substitute' in message.lower() or 'replace' in message.lower():
            response_key = 'substitute'
        elif 'nutrition' in message.lower() or 'calories' in message.lower():
            response_key = 'nutrition'
        
        return jsonify({'response': responses[response_key]})
        
    except Exception as e:
        logger.error(f"Error in meal prep chat: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/recipes/search', methods=['GET'])
def search_recipes():
    """Search saved AI-generated recipes"""
    if DEMO_MODE:
        # Return demo recipes
        return jsonify({
            'recipes': [
                {
                    'id': 'demo-recipe-1',
                    'name': 'Mediterranean Herb-Crusted Chicken with Quinoa',
                    'meal_type': 'lunch',
                    'cuisine_type': 'mediterranean',
                    'calories': 650,
                    'protein_g': 45,
                    'carbs_g': 52,
                    'fats_g': 18,
                    'tags': ['high-protein', 'meal-prep', 'mediterranean'],
                    'average_rating': 4.5,
                    'created_at': datetime.now().isoformat()
                }
            ],
            'total': 1
        })
    else:
        from auth import login_required, get_current_user_id
        from database.connection import supabase
        from database.recipe_storage_db import RecipeStorageDB
        
        @login_required
        def _search_recipes():
            try:
                user_id = get_current_user_id()
                
                # Get search parameters
                search_params = {
                    'name': request.args.get('name'),
                    'meal_type': request.args.get('meal_type'),
                    'cuisine_type': request.args.get('cuisine_type'),
                    'max_calories': request.args.get('max_calories', type=int),
                    'min_protein': request.args.get('min_protein', type=int),
                    'tags': request.args.getlist('tags'),
                    'limit': request.args.get('limit', 20, type=int)
                }
                
                # Remove None values
                search_params = {k: v for k, v in search_params.items() if v}
                
                # Search recipes
                recipes = RecipeStorageDB.search_recipes(supabase, user_id, search_params)
                
                return jsonify({
                    'recipes': recipes,
                    'total': len(recipes)
                })
                
            except Exception as e:
                logger.error(f"Error searching recipes: {str(e)}")
                return jsonify({'error': 'Failed to search recipes'}), 500
        
        return _search_recipes()

@app.route('/api/recipes/<recipe_id>', methods=['GET'])
def get_recipe_details():
    """Get detailed recipe information including ingredients"""
    if DEMO_MODE:
        return jsonify({
            'id': 'demo-recipe-1',
            'name': 'Mediterranean Herb-Crusted Chicken with Quinoa',
            'description': 'A healthy, high-protein meal perfect for meal prep',
            'meal_type': 'lunch',
            'cuisine_type': 'mediterranean',
            'prep_time': 15,
            'cook_time': 25,
            'servings': 1,
            'difficulty': 'medium',
            'calories': 650,
            'protein_g': 45,
            'carbs_g': 52,
            'fats_g': 18,
            'fiber_g': 8,
            'ingredients': [
                {'name': 'Chicken breast', 'quantity': 6, 'unit': 'oz'},
                {'name': 'Quinoa', 'quantity': 1, 'unit': 'cup cooked'},
                {'name': 'Broccoli', 'quantity': 1, 'unit': 'cup'},
                {'name': 'Olive oil', 'quantity': 1, 'unit': 'tbsp'}
            ],
            'instructions': [
                'Marinate chicken in herbs and spices',
                'Cook quinoa according to package directions',
                'Grill chicken until internal temp reaches 165°F',
                'Steam broccoli until tender',
                'Serve together with a drizzle of olive oil'
            ],
            'tags': ['high-protein', 'meal-prep', 'mediterranean'],
            'average_rating': 4.5,
            'created_at': datetime.now().isoformat()
        })
    else:
        from auth import login_required, get_current_user_id
        from database.connection import supabase
        from database.recipe_storage_db import RecipeStorageDB
        
        @login_required
        def _get_recipe_details(recipe_id):
            try:
                recipe = RecipeStorageDB.get_recipe_by_id(supabase, recipe_id)
                
                if not recipe:
                    return jsonify({'error': 'Recipe not found'}), 404
                
                return jsonify(recipe)
                
            except Exception as e:
                logger.error(f"Error getting recipe details: {str(e)}")
                return jsonify({'error': 'Failed to get recipe details'}), 500
        
        return _get_recipe_details(recipe_id)

@app.route('/api/recipes/<recipe_id>/favorite', methods=['POST'])
def add_recipe_to_favorites():
    """Add a recipe to user's favorites"""
    if DEMO_MODE:
        return jsonify({'success': True, 'message': 'Recipe added to favorites'})
    else:
        from auth import login_required, get_current_user_id
        from database.connection import supabase
        from database.recipe_storage_db import RecipeStorageDB
        
        @login_required
        def _add_to_favorites(recipe_id):
            try:
                user_id = get_current_user_id()
                data = request.json
                
                success = RecipeStorageDB.add_recipe_to_collection(
                    supabase,
                    user_id,
                    recipe_id,
                    'favorites',
                    data.get('notes')
                )
                
                if success:
                    return jsonify({'success': True, 'message': 'Recipe added to favorites'})
                else:
                    return jsonify({'error': 'Failed to add to favorites'}), 400
                    
            except Exception as e:
                logger.error(f"Error adding to favorites: {str(e)}")
                return jsonify({'error': 'Failed to add to favorites'}), 500
        
        return _add_to_favorites(recipe_id)

@app.route('/api/recipes/generation-history', methods=['GET'])
def get_generation_history():
    """Get user's meal generation history"""
    if DEMO_MODE:
        return jsonify({
            'history': [{
                'id': 'demo-history-1',
                'generation_date': datetime.now().isoformat(),
                'generation_type': '7_day',
                'total_recipes': 21,
                'dietary_requirements': ['vegetarian'],
                'budget': 150.00
            }],
            'total': 1
        })
    else:
        from auth import login_required, get_current_user_id
        from database.connection import supabase
        from database.recipe_storage_db import RecipeStorageDB
        
        @login_required
        def _get_generation_history():
            try:
                user_id = get_current_user_id()
                limit = request.args.get('limit', 10, type=int)
                
                history = RecipeStorageDB.get_user_generation_history(supabase, user_id, limit)
                
                return jsonify({
                    'history': history,
                    'total': len(history)
                })
                
            except Exception as e:
                logger.error(f"Error getting generation history: {str(e)}")
                return jsonify({'error': 'Failed to get generation history'}), 500
        
        return _get_generation_history()

# Error handlers
@app.errorhandler(404)
def not_found(error):
    logger.error(f"404 error: {error}")
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"500 error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Run development server
    import os
    port = int(os.environ.get('PORT', 8000))
    app.run(debug=True, host='0.0.0.0', port=port)