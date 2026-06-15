"""
Centralized nutrition calculation using Mifflin-St Jeor equation.
Single source of truth for BMR, TDEE, and macronutrient calculations.
"""

import logging

logger = logging.getLogger(__name__)


class NutritionCalculator:
    """
    Centralized nutrition calculator.
    Eliminates duplicate logic between views.py and models.py.
    """
    
    # Formula version for traceability
    BMR_FORMULA_VERSION = "Mifflin-St Jeor"
    
    # Activity level multipliers (TDEE = BMR * multiplier)
    ACTIVITY_MULTIPLIERS = {
        'sedentary': 1.2,       # Little or no exercise
        'light': 1.375,         # Light exercise 1-3 days/week
        'moderate': 1.55,       # Moderate exercise 3-5 days/week
        'active': 1.725,        # Hard exercise 6-7 days/week
        'very_active': 1.9      # Very hard exercise & physical job
    }
    
    # Macronutrient distribution (ratio : calories_per_gram)
    MACRO_RATIOS = {
        'protein': {'ratio': 0.30, 'calories_per_gram': 4},      # 30% protein
        'carbs': {'ratio': 0.40, 'calories_per_gram': 4},        # 40% carbs
        'fats': {'ratio': 0.30, 'calories_per_gram': 9}          # 30% fats
    }
    
    # Protein multipliers based on weight (grams per kg of body weight)
    # This is more scientifically accurate for athletes
    PROTEIN_MULTIPLIERS = {
        'sedentary': 0.8,           # Light activity: 0.8g per kg
        'light': 1.2,               # Light exercise: 1.2g per kg
        'moderate': 1.6,            # Moderate exercise: 1.6g per kg (athletes)
        'active': 1.8,              # Hard exercise: 1.8g per kg
        'very_active': 2.2          # Very hard exercise: 2.2g per kg (intensive training)
    }
    
    # Carb and fat ratios (after protein is calculated from weight)
    REMAINING_MACRO_RATIOS = {
        'carbs': {'ratio': 0.50, 'calories_per_gram': 4},        # 50% of remaining for carbs
        'fats': {'ratio': 0.50, 'calories_per_gram': 9}          # 50% of remaining for fats
    }
    
    # BMI Categories
    BMI_CATEGORIES = {
        'underweight': (0, 18.5),
        'normal': (18.5, 25),
        'overweight': (25, 30),
        'obese': (30, float('inf'))
    }
    
    # Caloric adjustment for goals
    GOAL_ADJUSTMENTS = {
        'maintenance': 0,           # No change
        'cutting': -300,            # 300 calorie deficit (fat loss)
        'bulking': 300              # 300 calorie surplus (muscle gain)
    }
    
    @staticmethod
    def validate_input(weight_kg, height_m, age_years):
        """
        Validate nutritional calculation inputs.
        
        Args:
            weight_kg: Weight in kilograms (float)
            height_m: Height in meters (float)
            age_years: Age in years (integer)
        
        Returns:
            tuple: (is_valid: bool, error_message: str or None)
        """
        errors = []
        
        # Weight validation
        if not weight_kg or weight_kg <= 0:
            errors.append("Weight must be greater than 0 kg")
        elif weight_kg > 300:
            errors.append("Weight seems unrealistic (> 300 kg)")
        elif weight_kg < 30:
            errors.append("Weight seems unrealistic (< 30 kg)")
        
        # Height validation
        if not height_m or height_m <= 0:
            errors.append("Height must be greater than 0 m")
        elif height_m > 2.5:
            errors.append("Height seems unrealistic (> 2.5 m)")
        elif height_m < 1.4:
            errors.append("Height seems unrealistic (< 1.4 m)")
        
        # Age validation
        if not age_years or age_years <= 0:
            errors.append("Age must be greater than 0")
        elif age_years > 120:
            errors.append("Age seems unrealistic (> 120 years)")
        elif age_years < 13:
            errors.append("Age should be at least 13 years")
        
        is_valid = len(errors) == 0
        error_message = " | ".join(errors) if errors else None
        
        return is_valid, error_message
    
    @staticmethod
    def calculate_bmi(weight_kg, height_m):
        """
        Calculate Body Mass Index (BMI).
        
        Args:
            weight_kg: Weight in kilograms (float)
            height_m: Height in meters (float)
        
        Returns:
            dict: {
                'bmi': float,
                'category': str,  # 'underweight', 'normal', 'overweight', 'obese'
                'description': str
            }
        """
        if height_m <= 0 or weight_kg <= 0:
            return {'bmi': 0, 'category': 'invalid', 'description': 'Invalid input'}
        
        bmi = weight_kg / (height_m ** 2)
        
        categories_desc = {
            'underweight': 'أقل من الوزن الصحي',
            'normal': 'وزن صحي ✓',
            'overweight': 'زيادة في الوزن',
            'obese': 'سمنة'
        }
        
        category = 'normal'
        for cat, (min_bmi, max_bmi) in NutritionCalculator.BMI_CATEGORIES.items():
            if min_bmi <= bmi < max_bmi:
                category = cat
                break
        
        return {
            'bmi': round(bmi, 1),
            'category': category,
            'description': categories_desc.get(category, 'Unknown')
        }
    
    @staticmethod
    def calculate_ideal_weight(height_m, gender=0):
        """
        Calculate ideal body weight using Devine formula.
        
        Args:
            height_m: Height in meters (float)
            gender: 0 for male, 1 for female (integer)
        
        Returns:
            dict: {
                'ideal_weight_kg': float,
                'min_range': float,  # -10%
                'max_range': float   # +10%
            }
        """
        height_cm = height_m * 100
        
        if gender == 0:  # Male
            # Males: 50 kg + 2.3 kg per cm above 152.4 cm
            ideal = 50 + (2.3 * (height_cm - 152.4))
        else:  # Female
            # Females: 45.5 kg + 2.3 kg per cm above 152.4 cm
            ideal = 45.5 + (2.3 * (height_cm - 152.4))
        
        # Ensure positive
        ideal = max(ideal, 40)
        
        return {
            'ideal_weight_kg': round(ideal, 1),
            'min_range': round(ideal * 0.9, 1),  # -10%
            'max_range': round(ideal * 1.1, 1)   # +10%
        }
    
    @staticmethod
    def calculate_daily_water_intake(weight_kg, activity_level='moderate'):
        """
        Calculate daily water intake recommendation.
        
        Args:
            weight_kg: Weight in kilograms (float)
            activity_level: Activity level affecting water needs
        
        Returns:
            dict: {
                'base_liters': float,      # Base calculation (weight_kg * 0.035)
                'with_exercise_liters': float,
                'cups': int,               # Approximate cups (1 cup = 240ml)
                'bottles': int             # Approximate 500ml bottles
            }
        """
        # Base formula: 35 ml per kg of body weight
        base_ml = weight_kg * 35
        
        # Add extra for exercise
        exercise_water = {
            'sedentary': 0,
            'light': 200,       # +200ml
            'moderate': 400,    # +400ml
            'active': 600,      # +600ml
            'very_active': 1000 # +1000ml
        }
        
        extra_ml = exercise_water.get(activity_level, 400)
        total_ml = base_ml + extra_ml
        
        return {
            'base_liters': round(base_ml / 1000, 2),
            'with_exercise_liters': round(total_ml / 1000, 2),
            'cups': round(total_ml / 240),
            'bottles_500ml': round(total_ml / 500)
        }
    
    @staticmethod
    def calculate_calories_by_goal(tdee, goal='maintenance'):
        """
        Adjust daily calories based on fitness goal.
        
        Args:
            tdee: Total Daily Energy Expenditure (float)
            goal: One of 'maintenance', 'cutting', 'bulking'
        
        Returns:
            dict: {
                'tdee': float,              # Original TDEE
                'goal': str,
                'adjusted_calories': int,   # With goal adjustment
                'weekly_surplus_deficit': int  # Caloric surplus/deficit per week
            }
        """
        adjustment = NutritionCalculator.GOAL_ADJUSTMENTS.get(goal, 0)
        adjusted = int(round(tdee + adjustment))
        weekly = adjustment * 7
        
        goal_descriptions = {
            'maintenance': 'الحفاظ على الوزن الحالي',
            'cutting': 'فقدان الدهون',
            'bulking': 'بناء العضلات'
        }
        
        return {
            'tdee': int(round(tdee)),
            'goal': goal,
            'goal_description': goal_descriptions.get(goal, 'Unknown'),
            'adjusted_calories': adjusted,
            'daily_adjustment': adjustment,
            'weekly_surplus_deficit': weekly
        }
    
    @staticmethod
    def calculate_bmr(weight_kg, height_m, age_years, gender):
        """
        Calculate Basal Metabolic Rate (BMR) using Mifflin-St Jeor equation.
        This is the calories burned at rest.
        
        Args:
            weight_kg: Weight in kilograms (float)
            height_m: Height in meters (float)
            age_years: Age in years (integer)
            gender: 0 for male, 1 for female (integer)
        
        Returns:
            float: BMR in calories
        """
        height_cm = height_m * 100
        
        if gender == 0:  # Male
            bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age_years) + 5
        else:  # Female
            bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age_years) - 161
        
        return max(bmr, 1200)  # Ensure minimum for safety
    
    @staticmethod
    def calculate_tdee(bmr, activity_level='moderate'):
        """
        Calculate Total Daily Energy Expenditure (TDEE).
        TDEE = BMR * activity multiplier
        
        Args:
            bmr: Basal Metabolic Rate (float)
            activity_level: One of 'sedentary', 'light', 'moderate', 'active', 'very_active'
        
        Returns:
            float: TDEE in calories
        """
        multiplier = NutritionCalculator.ACTIVITY_MULTIPLIERS.get(activity_level, 1.55)
        return bmr * multiplier
    
    @classmethod
    def calculate_macros(cls, tdee):
        """
        Calculate macronutrient distribution based on TDEE.
        **DEPRECATED: Use calculate_macros_weight_based() for better accuracy**
        
        Args:
            tdee: Total Daily Energy Expenditure (float)
        
        Returns:
            dict: {
                'protein_grams': float,
                'carbs_grams': float,
                'fats_grams': float
            }
        """
        macros = {}
        
        for macro_name, config in cls.MACRO_RATIOS.items():
            calories = tdee * config['ratio']
            grams = calories / config['calories_per_gram']
            macros[f'{macro_name}_grams'] = round(grams, 1)
        
        return macros
    
    @classmethod
    def calculate_macros_weight_based(cls, tdee, weight_kg, activity_level='moderate'):
        """
        Calculate macronutrient distribution based on weight (more scientifically accurate).
        
        This method calculates protein based on body weight and activity level,
        then distributes remaining calories between carbs and fats.
        This is more accurate for athletes and fitness-focused calculations.
        
        Args:
            tdee: Total Daily Energy Expenditure (float)
            weight_kg: Weight in kilograms (float)
            activity_level: Activity level for determining protein multiplier
        
        Returns:
            dict: {
                'protein_grams': float,      # Based on weight (1.6-2.2g per kg)
                'carbs_grams': float,
                'fats_grams': float,
                'method': str                # 'weight_based' indicator
            }
        """
        # Get protein multiplier based on activity level
        protein_multiplier = cls.PROTEIN_MULTIPLIERS.get(activity_level, 1.6)
        
        # Calculate protein grams based on weight
        protein_grams = weight_kg * protein_multiplier
        protein_calories = protein_grams * 4  # 4 calories per gram
        
        # Calculate remaining calories for carbs and fats
        remaining_calories = tdee - protein_calories
        
        # Distribute remaining calories: 50% carbs, 50% fats
        carbs_grams = (remaining_calories * cls.REMAINING_MACRO_RATIOS['carbs']['ratio']) / 4
        fats_grams = (remaining_calories * cls.REMAINING_MACRO_RATIOS['fats']['ratio']) / 9
        
        return {
            'protein_grams': round(protein_grams, 1),
            'carbs_grams': round(carbs_grams, 1),
            'fats_grams': round(fats_grams, 1),
            'method': 'weight_based',
            'protein_per_kg': round(protein_multiplier, 2)
        }
    
    @classmethod
    def calculate_full_nutrition(cls, weight_kg, height_m, age_years, 
                                activity_level='moderate', gender=0, 
                                use_weight_based=True, goal='maintenance'):
        """
        Complete nutrition calculation in one call.
        **This is the single source of truth - use everywhere!**
        
        Now includes BMI, ideal weight, water intake, and goal-based adjustments.
        
        Args:
            weight_kg: Weight in kilograms (float)
            height_m: Height in meters (float)
            age_years: Age in years (integer)
            activity_level: Activity level string (default 'moderate')
            gender: 0 for male, 1 for female (default 0)
            use_weight_based: If True, use weight-based protein (default True)
            goal: 'maintenance', 'cutting', or 'bulking' (default 'maintenance')
        
        Returns:
            dict: Complete nutrition profile including:
                - bmr, daily_calories, macros, max_bpm
                - bmi, ideal weight, water intake
                - goal-adjusted calories
                - calculation_method
        
        Example:
            >>> nutrition = NutritionCalculator.calculate_full_nutrition(
            ...     weight_kg=70, height_m=1.75, age_years=30,
            ...     activity_level='moderate', gender=0, goal='bulking'
            ... )
            >>> print(f"Daily calories: {nutrition['daily_calories']}")
            >>> print(f"Goal calories: {nutrition['goal_calories']}")
        """
        try:
            # Validate inputs first
            is_valid, error_msg = cls.validate_input(weight_kg, height_m, age_years)
            if not is_valid:
                logger.error(f"Invalid input: {error_msg}")
                raise ValueError(f"Invalid input: {error_msg}")
            
            # Validate activity level
            if activity_level not in cls.ACTIVITY_MULTIPLIERS:
                logger.warning(f"Unknown activity level '{activity_level}', using 'moderate'")
                activity_level = 'moderate'
            
            # Validate goal
            if goal not in cls.GOAL_ADJUSTMENTS:
                logger.warning(f"Unknown goal '{goal}', using 'maintenance'")
                goal = 'maintenance'
            
            # Calculate BMR
            bmr = cls.calculate_bmr(weight_kg, height_m, age_years, gender)
            
            # Calculate TDEE
            tdee = cls.calculate_tdee(bmr, activity_level)
            
            # Calculate macros using the selected method
            if use_weight_based:
                macros = cls.calculate_macros_weight_based(tdee, weight_kg, activity_level)
                calculation_method = 'weight_based'
            else:
                macros = cls.calculate_macros(tdee)
                calculation_method = 'percentage_based'
            
            # Calculate Max BPM
            max_bpm = 220 - age_years
            
            # Calculate BMI
            bmi_data = cls.calculate_bmi(weight_kg, height_m)
            
            # Calculate ideal weight
            ideal_weight_data = cls.calculate_ideal_weight(height_m, gender)
            
            # Calculate water intake
            water_data = cls.calculate_daily_water_intake(weight_kg, activity_level)
            
            # Calculate goal-based calories
            goal_data = cls.calculate_calories_by_goal(tdee, goal)
            
            # Adjust macros if goal is not maintenance
            adjusted_macros = macros.copy()
            if goal != 'maintenance':
                calorie_adjustment_factor = goal_data['adjusted_calories'] / int(round(tdee))
                adjusted_macros['protein_grams'] = round(macros['protein_grams'] * calorie_adjustment_factor, 1)
                adjusted_macros['carbs_grams'] = round(macros['carbs_grams'] * calorie_adjustment_factor, 1)
                adjusted_macros['fats_grams'] = round(macros['fats_grams'] * calorie_adjustment_factor, 1)
            
            result = {
                # Basic calculations
                'bmr': round(bmr, 1),
                'daily_calories': int(round(tdee)),
                'protein_grams': macros['protein_grams'],
                'carbs_grams': macros['carbs_grams'],
                'fats_grams': macros['fats_grams'],
                'max_bpm': max(max_bpm, 100),
                'calculation_method': calculation_method,
                
                # BMI Information
                'bmi': bmi_data['bmi'],
                'bmi_category': bmi_data['category'],
                'bmi_description': bmi_data['description'],
                
                # Ideal weight
                'ideal_weight_kg': ideal_weight_data['ideal_weight_kg'],
                'ideal_weight_min': ideal_weight_data['min_range'],
                'ideal_weight_max': ideal_weight_data['max_range'],
                
                # Water intake
                'water_base_liters': water_data['base_liters'],
                'water_with_exercise_liters': water_data['with_exercise_liters'],
                'water_cups_daily': water_data['cups'],
                'water_bottles_daily': water_data['bottles_500ml'],
                
                # Goal-based adjustments
                'goal': goal,
                'goal_description': goal_data['goal_description'],
                'goal_adjusted_calories': goal_data['adjusted_calories'],
                'adjusted_protein_grams': adjusted_macros['protein_grams'],
                'adjusted_carbs_grams': adjusted_macros['carbs_grams'],
                'adjusted_fats_grams': adjusted_macros['fats_grams'],
                'weekly_caloric_difference': goal_data['weekly_surplus_deficit'],
            }
            
            # Add weight-based metadata if available
            if 'protein_per_kg' in macros:
                result['protein_per_kg'] = macros['protein_per_kg']
            
            return result
        
        except ValueError as ve:
            logger.error(f"Validation error: {str(ve)}")
            raise
        except Exception as e:
            logger.error(f"Failed to calculate nutrition: {str(e)}")
            raise
