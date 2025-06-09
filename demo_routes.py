"""
Demo routes for testing without Supabase connection
These routes allow testing the app without setting up authentication
"""
from flask import Blueprint, jsonify, request
from datetime import datetime
import uuid

demo_bp = Blueprint('demo', __name__, url_prefix='/api/demo')

# Demo data storage (in-memory)
demo_workouts = []
demo_nutrition = {}  # Store by date
demo_exercises = [
    {'id': '1', 'name': 'Incline Barbell Bench Press', 'slug': 'incline-bench', 'category': 'indicator', 'muscle_group': 'chest'},
    {'id': '2', 'name': 'Standing Shoulder Press', 'slug': 'standing-press', 'category': 'indicator', 'muscle_group': 'shoulders'},
    {'id': '3', 'name': 'Weighted Chin-ups', 'slug': 'weighted-chins', 'category': 'indicator', 'muscle_group': 'back'},
    {'id': '4', 'name': 'Power Cleans (Hang)', 'slug': 'power-cleans', 'category': 'indicator', 'muscle_group': 'legs'},
    {'id': '5', 'name': 'Weighted Dips', 'slug': 'weighted-dips', 'category': 'assistance', 'muscle_group': 'chest'},
    {'id': '6', 'name': 'Close Grip Bench Press', 'slug': 'close-grip-bench', 'category': 'assistance', 'muscle_group': 'triceps'},
    {'id': '7', 'name': 'Barbell Curls', 'slug': 'barbell-curls', 'category': 'assistance', 'muscle_group': 'biceps'},
    {'id': '8', 'name': 'Incline Dumbbell Curls', 'slug': 'incline-db-curls', 'category': 'assistance', 'muscle_group': 'biceps'},
    {'id': '9', 'name': 'Skull Crushers', 'slug': 'skull-crushers', 'category': 'assistance', 'muscle_group': 'triceps'},
    {'id': '10', 'name': 'Rope Extensions', 'slug': 'rope-extensions', 'category': 'assistance', 'muscle_group': 'triceps'},
    {'id': '11', 'name': 'Lateral Raises', 'slug': 'lateral-raises', 'category': 'assistance', 'muscle_group': 'shoulders'},
    {'id': '12', 'name': 'Bent Over Flyes', 'slug': 'bent-over-flyes', 'category': 'assistance', 'muscle_group': 'shoulders'},
    {'id': '13', 'name': 'Pistol Squats', 'slug': 'pistol-squats', 'category': 'assistance', 'muscle_group': 'legs'},
    {'id': '14', 'name': 'Single Leg Calf Raises', 'slug': 'calf-raises', 'category': 'assistance', 'muscle_group': 'legs'}
]

demo_prs = {
    'incline-bench': {'weight': 225, 'reps': 5, 'date': '2024-01-01'},
    'standing-press': {'weight': 155, 'reps': 5, 'date': '2024-01-01'},
    'weighted-chins': {'weight': 90, 'reps': 5, 'date': '2024-01-01'}
}

# Demo user for testing
demo_user = {
    'id': 'demo-user-123',
    'email': 'wfmckie@gmail.com',
    'password': '123456',  # In real app, this would be hashed
    'profile': {
        'username': 'willmckie',
        'full_name': 'Will McKie',
        'body_weight': 175
    }
}

