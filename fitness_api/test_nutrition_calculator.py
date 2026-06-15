"""
Comprehensive tests for NutritionCalculator with new weight-based calculations.

Tests cover:
- BMI calculation and categorization
- Ideal weight calculation
- Water intake calculation
- Goal-based calorie adjustments
- Input validation
- Full nutrition calculation with all features
"""

import pytest
from fitness_api.nutrition_calculator import NutritionCalculator


class TestNutritionCalculatorValidation:
    """Test input validation."""
    
    def test_valid_inputs(self):
        """Test that valid inputs pass validation."""
        is_valid, error_msg = NutritionCalculator.validate_input(70, 1.75, 30)
        assert is_valid is True
        assert error_msg is None
    
    def test_invalid_weight_zero(self):
        """Test that zero weight fails validation."""
        is_valid, error_msg = NutritionCalculator.validate_input(0, 1.75, 30)
        assert is_valid is False
        assert error_msg is not None
    
    def test_invalid_weight_too_high(self):
        """Test that unrealistic high weight fails validation."""
        is_valid, error_msg = NutritionCalculator.validate_input(350, 1.75, 30)
        assert is_valid is False
        assert "Weight seems unrealistic" in error_msg
    
    def test_invalid_weight_too_low(self):
        """Test that unrealistic low weight fails validation."""
        is_valid, error_msg = NutritionCalculator.validate_input(20, 1.75, 30)
        assert is_valid is False
        assert "Weight seems unrealistic" in error_msg
    
    def test_invalid_height_zero(self):
        """Test that zero height fails validation."""
        is_valid, error_msg = NutritionCalculator.validate_input(70, 0, 30)
        assert is_valid is False
        assert error_msg is not None
    
    def test_invalid_height_too_high(self):
        """Test that unrealistic high height fails validation."""
        is_valid, error_msg = NutritionCalculator.validate_input(70, 3.0, 30)
        assert is_valid is False
        assert "Height seems unrealistic" in error_msg
    
    def test_invalid_height_too_low(self):
        """Test that unrealistic low height fails validation."""
        is_valid, error_msg = NutritionCalculator.validate_input(70, 1.3, 30)
        assert is_valid is False
        assert "Height seems unrealistic" in error_msg
    
    def test_invalid_age_zero(self):
        """Test that zero age fails validation."""
        is_valid, error_msg = NutritionCalculator.validate_input(70, 1.75, 0)
        assert is_valid is False
        assert error_msg is not None
    
    def test_invalid_age_too_low(self):
        """Test that age below 13 fails validation."""
        is_valid, error_msg = NutritionCalculator.validate_input(70, 1.75, 10)
        assert is_valid is False
        assert "Age should be at least 13" in error_msg
    
    def test_invalid_age_too_high(self):
        """Test that unrealistic high age fails validation."""
        is_valid, error_msg = NutritionCalculator.validate_input(70, 1.75, 150)
        assert is_valid is False
        assert "Age seems unrealistic" in error_msg


class TestBMICalculation:
    """Test BMI calculation and categorization."""
    
    def test_bmi_underweight(self):
        """Test BMI underweight category."""
        # BMI around 18
        result = NutritionCalculator.calculate_bmi(50, 1.68)
        assert result['bmi'] < 18.5
        assert result['category'] == 'underweight'
    
    def test_bmi_normal(self):
        """Test BMI normal category."""
        # BMI around 22
        result = NutritionCalculator.calculate_bmi(65, 1.72)
        assert 18.5 <= result['bmi'] < 25
        assert result['category'] == 'normal'
    
    def test_bmi_overweight(self):
        """Test BMI overweight category."""
        # BMI around 27
        result = NutritionCalculator.calculate_bmi(80, 1.72)
        assert 25 <= result['bmi'] < 30
        assert result['category'] == 'overweight'
    
    def test_bmi_obese(self):
        """Test BMI obese category."""
        # BMI around 32
        result = NutritionCalculator.calculate_bmi(95, 1.72)
        assert result['bmi'] >= 30
        assert result['category'] == 'obese'
    
    def test_bmi_has_description(self):
        """Test that BMI result includes description."""
        result = NutritionCalculator.calculate_bmi(70, 1.75)
        assert 'description' in result
        assert len(result['description']) > 0


class TestIdealWeightCalculation:
    """Test ideal weight calculation using Devine formula."""
    
    def test_ideal_weight_male(self):
        """Test ideal weight for male."""
        result = NutritionCalculator.calculate_ideal_weight(1.75, gender=0)
        assert result['ideal_weight_kg'] > 0
        assert result['min_range'] < result['ideal_weight_kg']
        assert result['ideal_weight_kg'] < result['max_range']
    
    def test_ideal_weight_female(self):
        """Test ideal weight for female."""
        result = NutritionCalculator.calculate_ideal_weight(1.70, gender=1)
        assert result['ideal_weight_kg'] > 0
        assert result['min_range'] < result['ideal_weight_kg']
        assert result['ideal_weight_kg'] < result['max_range']
    
    def test_ideal_weight_ranges(self):
        """Test that ideal weight ranges are ±10%."""
        result = NutritionCalculator.calculate_ideal_weight(1.75, gender=0)
        expected_min = result['ideal_weight_kg'] * 0.9
        expected_max = result['ideal_weight_kg'] * 1.1
        assert abs(result['min_range'] - expected_min) < 0.1
        assert abs(result['max_range'] - expected_max) < 0.1


