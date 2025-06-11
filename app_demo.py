from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from flask_cors import CORS
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'

# Enable CORS for API endpoints
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Import demo routes
from demo_routes import demo_bp
app.register_blueprint(demo_bp)

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
        'message': 'Kinobody Tracker API is running',
        'mode': 'demo',
        'database': 'demo mode - in memory'
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

@app.route('/meal-prep')
def meal_prep():
    """AI-Powered Meal Prep Planner page"""
    return render_template('meal-prep.html')

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
        'body_weight': profile['body_weight'],
        'age': profile['age'],
        'gender': profile['gender'],
        'dietary_requirements': data.get('dietary_requirements', []),
        'budget': data.get('budget', 150),
        'store_preference': data.get('store_preference', 'Whole Foods'),
        'exclusions': data.get('exclusions', []),
        'cooking_time': data.get('cooking_time', 45),
        'variety': data.get('variety', 'medium'),
        'training_days': ['Monday', 'Wednesday', 'Friday']
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
        'body_weight': profile['body_weight'],
        'age': profile['age'],
        'gender': profile['gender'],
        'dietary_requirements': data.get('dietary_requirements', []),
        'budget': data.get('budget', 150),
        'store_preference': data.get('store_preference', 'Local Grocery'),
        'training_days': ['Monday', 'Wednesday', 'Friday']
    }
    
    meal_plan = ai_service.generate_meal_plan(user_data)
    return jsonify(meal_plan)

@app.route('/api/meal-prep/plans', methods=['GET'])
def get_meal_plans():
    """Get user's saved meal plans"""
    return jsonify([
        {
            'id': 'demo-plan-1',
            'name': 'Demo Meal Plan - Week 1',
            'created_at': datetime.now().isoformat(),
            'status': 'active',
            'budget': 150
        }
    ])

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)