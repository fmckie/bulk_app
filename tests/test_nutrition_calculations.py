"""
Test nutrition calculations and business logic
"""
import pytest
from datetime import date

class TestNutritionCalculations:
    """Test nutrition calculation logic"""
    
    def test_maintenance_calories_calculation(self):
        """Test maintenance calories calculation"""
        body_weights = [150, 175, 200]
        expected_maintenance = [2250, 2625, 3000]  # 15 cal per lb
        
        for weight, expected in zip(body_weights, expected_maintenance):
            maintenance = weight * 15
            assert maintenance == expected
    
    def test_training_day_calorie_surplus(self):
        """Test training day calorie calculations"""
        body_weight = 175
        maintenance = body_weight * 15  # 2625
        training_calories = maintenance + 500  # 3125
        
        assert training_calories == 3125
        assert training_calories - maintenance == 500
    
    def test_rest_day_calorie_surplus(self):
        """Test rest day calorie calculations"""
        body_weight = 175
        maintenance = body_weight * 15  # 2625
        rest_calories = maintenance + 100  # 2725
        
        assert rest_calories == 2725
        assert rest_calories - maintenance == 100
    
    def test_protein_calculation(self):
        """Test protein calculation (1g per lb body weight)"""
        body_weights = [150, 175, 200]
        
        for weight in body_weights:
            protein = weight * 1.0
            assert protein == weight
    
    def test_macro_distribution_training_day(self):
        """Test macro distribution for training day"""
        body_weight = 175
        maintenance = body_weight * 15
        calories = maintenance + 500  # 3125
        
        # Protein: 1g per lb
        protein = body_weight * 1.0  # 175g
        protein_calories = protein * 4  # 700 cal
        
        # Fats: 25% of total calories
        fat_calories = calories * 0.25  # 781.25 cal
        fats = fat_calories / 9  # 86.8g
        
        # Carbs: remaining calories
        remaining_calories = calories - protein_calories - fat_calories  # 1643.75
        carbs = remaining_calories / 4  # 410.9g
        
        assert round(protein) == 175
        assert round(fats) == 87
        assert round(carbs) == 411
        
        # Verify total calories
        total_calculated = (protein * 4) + (round(fats) * 9) + (round(carbs) * 4)
        assert abs(total_calculated - calories) < 10  # Allow small rounding difference
    
    def test_macro_distribution_rest_day(self):
        """Test macro distribution for rest day"""
        body_weight = 175
        maintenance = body_weight * 15
        calories = maintenance + 100  # 2725
        
        # Protein: 1g per lb
        protein = body_weight * 1.0  # 175g
        protein_calories = protein * 4  # 700 cal
        
        # Fats: 25% of total calories
        fat_calories = calories * 0.25  # 681.25 cal
        fats = fat_calories / 9  # 75.7g
        
        # Carbs: remaining calories
        remaining_calories = calories - protein_calories - fat_calories  # 1343.75
        carbs = remaining_calories / 4  # 335.9g
        
        assert round(protein) == 175
        assert round(fats) == 76
        assert round(carbs) == 336
    
    def test_calorie_cycling_difference(self):
        """Test the difference between training and rest day calories"""
        body_weight = 175
        maintenance = body_weight * 15
        
        training_calories = maintenance + 500
        rest_calories = maintenance + 100
        
        difference = training_calories - rest_calories
        assert difference == 400  # 400 calorie difference
    
    def test_various_body_weights(self):
        """Test calculations for various body weights"""
        test_weights = [
            {'weight': 150, 'maintenance': 2250, 'training': 2750, 'rest': 2350},
            {'weight': 175, 'maintenance': 2625, 'training': 3125, 'rest': 2725},
            {'weight': 200, 'maintenance': 3000, 'training': 3500, 'rest': 3100},
            {'weight': 225, 'maintenance': 3375, 'training': 3875, 'rest': 3475}
        ]
        
        for test in test_weights:
            weight = test['weight']
            maintenance = weight * 15
            training = maintenance + 500
            rest = maintenance + 100
            
            assert maintenance == test['maintenance']
            assert training == test['training']
            assert rest == test['rest']
    
    def test_protein_percentage_of_calories(self):
        """Test protein as percentage of total calories"""
        body_weight = 175
        protein = body_weight * 1.0
        protein_calories = protein * 4  # 700
        
        # Training day
        training_calories = (body_weight * 15) + 500  # 3125
        training_protein_percentage = (protein_calories / training_calories) * 100
        assert 22 <= training_protein_percentage <= 23  # Should be ~22.4%
        
        # Rest day
        rest_calories = (body_weight * 15) + 100  # 2725
        rest_protein_percentage = (protein_calories / rest_calories) * 100
        assert 25 <= rest_protein_percentage <= 26  # Should be ~25.7%
    
    def test_fat_percentage_constant(self):
        """Test that fat percentage remains constant at 25%"""
        body_weights = [150, 175, 200]
        
        for weight in body_weights:
            # Training day
            training_calories = (weight * 15) + 500
            training_fat_calories = training_calories * 0.25
            training_fat_percentage = (training_fat_calories / training_calories) * 100
            assert training_fat_percentage == 25.0
            
            # Rest day
            rest_calories = (weight * 15) + 100
            rest_fat_calories = rest_calories * 0.25
            rest_fat_percentage = (rest_fat_calories / rest_calories) * 100
            assert rest_fat_percentage == 25.0
    
    def test_carb_adjustment_between_days(self):
        """Test that carbs adjust properly between training and rest days"""
        body_weight = 175
        protein = body_weight * 1.0  # Constant
        
        # Training day
        training_calories = (body_weight * 15) + 500
        training_fats = training_calories * 0.25 / 9
        training_carbs = (training_calories - (protein * 4) - (training_fats * 9)) / 4
        
        # Rest day
        rest_calories = (body_weight * 15) + 100
        rest_fats = rest_calories * 0.25 / 9
        rest_carbs = (rest_calories - (protein * 4) - (rest_fats * 9)) / 4
        
        # Carbs should be significantly higher on training days
        carb_difference = training_carbs - rest_carbs
        assert 70 <= carb_difference <= 80  # Should be ~75g difference