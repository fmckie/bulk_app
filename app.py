from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import os
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

# Enable CORS for API endpoints
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Routes
@app.route('/')
def index():
    """Home page - Dashboard"""
    current_date = datetime.now().strftime('%A, %B %d, %Y')
    return render_template('index.html', current_date=current_date)

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'Kinobody Tracker API is running'
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
@app.route('/api/workouts', methods=['POST'])
def log_workout():
    """Save a workout session"""
    try:
        data = request.json
        # In a real app, this would save to Supabase
        # For now, we'll just return success
        return jsonify({
            'status': 'success',
            'message': 'Workout saved successfully',
            'workout_id': 'demo_' + datetime.now().strftime('%Y%m%d%H%M%S')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/workouts/recent', methods=['GET'])
def get_recent_workouts():
    """Get recent workout history"""
    # Demo data - in production this would query Supabase
    demo_workouts = [
        {
            'date': '2024-01-08',
            'exercises': [
                {
                    'name': 'Incline Barbell Bench Press',
                    'sets': [
                        {'weight': 185, 'reps': 5},
                        {'weight': 165, 'reps': 6},
                        {'weight': 150, 'reps': 8}
                    ]
                }
            ]
        }
    ]
    return jsonify(demo_workouts)

@app.route('/api/exercises', methods=['GET'])
def get_exercises():
    """Get list of exercises"""
    exercises = {
        'indicator': [
            {'id': 1, 'name': 'Incline Barbell Bench Press', 'category': 'chest'},
            {'id': 2, 'name': 'Standing Shoulder Press', 'category': 'shoulders'},
            {'id': 3, 'name': 'Weighted Chin-ups', 'category': 'back'},
            {'id': 4, 'name': 'Power Cleans (Hang)', 'category': 'legs'}
        ],
        'assistance': [
            {'id': 5, 'name': 'Weighted Dips', 'category': 'chest'},
            {'id': 6, 'name': 'Close Grip Bench Press', 'category': 'triceps'},
            {'id': 7, 'name': 'Barbell Curls', 'category': 'biceps'},
            {'id': 8, 'name': 'Incline Dumbbell Curls', 'category': 'biceps'},
            {'id': 9, 'name': 'Skull Crushers', 'category': 'triceps'},
            {'id': 10, 'name': 'Rope Extensions', 'category': 'triceps'},
            {'id': 11, 'name': 'Lateral Raises', 'category': 'shoulders'},
            {'id': 12, 'name': 'Bent Over Flyes', 'category': 'shoulders'},
            {'id': 13, 'name': 'Pistol Squats', 'category': 'legs'},
            {'id': 14, 'name': 'Single Leg Calf Raises', 'category': 'legs'}
        ]
    }
    return jsonify(exercises)

@app.route('/api/personal-records', methods=['GET'])
def get_personal_records():
    """Get personal records for exercises"""
    # Demo data - in production this would query Supabase
    prs = {
        'incline-bench': 225,
        'standing-press': 155,
        'weighted-chins': 90,
        'weighted-dips': 90
    }
    return jsonify(prs)

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