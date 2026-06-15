"""
Test the ML integration fixes.
Verifies the calorie pipeline uses scaler + realistic predictions.
"""

import pytest
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gym_config.settings')
django.setup()

from fitness_api.utils import prepare_calorie_model_input, prepare_fitness_model_input
from fitness_api.nutrition_calculator import NutritionCalculator
from fitness_api.model_manager import ModelRegistry
from fitness_api.calorie_predictor import predict_calories


class TestCalorieInputPreparation:
    """Test that calorie model input matches new 6-feature schema."""
    
    def test_prepare_calorie_model_input_units(self):
        """Verify height is in cm and feature order matches training."""
        # Test data
        gender, age, height_cm, weight_kg = 0, 30, 175, 70
        duration_min, heart_rate = 30, 130
        
        # Prepare input (6-feature final model format)
        df = prepare_calorie_model_input(
            gender=gender, age=age, height_cm=height_cm, weight_kg=weight_kg,
            duration_min=duration_min, heart_rate=heart_rate
        )
        
        # Verify units and features
        assert df['Height'].iloc[0] == 175.0, "Height should be 175cm (1.75m * 100)"
        assert df['Duration'].iloc[0] == 30.0, "Duration should be 30 min (NOT 1800 seconds)"
        assert df['Gender'].iloc[0] == 0, "Gender should be 0 for male"
        assert df['Age'].iloc[0] == 30, "Age should be 30"
        assert list(df.columns) == ['Gender', 'Age', 'Height', 'Weight', 'Duration', 'Heart_Rate']
        assert len(df.columns) == 6, "Should have 6 features (new final model format)"

    def test_consistency_across_endpoints(self):
        """Verify same input produces same DataFrame across multiple calls."""
        test_data = {
            'gender': 1,  # female
            'age': 25,
            'height_cm': 165,
            'weight_kg': 60,
            'duration_min': 45,
            'heart_rate': 140
        }
        
        # Call multiple times
        df1 = prepare_calorie_model_input(**test_data)
        df2 = prepare_calorie_model_input(**test_data)
        df3 = prepare_calorie_model_input(**test_data)
        
        # Should be identical
        assert df1.equals(df2), "Repeated calls should produce identical DataFrames"
        assert df2.equals(df3), "Repeated calls should produce identical DataFrames"


class TestCaloriePredictionPipeline:
    """Regression checks against constant-output bug."""

    def test_required_scenarios_are_realistic_and_different(self):
        gender, age, height_cm, weight = 0, 30, 175, 70
        scenarios = [
            ("light20", 20, 100, 80, 150),
            ("moderate30", 30, 130, 200, 300),
            ("moderate60", 60, 130, 500, 800),
            ("intense45", 45, 160, 400, 650),
        ]

        outputs = []
        for _, duration, heart_rate, expected_min, expected_max in scenarios:
            pred = predict_calories(gender, age, height_cm, weight, duration, heart_rate)
            outputs.append(pred)
            assert expected_min <= pred <= expected_max, (
                f"Prediction {pred} out of expected range [{expected_min}, {expected_max}]"
            )

        assert len(set(outputs)) == len(outputs), "Predictions must differ across scenarios"


class TestNutritionCalculator:
    """Test the centralized nutrition calculator."""
    
    def test_nutrition_calculation_consistency(self):
        """Verify nutrition calculation produces consistent results."""
        nutrition = NutritionCalculator.calculate_full_nutrition(
            weight_kg=70, height_m=1.75, age_years=30,
            activity_level='moderate', gender=0
        )
        
        # Check that all keys exist
        assert 'bmr' in nutrition, "should have bmr"
        assert 'daily_calories' in nutrition, "should have daily_calories"
        assert 'protein_grams' in nutrition, "should have protein_grams"
        assert 'carbs_grams' in nutrition, "should have carbs_grams"
        assert 'fats_grams' in nutrition, "should have fats_grams"
        assert 'max_bpm' in nutrition, "should have max_bpm"
        
        # Check values are reasonable
        assert nutrition['bmr'] > 0, "BMR should be positive"
        assert nutrition['daily_calories'] > 0, "daily_calories should be positive"
        assert nutrition['protein_grams'] > 0, "protein_grams should be positive"
        assert nutrition['max_bpm'] == 190, "max_bpm should be 220 - 30"

    def test_bmr_gender_differences(self):
        """Verify BMR calculation differs between genders as expected."""
        male_nutrition = NutritionCalculator.calculate_full_nutrition(
            weight_kg=70, height_m=1.75, age_years=30,
            activity_level='moderate', gender=0  # male
        )
        
        female_nutrition = NutritionCalculator.calculate_full_nutrition(
            weight_kg=70, height_m=1.75, age_years=30,
            activity_level='moderate', gender=1  # female
        )
        
        # Male BMR should be higher than female BMR (with same params)
        assert male_nutrition['bmr'] > female_nutrition['bmr'], \
            "Male BMR should be higher than female BMR for same body metrics"


class TestModelRegistry:
    """Test the centralized model loading."""
    
    def test_model_registry_caching(self):
        """Verify models are cached after first load."""
        # Clear cache
        ModelRegistry.clear_cache()
        
        # First load
        try:
            model1 = ModelRegistry.get_model('fitness')
        except:
            pytest.skip("Fitness model not available")
        
        # Second load should return same object (cached)
        model2 = ModelRegistry.get_model('fitness')
        
        assert model1 is model2, "Should return cached model"

    def test_fitness_labels_from_config(self):
        """Verify fitness labels are loaded from config."""
        labels = ModelRegistry.get_fitness_labels()
        
        assert isinstance(labels, dict), "Labels should be a dict"
        assert len(labels) > 0, "Should have at least one label"


class TestFitnessPredictionInput:
    """Test fitness model input preparation."""
    
    def test_prepare_fitness_model_input(self):
        """Verify fitness model input is correctly formatted."""
        df = prepare_fitness_model_input(
            age=30, gender=0, weight_kg=70, height_m=1.75,
            max_bpm=190, avg_bpm=120, resting_bpm=70,
            fat_percentage=15, water_intake=3, workout_frequency=4
        )
        
        # Verify structure
        expected_columns = [
            'Age', 'Gender', 'Weight (kg)', 'Height (m)', 'Max_BPM', 'Avg_BPM',
            'Resting_BPM', 'Fat_Percentage', 'Water_Intake (liters)', 'Workout_Frequency (days/week)'
        ]
        
        assert list(df.columns) == expected_columns, "Columns should match training feature order"
        assert df['Height (m)'].iloc[0] == 1.75, "Height should remain in meters"


if __name__ == '__main__':
    print("🧪 Running ML Integration Tests...")
    pytest.main([__file__, '-v'])