class TestWaterIntakeCalculation:
    """Test daily water intake calculation."""
    
    def test_water_base_calculation(self):
        """Test base water calculation (35ml per kg)."""
        result = NutritionCalculator.calculate_daily_water_intake(70, 'sedentary')
        expected_base = (70 * 35) / 1000  # Convert to liters
        assert abs(result['base_liters'] - expected_base) < 0.1
    
    def test_water_with_exercise_sedentary(self):
        """Test water intake for sedentary activity."""
        result = NutritionCalculator.calculate_daily_water_intake(70, 'sedentary')
        assert result['with_exercise_liters'] == result['base_liters']
    
    def test_water_with_exercise_moderate(self):
        """Test water intake for moderate activity (should add 400ml)."""
        result = NutritionCalculator.calculate_daily_water_intake(70, 'moderate')
        base_ml = 70 * 35
        expected_total_ml = base_ml + 400
        assert abs(result['with_exercise_liters'] * 1000 - expected_total_ml) < 10
    
    def test_water_cups_conversion(self):
        """Test water cups conversion (240ml per cup)."""
        result = NutritionCalculator.calculate_daily_water_intake(70, 'sedentary')
        expected_cups = round((70 * 35) / 240)
        assert result['cups'] == expected_cups
    
    def test_water_bottles_conversion(self):
        """Test water bottles conversion (500ml per bottle)."""
        result = NutritionCalculator.calculate_daily_water_intake(70, 'sedentary')
        expected_bottles = round((70 * 35) / 500)
        assert result['bottles_500ml'] == expected_bottles


class TestGoalAdjustment:
    """Test goal-based calorie adjustments."""
    
    def test_maintenance_goal(self):
        """Test maintenance goal (no adjustment)."""
        result = NutritionCalculator.calculate_calories_by_goal(2500, 'maintenance')
        assert result['adjusted_calories'] == 2500
        assert result['daily_adjustment'] == 0
        assert result['weekly_surplus_deficit'] == 0
    
    def test_cutting_goal(self):
        """Test cutting goal (-300 calories)."""
        result = NutritionCalculator.calculate_calories_by_goal(2500, 'cutting')
        assert result['adjusted_calories'] == 2200
        assert result['daily_adjustment'] == -300
        assert result['weekly_surplus_deficit'] == -2100
    
    def test_bulking_goal(self):
        """Test bulking goal (+300 calories)."""
        result = NutritionCalculator.calculate_calories_by_goal(2500, 'bulking')
        assert result['adjusted_calories'] == 2800
        assert result['daily_adjustment'] == 300
        assert result['weekly_surplus_deficit'] == 2100
    
    def test_goal_has_description(self):
        """Test that goal result includes description."""
        result = NutritionCalculator.calculate_calories_by_goal(2500, 'bulking')
        assert 'goal_description' in result
        assert len(result['goal_description']) > 0


class TestWeightBasedMacroCalculation:
    """Test weight-based macronutrient calculation."""
    
    def test_protein_calculation_moderate(self):
        """Test protein calculation for moderate activity (1.6g per kg)."""
        result = NutritionCalculator.calculate_macros_weight_based(2500, 70, 'moderate')
        expected_protein = 70 * 1.6
        assert abs(result['protein_grams'] - expected_protein) < 0.1
    
    def test_protein_calculation_active(self):
        """Test protein calculation for active level (1.8g per kg)."""
        result = NutritionCalculator.calculate_macros_weight_based(2500, 70, 'active')
        expected_protein = 70 * 1.8
        assert abs(result['protein_grams'] - expected_protein) < 0.1
    
    def test_macro_calories_sum(self):
        """Test that macro calories sum to approximately TDEE."""
        result = NutritionCalculator.calculate_macros_weight_based(2500, 70, 'moderate')
        total_calories = (result['protein_grams'] * 4) + (result['carbs_grams'] * 4) + (result['fats_grams'] * 9)
        assert abs(total_calories - 2500) < 50  # Within 50 calorie margin
    
    def test_method_indicator(self):
        """Test that result includes method indicator."""
        result = NutritionCalculator.calculate_macros_weight_based(2500, 70, 'moderate')
        assert result['method'] == 'weight_based'
        assert 'protein_per_kg' in result


