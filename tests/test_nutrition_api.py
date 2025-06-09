"""
Test nutrition API endpoints
"""
import pytest
from datetime import date, timedelta
import json

class TestNutritionAPI:
    """Test nutrition API endpoints"""
    
    def test_save_nutrition_unauthenticated(self, client):
        """Test saving nutrition without authentication"""
        response = client.post('/api/nutrition', 
            json={'calories': 2500, 'protein': 175},
            content_type='application/json'
        )
        # In demo mode, should redirect to demo API
        assert response.status_code in [307, 302]
        # Check if it redirects to demo endpoint
        if hasattr(response, 'location'):
            assert '/api/demo/nutrition' in response.location
    
    def test_save_nutrition_demo_mode(self, auth_client, clear_demo_data):
        """Test saving nutrition data in demo mode"""
        data = {
            'date': date.today().isoformat(),
            'calories': 2500,
            'protein': 175,
            'carbs': 300,
            'fats': 70,
            'notes': 'Good day of eating'
        }
        
        response = auth_client.post('/api/demo/nutrition',
            json=data,
            content_type='application/json'
        )
        
        assert response.status_code == 200
        result = response.get_json()
        assert result['status'] == 'success'
        assert result['data']['calories'] == 2500
        assert result['data']['protein_g'] == 175
        assert result['data']['carbs_g'] == 300
        assert result['data']['fats_g'] == 70
    
    def test_get_nutrition_by_date(self, auth_client, clear_demo_data):
        """Test retrieving nutrition data by date"""
        # First save some data
        test_date = date.today().isoformat()
        data = {
            'date': test_date,
            'calories': 2500,
            'protein': 175,
            'carbs': 300,
            'fats': 70
        }
        
        auth_client.post('/api/demo/nutrition', json=data)
        
        # Then retrieve it
        response = auth_client.get(f'/api/demo/nutrition/{test_date}')
        assert response.status_code == 200
        
        result = response.get_json()
        assert result['date'] == test_date
        assert result['calories'] == 2500
        assert result['protein_g'] == 175
        assert result['carbs_g'] == 300
        assert result['fats_g'] == 70
    
    def test_get_nutrition_nonexistent_date(self, auth_client):
        """Test retrieving nutrition for date with no data"""
        future_date = (date.today() + timedelta(days=30)).isoformat()
        response = auth_client.get(f'/api/demo/nutrition/{future_date}')
        
        assert response.status_code == 200
        result = response.get_json()
        assert result['date'] == future_date
        assert result['calories'] is None
        assert result['protein_g'] is None
        assert result['carbs_g'] is None
        assert result['fats_g'] is None
    
    def test_nutrition_history(self, auth_client, clear_demo_data):
        """Test retrieving nutrition history"""
        # Save data for multiple days
        for i in range(3):
            test_date = (date.today() - timedelta(days=i)).isoformat()
            data = {
                'date': test_date,
                'calories': 2500 + (i * 100),
                'protein': 175,
                'carbs': 300,
                'fats': 70
            }
            auth_client.post('/api/demo/nutrition', json=data)
        
        # Get history
        response = auth_client.get('/api/demo/nutrition/history?days=7')
        assert response.status_code == 200
        
        history = response.get_json()
        assert len(history) == 3
        # History should be ordered by date descending
        assert history[0]['calories'] == 2500  # Today
        assert history[1]['calories'] == 2600  # Yesterday
        assert history[2]['calories'] == 2700  # 2 days ago
    
    def test_nutrition_targets_rest_day(self, auth_client, rest_day_targets):
        """Test nutrition targets calculation for rest days"""
        response = auth_client.get('/api/demo/nutrition/targets')
        assert response.status_code == 200
        
        result = response.get_json()
        assert result['is_training_day'] == False
        assert result['body_weight'] == 175
        assert result['targets']['calories'] == rest_day_targets['calories']
        assert result['targets']['protein'] == rest_day_targets['protein']
        assert result['targets']['carbs'] == rest_day_targets['carbs']
        assert result['targets']['fats'] == rest_day_targets['fats']
        assert result['calorie_surplus'] == 100
    
    def test_nutrition_targets_training_day(self, auth_client, training_day_targets, clear_demo_data):
        """Test nutrition targets calculation for training days"""
        # First log a workout for today
        workout_data = {
            'date': date.today().isoformat(),
            'sets': [{
                'exercise_slug': 'incline-bench',
                'set_number': 1,
                'weight': 225,
                'reps': 5
            }]
        }
        auth_client.post('/api/demo/workouts', json=workout_data)
        
        # Then get nutrition targets
        response = auth_client.get('/api/demo/nutrition/targets')
        assert response.status_code == 200
        
        result = response.get_json()
        assert result['is_training_day'] == True
        assert result['body_weight'] == 175
        assert result['targets']['calories'] == training_day_targets['calories']
        assert result['targets']['protein'] == training_day_targets['protein']
        assert result['targets']['carbs'] == training_day_targets['carbs']
        assert result['targets']['fats'] == training_day_targets['fats']
        assert result['calorie_surplus'] == 500
    
    def test_nutrition_targets_specific_date(self, auth_client):
        """Test nutrition targets for a specific date"""
        specific_date = '2024-01-15'
        response = auth_client.get(f'/api/demo/nutrition/targets?date={specific_date}')
        
        assert response.status_code == 200
        result = response.get_json()
        assert 'targets' in result
        assert 'body_weight' in result
    
    def test_training_day_detection(self, auth_client, clear_demo_data):
        """Test that training day is properly detected"""
        test_date = date.today().isoformat()
        
        # Initially no workout - should be rest day
        response = auth_client.get(f'/api/demo/nutrition/{test_date}')
        result = response.get_json()
        assert result['is_training_day'] == False
        
        # Log a workout
        workout_data = {
            'date': test_date,
            'sets': [{
                'exercise_slug': 'incline-bench',
                'set_number': 1,
                'weight': 225,
                'reps': 5
            }]
        }
        auth_client.post('/api/demo/workouts', json=workout_data)
        
        # Now should be training day
        response = auth_client.get(f'/api/demo/nutrition/{test_date}')
        result = response.get_json()
        assert result['is_training_day'] == True
    
    def test_save_nutrition_updates_training_status(self, auth_client, clear_demo_data):
        """Test that saving nutrition preserves training day status"""
        test_date = date.today().isoformat()
        
        # Log a workout first
        workout_data = {
            'date': test_date,
            'sets': [{
                'exercise_slug': 'standing-press',
                'set_number': 1,
                'weight': 135,
                'reps': 5
            }]
        }
        auth_client.post('/api/demo/workouts', json=workout_data)
        
        # Save nutrition
        nutrition_data = {
            'date': test_date,
            'calories': 3125,  # Training day calories
            'protein': 175,
            'carbs': 400,
            'fats': 87
        }
        response = auth_client.post('/api/demo/nutrition', json=nutrition_data)
        
        assert response.status_code == 200
        result = response.get_json()
        assert result['data']['is_training_day'] == True