@demo_bp.route('/auth/signin', methods=['POST'])
def demo_signin():
    """Sign in a user (demo mode)"""
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        
        # Check demo credentials
        if email == demo_user['email'] and password == demo_user['password']:
            from flask import session
            # Store in session
            session['access_token'] = 'demo-token-123'
            session['user_email'] = email
            session['demo_mode'] = True
            
            return jsonify({
                'success': True,
                'message': 'Signed in successfully (demo mode)',
                'user': {
                    'id': demo_user['id'],
                    'email': demo_user['email']
                }
            })
        else:
            return jsonify({'error': 'Invalid email or password'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@demo_bp.route('/auth/signup', methods=['POST'])
def demo_signup():
    """Sign up a new user (demo mode)"""
    try:
        data = request.json
        
        # In demo mode, just pretend to create user
        return jsonify({
            'success': True,
            'message': 'Account created successfully (demo mode)',
            'user': {
                'id': str(uuid.uuid4()),
                'email': data.get('email')
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@demo_bp.route('/auth/signout', methods=['POST'])
def demo_signout():
    """Sign out the current user (demo mode)"""
    from flask import session
    session.clear()
    return jsonify({
        'success': True,
        'message': 'Signed out successfully'
    })

@demo_bp.route('/auth/user', methods=['GET'])
def demo_get_user():
    """Get current user info (demo mode)"""
    from flask import session
    if session.get('demo_mode'):
        return jsonify({
            'id': demo_user['id'],
            'profile': demo_user['profile']
        })
    else:
        return jsonify({'error': 'Authentication required'}), 401

@demo_bp.route('/workouts', methods=['POST'])
def demo_log_workout():
    """Save a workout session (demo mode)"""
    try:
        data = request.json
        
        # Create workout
        workout_id = str(uuid.uuid4())
        date = data.get('date', datetime.now().date().isoformat())
        
        # Process sets
        exercises = {}
        for set_data in data.get('sets', []):
            exercise_slug = set_data['exercise_slug']
            
            # Find exercise
            exercise = next((e for e in demo_exercises if e['slug'] == exercise_slug), None)
            if not exercise:
                continue
                
            if exercise_slug not in exercises:
                exercises[exercise_slug] = {
                    'name': exercise['name'],
                    'slug': exercise_slug,
                    'sets': []
                }
            
            exercises[exercise_slug]['sets'].append({
                'set_number': set_data['set_number'],
                'weight': set_data['weight'],
                'reps': set_data['reps']
            })
            
            # Update PR if applicable
            current_pr = demo_prs.get(exercise_slug, {'weight': 0, 'reps': 0})
            if set_data['weight'] > current_pr['weight'] or \
               (set_data['weight'] == current_pr['weight'] and set_data['reps'] > current_pr['reps']):
                demo_prs[exercise_slug] = {
                    'weight': set_data['weight'],
                    'reps': set_data['reps'],
                    'date': date
                }
        
        workout = {
            'id': workout_id,
            'date': date,
            'exercises': list(exercises.values())
        }
        
        demo_workouts.append(workout)
        
        return jsonify({
            'status': 'success',
            'message': 'Workout saved successfully (demo mode)',
            'workout_id': workout_id
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@demo_bp.route('/workouts/recent', methods=['GET'])
def demo_get_recent_workouts():
    """Get recent workout history (demo mode)"""
    limit = request.args.get('limit', 10, type=int)
    
    # Sort by date descending
    sorted_workouts = sorted(demo_workouts, key=lambda x: x['date'], reverse=True)
    
    return jsonify(sorted_workouts[:limit])

@demo_bp.route('/exercises', methods=['GET'])
def demo_get_exercises():
    """Get list of exercises (demo mode)"""
    exercises = {
        'indicator': [],
        'assistance': []
    }
    
    for exercise in demo_exercises:
        exercise_data = {
            'id': exercise['id'],
            'name': exercise['name'],
            'slug': exercise['slug'],
            'category': exercise['muscle_group']
        }
        
        if exercise['category'] == 'indicator':
            exercises['indicator'].append(exercise_data)
        else:
            exercises['assistance'].append(exercise_data)
    
    return jsonify(exercises)

@demo_bp.route('/personal-records', methods=['GET'])
def demo_get_personal_records():
    """Get personal records (demo mode)"""
    return jsonify(demo_prs)

# Nutrition Routes
@demo_bp.route('/nutrition', methods=['POST'])
def demo_save_nutrition():
    """Save daily nutrition data (demo mode)"""
    try:
        data = request.json
        date = data.get('date', datetime.now().date().isoformat())
        
        # Check if workout exists for this date to determine if it's a training day
        is_training_day = any(w['date'] == date for w in demo_workouts)
        
        nutrition_data = {
            'date': date,
            'calories': data.get('calories', 0),
            'protein_g': data.get('protein', 0),
            'carbs_g': data.get('carbs', 0),
            'fats_g': data.get('fats', 0),
            'notes': data.get('notes', ''),
            'is_training_day': is_training_day
        }
        
        demo_nutrition[date] = nutrition_data
        
        return jsonify({
            'status': 'success',
            'message': 'Nutrition saved successfully (demo mode)',
            'data': nutrition_data
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@demo_bp.route('/nutrition/<date>', methods=['GET'])
def demo_get_nutrition(date):
    """Get nutrition data for a specific date (demo mode)"""
    nutrition = demo_nutrition.get(date)
    
    if nutrition:
        # Update training day status
        nutrition['is_training_day'] = any(w['date'] == date for w in demo_workouts)
        return jsonify(nutrition)
    else:
        # Check if it's a training day even if no nutrition logged
        is_training_day = any(w['date'] == date for w in demo_workouts)
        return jsonify({
            'date': date,
            'is_training_day': is_training_day,
            'calories': None,
            'protein_g': None,
            'carbs_g': None,
            'fats_g': None
        })

@demo_bp.route('/nutrition/history', methods=['GET'])
def demo_get_nutrition_history():
    """Get nutrition history (demo mode)"""
    days = request.args.get('days', 7, type=int)
    
    # Get dates for the last N days
    from datetime import datetime, timedelta
    end_date = datetime.now().date()
    
    history = []
    for i in range(days):
        date = (end_date - timedelta(days=i)).isoformat()
        nutrition = demo_nutrition.get(date)
        if nutrition:
            nutrition['is_training_day'] = any(w['date'] == date for w in demo_workouts)
            history.append(nutrition)
    
    return jsonify(history)

@demo_bp.route('/nutrition/targets', methods=['GET'])
def demo_get_nutrition_targets():
    """Calculate daily nutrition targets (demo mode)"""
    date = request.args.get('date', datetime.now().date().isoformat())
    
    # Use demo user's body weight
    body_weight = demo_user['profile']['body_weight']
    
    # Check if today is a training day
    is_training_day = any(w['date'] == date for w in demo_workouts)
    
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