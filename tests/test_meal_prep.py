"""
Tests for meal prep functionality
"""
import pytest
from unittest.mock import Mock, patch
from services.openai_meal_service import OpenAIMealService
from services.meal_prep_service import MealPrepService


class TestOpenAIMealService:
    """Test OpenAI meal service"""
    
    def test_init_without_api_key(self):
        """Test initialization without API key"""
        with patch.dict('os.environ', {}, clear=True):
            service = OpenAIMealService()
            assert service.client is None
            assert not service.is_available()
    
    def test_init_with_api_key(self):
        """Test initialization with API key"""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            service = OpenAIMealService()
            assert service.client is not None
            assert service.is_available()
    
    def test_demo_meal_plan_generation(self):
        """Test demo meal plan generation when AI is not available"""
        with patch.dict('os.environ', {}, clear=True):
            service = OpenAIMealService()
            user_data = {
                'body_weight': 175,
                'age': 25,
                'gender': 'male',
                'dietary_requirements': [],
                'budget': 150,
                'store_preference': 'Local Grocery'
            }
            
            meal_plan = service.generate_meal_plan(user_data)
            
            assert 'meal_plan' in meal_plan
            assert 'shopping_list' in meal_plan
            assert meal_plan['demo_mode'] is True
            assert meal_plan['total_estimated_cost'] == 120.00


class TestMealPrepService:
    """Test meal prep service"""
    
    def test_calculate_nutritional_targets_training_day(self):
        """Test nutritional target calculation for training day"""
        service = MealPrepService()
        
        # Mock training day check
        with patch.object(service, '_is_training_day', return_value=True):
            targets = service.calculate_nutritional_targets(
                {'body_weight': 175},
                '2024-01-01'
            )
            
            assert targets['body_weight'] == 175
            assert targets['maintenance_calories'] == 2625  # 175 * 15
            assert targets['total_calories'] == 3125  # maintenance + 500
            assert targets['protein_g'] == 175  # 1g per lb
            assert targets['is_training_day'] is True
            assert targets['calorie_surplus'] == 500
    
    def test_calculate_nutritional_targets_rest_day(self):
        """Test nutritional target calculation for rest day"""
        service = MealPrepService()
        
        # Mock rest day check
        with patch.object(service, '_is_training_day', return_value=False):
            targets = service.calculate_nutritional_targets(
                {'body_weight': 175},
                '2024-01-02'
            )
            
            assert targets['total_calories'] == 2725  # maintenance + 100
            assert targets['is_training_day'] is False
            assert targets['calorie_surplus'] == 100
    
    def test_create_demo_meal_plan(self):
        """Test creating a demo meal plan"""
        service = MealPrepService()
        
        meal_plan_data = {
            'name': 'Test Meal Plan',
            'dietary_requirements': ['vegetarian'],
            'budget': 150
        }
        
        result = service.create_meal_plan('test-user', meal_plan_data)
        
        assert result['success'] is True
        assert 'meal_plan_id' in result
        assert result['data']['demo_mode'] is True


class TestMealPrepIntegration:
    """Test meal prep integration with Flask app"""
    
    def test_meal_prep_page_loads(self, client):
        """Test that meal prep page loads"""
        response = client.get('/meal-prep')
        assert response.status_code == 200
        assert b'AI-Powered Meal Prep Planner' in response.data
    
    def test_generate_meal_plan_demo_mode(self, client, monkeypatch):
        """Test meal plan generation in demo mode"""
        # Force DEMO_MODE to True for this test
        import app
        monkeypatch.setattr(app, 'DEMO_MODE', True)
        
        # Also mock the OpenAIMealService to not be available
        from services.openai_meal_service import OpenAIMealService
        monkeypatch.setattr(OpenAIMealService, 'is_available', lambda self: False)
        
        response = client.post('/api/meal-prep/generate', 
            json={
                'dietary_requirements': ['vegetarian'],
                'budget': 150,
                'store_preference': 'Whole Foods',
                'use_ai': False
            }
        )
        
        assert response.status_code == 200
        data = response.json
        assert 'meal_plan' in data
        assert 'shopping_list' in data
        assert data.get('demo_mode') is True
    
    def test_get_saved_plans_demo_mode(self, client, monkeypatch):
        """Test getting saved plans in demo mode"""
        # Force DEMO_MODE to True for this test
        import app
        monkeypatch.setattr(app, 'DEMO_MODE', True)
        
        response = client.get('/api/meal-prep/plans')
        
        assert response.status_code == 200
        data = response.json
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]['name'] == 'Demo Meal Plan - Week 1'
    
    def test_research_recipe_nutrition(self, client):
        """Test recipe nutrition research"""
        response = client.post('/api/meal-prep/research-recipe',
            json={
                'ingredients': ['6 oz chicken breast', '1 cup rice', '1 cup broccoli'],
                'servings': 1
            }
        )
        
        assert response.status_code == 200
        data = response.json
        # In demo mode or without AI, it returns an error
        assert 'error' in data or 'total_nutrition' in data
    
    def test_meal_prep_chat(self, client):
        """Test meal prep chat assistant"""
        response = client.post('/api/meal-prep/chat',
            json={
                'message': 'How can I customize this meal?',
                'context': {}
            }
        )
        
        assert response.status_code == 200
        data = response.json
        assert 'response' in data
        assert 'customize' in data['response']


@pytest.mark.parametrize("dietary_requirement,expected_in_plan", [
    (['vegetarian'], 'vegetarian'),
    (['vegan'], 'vegan'),
    (['gluten-free'], 'gluten'),
])
def test_dietary_requirements_handling(dietary_requirement, expected_in_plan):
    """Test that dietary requirements are properly handled"""
    service = OpenAIMealService()
    user_data = {
        'body_weight': 175,
        'dietary_requirements': dietary_requirement,
        'budget': 150
    }
    
    # This would test the prompt building
    prompt = service._build_meal_plan_prompt(
        user_data, 
        2625,  # maintenance calories
        ['Monday', 'Wednesday', 'Friday']
    )
    
    assert dietary_requirement[0] in prompt