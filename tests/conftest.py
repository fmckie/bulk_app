"""
Pytest configuration and fixtures for testing
"""
import pytest
import os
import sys
from datetime import datetime, date
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app as flask_app
from demo_routes import demo_bp

@pytest.fixture
def app():
    """Create and configure a test app instance"""
    flask_app.config.update({
        'TESTING': True,
        'SECRET_KEY': 'test-secret-key',
        'WTF_CSRF_ENABLED': False
    })
    
    # Ensure demo mode is active for tests
    if not hasattr(flask_app, 'blueprints') or 'demo' not in flask_app.blueprints:
        flask_app.register_blueprint(demo_bp)
    
    yield flask_app

@pytest.fixture
def client(app):
    """Create a test client"""
    return app.test_client()

@pytest.fixture
def auth_client(client):
    """Create an authenticated test client"""
    # Sign in with demo credentials
    response = client.post('/api/demo/auth/signin', 
        json={'email': 'wfmckie@gmail.com', 'password': '123456'},
        content_type='application/json'
    )
    assert response.status_code == 200
    return client

@pytest.fixture
def sample_nutrition_data():
    """Sample nutrition data for testing"""
    return {
        'date': date.today().isoformat(),
        'calories': 2500,
        'protein': 175,
        'carbs': 300,
        'fats': 70,
        'notes': 'Test nutrition entry'
    }

@pytest.fixture
def sample_workout_data():
    """Sample workout data for testing"""
    return {
        'date': date.today().isoformat(),
        'sets': [
            {
                'exercise_slug': 'incline-bench',
                'set_number': 1,
                'weight': 225,
                'reps': 5
            },
            {
                'exercise_slug': 'incline-bench',
                'set_number': 2,
                'weight': 205,
                'reps': 6
            }
        ]
    }

@pytest.fixture
def demo_user_profile():
    """Demo user profile data"""
    return {
        'id': 'demo-user-123',
        'email': 'wfmckie@gmail.com',
        'profile': {
            'username': 'willmckie',
            'full_name': 'Will McKie',
            'body_weight': 175
        }
    }

@pytest.fixture
def training_day_targets():
    """Expected nutrition targets for training days"""
    body_weight = 175
    maintenance = body_weight * 15
    calories = maintenance + 500
    protein = body_weight * 1.0
    fats = calories * 0.25 / 9
    carbs = (calories - (protein * 4) - (fats * 9)) / 4
    
    return {
        'calories': round(calories),
        'protein': round(protein),
        'carbs': round(carbs),
        'fats': round(fats),
        'maintenance': round(maintenance),
        'surplus': 500
    }

@pytest.fixture
def rest_day_targets():
    """Expected nutrition targets for rest days"""
    body_weight = 175
    maintenance = body_weight * 15
    calories = maintenance + 100
    protein = body_weight * 1.0
    fats = calories * 0.25 / 9
    carbs = (calories - (protein * 4) - (fats * 9)) / 4
    
    return {
        'calories': round(calories),
        'protein': round(protein),
        'carbs': round(carbs),
        'fats': round(fats),
        'maintenance': round(maintenance),
        'surplus': 100
    }

@pytest.fixture
def clear_demo_data():
    """Clear demo data before and after tests"""
    # Import here to avoid circular imports
    from demo_routes import demo_workouts, demo_nutrition
    
    # Clear before test
    demo_workouts.clear()
    demo_nutrition.clear()
    
    yield
    
    # Clear after test
    demo_workouts.clear()
    demo_nutrition.clear()