"""
Utility functions for ML model preprocessing and data alignment.
Ensures consistent feature order, units, and data types across all endpoints.
"""

import pandas as pd
import logging

logger = logging.getLogger(__name__)


def prepare_calorie_model_input(gender, age, height_cm, weight_kg, duration_min, heart_rate):
    """
    Centralized function to prepare calorie model input for the new 6-feature model.
    **CRITICAL**: Ensures correct feature order expected by scaler/model pipeline.
    
    Args:
        gender: 0 for male, 1 for female (integer)
        age: age in years (integer)
        height_cm: height in centimeters (float)
        weight_kg: weight in kilograms (float)
        duration_min: duration in MINUTES (float) - NOT seconds!
        heart_rate: heart rate in bpm (integer)
    
    Returns:
        pd.DataFrame with correct columns for the new calorie model
    
    Example:
        >>> cal_input = prepare_calorie_model_input(
        ...     gender=0, age=30, height_cm=175, weight_kg=70,
        ...     duration_min=30, heart_rate=130
        ... )
        >>> # Height is in cm, duration is in minutes
        >>> prediction = calorie_model.predict(cal_input)
    """
    try:
        # Validate inputs
        if not isinstance(gender, (int, float)) or gender not in [0, 1]:
            raise ValueError(f"gender must be 0 (male) or 1 (female), got {gender}")
        
        if not isinstance(age, (int, float)) or age <= 0:
            raise ValueError(f"age must be positive, got {age}")
        
        if not isinstance(height_cm, (int, float)) or height_cm <= 0:
            raise ValueError(f"height_cm must be positive, got {height_cm}")
        
        if not isinstance(weight_kg, (int, float)) or weight_kg <= 0:
            raise ValueError(f"weight_kg must be positive, got {weight_kg}")
        
        if not isinstance(duration_min, (int, float)) or duration_min <= 0:
            raise ValueError(f"duration_min must be positive, got {duration_min}")
        
        if not isinstance(heart_rate, (int, float)) or heart_rate <= 0:
            raise ValueError(f"heart_rate must be positive, got {heart_rate}")
        
        # Create DataFrame with new 6-feature order expected by trained pipeline
        df = pd.DataFrame([[
            int(gender),
            int(age),
            float(height_cm),
            float(weight_kg),
            float(duration_min),
            float(heart_rate),
        ]], columns=['Gender', 'Age', 'Height', 'Weight', 'Duration', 'Heart_Rate'])
        
        logger.debug(
            "Calorie input prepared for new model: Height=%.1fcm, Duration=%.1fmin",
            df['Height'].iloc[0],
            df['Duration'].iloc[0],
        )
        return df
    
    except Exception as e:
        logger.error(f"Failed to prepare calorie model input: {str(e)}")
        raise


def prepare_fitness_model_input(age, gender, weight_kg, height_m, 
                               max_bpm, avg_bpm, resting_bpm,
                               fat_percentage, water_intake, workout_frequency):
    """
    Prepare fitness level classification model input.
    
    Args:
        age: age in years (integer)
        gender: 0 for male, 1 for female (integer)
        weight_kg: weight in kilograms (float)
        height_m: height in meters (float) - keep in meters
        max_bpm: max heart rate (integer)
        avg_bpm: average heart rate (integer)
        resting_bpm: resting heart rate (integer)
        fat_percentage: body fat percentage (float)
        water_intake: daily water intake in liters (float)
        workout_frequency: workouts per week (integer)
    
    Returns:
        pd.DataFrame with correct columns
    """
    try:
        df = pd.DataFrame([[
            int(age),
            int(gender),
            float(weight_kg),
            float(height_m),             # Keep in meters
            int(max_bpm),
            int(avg_bpm),
            int(resting_bpm),
            float(fat_percentage),
            float(water_intake),
            int(workout_frequency)
        ]], columns=[
            'Age', 'Gender', 'Weight (kg)', 'Height (m)', 'Max_BPM', 'Avg_BPM',
            'Resting_BPM', 'Fat_Percentage', 'Water_Intake (liters)', 'Workout_Frequency (days/week)'
        ])
        
        logger.debug("Fitness input prepared successfully")
        return df
    
    except Exception as e:
        logger.error(f"Failed to prepare fitness model input: {str(e)}")
        raise
