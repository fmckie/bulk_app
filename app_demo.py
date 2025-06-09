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

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)