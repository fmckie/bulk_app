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

@demo_bp.route('/auth/signin', methods=['POST'])
def demo_signin():
    """Demo sign in (no real authentication)"""
    return jsonify({
        'success': True,
        'message': 'Demo mode - no authentication required',
        'user': {
            'id': 'demo-user',
            'email': 'demo@kinobody.com'
        }
    })

@demo_bp.route('/auth/user', methods=['GET'])
def demo_get_user():
    """Get demo user info"""
    return jsonify({
        'id': 'demo-user',
        'profile': {
            'email': 'demo@kinobody.com',
            'username': 'demo_user',
            'full_name': 'Demo User',
            'body_weight': 180
        }
    })