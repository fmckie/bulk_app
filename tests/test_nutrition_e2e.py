"""
End-to-end tests for nutrition feature user workflows
"""
import pytest
from datetime import date, timedelta
import json

class TestNutritionE2E:
    """Test complete user workflows for nutrition tracking"""
    
    def test_daily_nutrition_workflow(self, auth_client, clear_demo_data):
        """Test a typical daily nutrition tracking workflow"""
        today = date.today().isoformat()
        
        # Step 1: User logs morning workout
        workout_data = {
            'date': today,
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
                },
                {
                    'exercise_slug': 'incline-bench',
                    'set_number': 3,
                    'weight': 185,
                    'reps': 8
                }
            ]
        }
        response = auth_client.post('/api/demo/workouts', json=workout_data)
        assert response.status_code == 200
        
        # Step 2: User checks nutrition targets for the day
        response = auth_client.get(f'/api/demo/nutrition/targets?date={today}')
        targets = response.get_json()
        assert targets['is_training_day'] == True
        assert targets['targets']['calories'] == 3125
        
        # Step 3: User logs breakfast
        breakfast = {
            'date': today,
            'calories': 800,
            'protein': 50,
            'carbs': 100,
            'fats': 20,
            'notes': 'Oatmeal with protein powder and berries'
        }
        response = auth_client.post('/api/demo/nutrition', json=breakfast)
        assert response.status_code == 200
        
        # Step 4: User logs lunch (updating totals)
        lunch_totals = {
            'date': today,
            'calories': 1600,  # 800 + 800
            'protein': 100,    # 50 + 50
            'carbs': 180,      # 100 + 80
            'fats': 45,        # 20 + 25
            'notes': 'Chicken breast with rice and vegetables'
        }
        response = auth_client.post('/api/demo/nutrition', json=lunch_totals)
        assert response.status_code == 200
        
        # Step 5: User logs dinner (final update)
        final_totals = {
            'date': today,
            'calories': 3125,  # Hit target exactly
            'protein': 175,    # Hit target
            'carbs': 411,      # Hit target
            'fats': 87,        # Hit target
            'notes': 'Steak with sweet potato, followed by Greek yogurt'
        }
        response = auth_client.post('/api/demo/nutrition', json=final_totals)
        assert response.status_code == 200
        
        # Step 6: User reviews the day
        response = auth_client.get(f'/api/demo/nutrition/{today}')
        final_data = response.get_json()
        assert final_data['calories'] == targets['targets']['calories']
        assert final_data['protein_g'] == targets['targets']['protein']
        assert final_data['is_training_day'] == True
    
    def test_weekly_review_workflow(self, auth_client, clear_demo_data):
        """Test reviewing a week of nutrition data"""
        # Simulate a week of tracking
        for i in range(7):
            day = (date.today() - timedelta(days=i)).isoformat()
            is_training = i % 3 == 0  # Every 3rd day is training
            
            if is_training:
                # Log workout
                workout = {
                    'date': day,
                    'sets': [{
                        'exercise_slug': 'weighted-chins',
                        'set_number': 1,
                        'weight': 90,
                        'reps': 5
                    }]
                }
                auth_client.post('/api/demo/workouts', json=workout)
            
            # Log nutrition (varying adherence)
            if i == 0:  # Today - perfect
                calories = 3125 if is_training else 2725
            elif i == 1:  # Yesterday - slightly over
                calories = 3200 if is_training else 2800
            elif i == 2:  # 2 days ago - slightly under
                calories = 3000 if is_training else 2600
            else:  # Older days - on target
                calories = 3125 if is_training else 2725
            
            nutrition = {
                'date': day,
                'calories': calories,
                'protein': 175,
                'carbs': 400 if is_training else 325,
                'fats': 85 if is_training else 75
            }
            auth_client.post('/api/demo/nutrition', json=nutrition)
        
        # Review the week
        response = auth_client.get('/api/demo/nutrition/history?days=7')
        history = response.get_json()
        
        assert len(history) == 7
        
        # Calculate weekly averages
        total_calories = sum(entry['calories'] for entry in history)
        avg_calories = total_calories / 7
        
        # With 3 training days and 4 rest days:
        # Expected average: (3*3125 + 4*2725) / 7 ≈ 2896
        # But we have some variation in our test data
        assert 2850 <= avg_calories <= 2950
    
    def test_missed_day_recovery_workflow(self, auth_client, clear_demo_data):
        """Test handling missed tracking days"""
        today = date.today()
        
        # User tracked 3 days ago
        three_days_ago = (today - timedelta(days=3)).isoformat()
        old_nutrition = {
            'date': three_days_ago,
            'calories': 2725,
            'protein': 175,
            'carbs': 336,
            'fats': 76
        }
        auth_client.post('/api/demo/nutrition', json=old_nutrition)
        
        # User returns today and wants to check history
        response = auth_client.get('/api/demo/nutrition/history?days=7')
        history = response.get_json()
        
        # Should only have 1 entry (3 days ago)
        assert len(history) == 1
        assert history[0]['date'] == three_days_ago
        
        # User checks today's targets
        response = auth_client.get('/api/demo/nutrition/targets')
        targets = response.get_json()
        assert 'targets' in targets
        
        # User logs today's nutrition
        today_nutrition = {
            'date': today.isoformat(),
            'calories': targets['targets']['calories'],
            'protein': targets['targets']['protein'],
            'carbs': targets['targets']['carbs'],
            'fats': targets['targets']['fats'],
            'notes': 'Back on track!'
        }
        response = auth_client.post('/api/demo/nutrition', json=today_nutrition)
        assert response.status_code == 200
    
    def test_calorie_cycling_week(self, auth_client, clear_demo_data):
        """Test a proper calorie cycling week (Mon/Wed/Fri training)"""
        # Use fixed dates to avoid test flakiness
        base_date = date(2024, 1, 15)  # A Monday
        
        week_plan = [
            ('Monday', True, 'Workout A'),
            ('Tuesday', False, 'Rest'),
            ('Wednesday', True, 'Workout B'),
            ('Thursday', False, 'Rest'),
            ('Friday', True, 'Workout C'),
            ('Saturday', False, 'Rest'),
            ('Sunday', False, 'Rest')
        ]
        
        for i, (day_name, is_training, note) in enumerate(week_plan):
            day_date = (base_date + timedelta(days=i)).isoformat()
            
            if is_training:
                # Log workout
                workout = {
                    'date': day_date,
                    'sets': [{
                        'exercise_slug': 'incline-bench',
                        'set_number': 1,
                        'weight': 225,
                        'reps': 5
                    }]
                }
                auth_client.post('/api/demo/workouts', json=workout)
            
            # Get targets for the day
            response = auth_client.get(f'/api/demo/nutrition/targets?date={day_date}')
            targets = response.get_json()
            
            # Log nutrition matching targets
            nutrition = {
                'date': day_date,
                'calories': targets['targets']['calories'],
                'protein': targets['targets']['protein'],
                'carbs': targets['targets']['carbs'],
                'fats': targets['targets']['fats'],
                'notes': f'{day_name}: {note}'
            }
            response = auth_client.post('/api/demo/nutrition', json=nutrition)
            assert response.status_code == 200
        
        # Get all logged nutrition to verify
        logged_data = []
        for i in range(7):
            day_date = (base_date + timedelta(days=i)).isoformat()
            response = auth_client.get(f'/api/demo/nutrition/{day_date}')
            if response.status_code == 200:
                logged_data.append(response.get_json())
        
        # Count training vs rest days
        training_days = sum(1 for entry in logged_data if entry['is_training_day'])
        rest_days = len(logged_data) - training_days
        
        assert training_days == 3
        assert rest_days == 4
        
        # Verify calorie cycling pattern
        for entry in logged_data:
            if entry['is_training_day']:
                assert entry['calories'] == 3125
            else:
                assert entry['calories'] == 2725
    
    def test_progress_check_workflow(self, auth_client, clear_demo_data):
        """Test checking adherence and progress"""
        # Log a week with varying adherence
        adherence_data = [
            {'offset': 0, 'adherence': 100},  # Today - perfect
            {'offset': 1, 'adherence': 95},   # Slightly under
            {'offset': 2, 'adherence': 105},  # Slightly over
            {'offset': 3, 'adherence': 90},   # Under target
            {'offset': 4, 'adherence': 110},  # Over target
            {'offset': 5, 'adherence': 100},  # Perfect
            {'offset': 6, 'adherence': 98},   # Close
        ]
        
        for data in adherence_data:
            day = (date.today() - timedelta(days=data['offset'])).isoformat()
            is_training = data['offset'] % 3 == 0
            
            base_calories = 3125 if is_training else 2725
            actual_calories = int(base_calories * data['adherence'] / 100)
            
            nutrition = {
                'date': day,
                'calories': actual_calories,
                'protein': 175,
                'carbs': 400 if is_training else 325,
                'fats': 85 if is_training else 75
            }
            auth_client.post('/api/demo/nutrition', json=nutrition)
        
        # Get history to analyze
        response = auth_client.get('/api/demo/nutrition/history?days=7')
        history = response.get_json()
        
        # Calculate adherence stats
        perfect_days = sum(1 for entry in history 
                          if entry['calories'] in [3125, 2725])
        
        within_5_percent = sum(1 for entry in history
                              if 0.95 <= entry['calories'] / (3125 if entry.get('is_training_day') else 2725) <= 1.05)
        
        assert perfect_days >= 2  # At least 2 perfect days
        assert within_5_percent >= 3  # At least 3 days within 5% of target (adjusted for test data)