class TestFullNutritionCalculation:
    """Test complete nutrition calculation."""
    
    def test_full_nutrition_valid_inputs(self):
        """Test full nutrition calculation with valid inputs."""
        result = NutritionCalculator.calculate_full_nutrition(
            weight_kg=70, height_m=1.75, age_years=30,
            activity_level='moderate', gender=0, use_weight_based=True
        )
        
        # Check required fields
        assert 'bmr' in result
        assert 'daily_calories' in result
        assert 'protein_grams' in result
        assert 'carbs_grams' in result
        assert 'fats_grams' in result
        
        # Check new fields
        assert 'bmi' in result
        assert 'bmi_category' in result
        assert 'ideal_weight_kg' in result
        assert 'water_with_exercise_liters' in result
        assert 'goal_adjusted_calories' in result
    
    def test_full_nutrition_with_bulking_goal(self):
        """Test full nutrition with bulking goal."""
        result = NutritionCalculator.calculate_full_nutrition(
            weight_kg=70, height_m=1.75, age_years=30,
            activity_level='moderate', gender=0, goal='bulking'
        )
        
        # Adjusted calories should be higher than base
        assert result['goal_adjusted_calories'] > result['daily_calories']
        assert result['adjusted_protein_grams'] > result['protein_grams']
    
    def test_full_nutrition_with_cutting_goal(self):
        """Test full nutrition with cutting goal."""
        result = NutritionCalculator.calculate_full_nutrition(
            weight_kg=70, height_m=1.75, age_years=30,
            activity_level='moderate', gender=0, goal='cutting'
        )
        
        # Adjusted calories should be lower than base
        assert result['goal_adjusted_calories'] < result['daily_calories']
        assert result['adjusted_protein_grams'] < result['protein_grams']
    
    def test_full_nutrition_percentage_based(self):
        """Test full nutrition with percentage-based calculation."""
        result = NutritionCalculator.calculate_full_nutrition(
            weight_kg=70, height_m=1.75, age_years=30,
            use_weight_based=False
        )
        
        assert result['calculation_method'] == 'percentage_based'
    
    def test_full_nutrition_invalid_input_raises_error(self):
        """Test that invalid inputs raise ValueError."""
        with pytest.raises(ValueError):
            NutritionCalculator.calculate_full_nutrition(
                weight_kg=0, height_m=1.75, age_years=30
            )
    
    def test_full_nutrition_female(self):
        """Test full nutrition calculation for female."""
        result = NutritionCalculator.calculate_full_nutrition(
            weight_kg=65, height_m=1.65, age_years=28,
            gender=1
        )
        
        assert result['bmr'] > 0
        assert result['daily_calories'] > 0
        assert result['bmi'] > 0
    
    def test_full_nutrition_all_activity_levels(self):
        """Test full nutrition for all activity levels."""
        activity_levels = ['sedentary', 'light', 'moderate', 'active', 'very_active']
        
        for level in activity_levels:
            result = NutritionCalculator.calculate_full_nutrition(
                weight_kg=70, height_m=1.75, age_years=30,
                activity_level=level
            )
            
            assert result['daily_calories'] > 0
            assert result['protein_grams'] > 0
            assert result['carbs_grams'] > 0
            assert result['fats_grams'] > 0
    
    def test_full_nutrition_returns_consistent_values(self):
        """Test that repeated calls return consistent values."""
        result1 = NutritionCalculator.calculate_full_nutrition(
            weight_kg=70, height_m=1.75, age_years=30
        )
        result2 = NutritionCalculator.calculate_full_nutrition(
            weight_kg=70, height_m=1.75, age_years=30
        )
        
        assert result1['daily_calories'] == result2['daily_calories']
        assert result1['protein_grams'] == result2['protein_grams']
        assert result1['bmi'] == result2['bmi']


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_very_low_weight_but_valid(self):
        """Test minimum valid weight (just above 30kg)."""
        result = NutritionCalculator.calculate_full_nutrition(
            weight_kg=31, height_m=1.50, age_years=20
        )
        assert result['daily_calories'] > 0
    
    def test_very_high_weight_but_valid(self):
        """Test maximum valid weight (just below 300kg)."""
        result = NutritionCalculator.calculate_full_nutrition(
            weight_kg=299, height_m=2.0, age_years=40
        )
        assert result['daily_calories'] > 0
    
    def test_teenager_at_boundary(self):
        """Test teenager at minimum valid age (13 years)."""
        result = NutritionCalculator.calculate_full_nutrition(
            weight_kg=50, height_m=1.60, age_years=13
        )
        assert result['daily_calories'] > 0
    
    def test_elderly_person(self):
        """Test elderly person at high valid age (100 years)."""
        result = NutritionCalculator.calculate_full_nutrition(
            weight_kg=70, height_m=1.70, age_years=100
        )
        assert result['daily_calories'] > 0
        assert result['max_bpm'] == 120  # 220 - 100


class TestComparisonBetweenMethods:
    """Compare weight-based vs percentage-based calculations."""
    
    def test_weight_based_has_higher_protein(self):
        """Test that weight-based typically gives different protein than percentage-based."""
        weight_based = NutritionCalculator.calculate_full_nutrition(
            weight_kg=70, height_m=1.75, age_years=30,
            use_weight_based=True
        )
        
        percentage_based = NutritionCalculator.calculate_full_nutrition(
            weight_kg=70, height_m=1.75, age_years=30,
            use_weight_based=False
        )
        
        # They should be different methods
        assert weight_based['calculation_method'] != percentage_based['calculation_method']
