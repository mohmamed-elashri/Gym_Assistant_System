import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gym_config.settings')
django.setup()

from fitness_api.nutrition_calculator import NutritionCalculator
from fitness_api.calorie_predictor import predict_calories
from fitness_api.model_manager import ModelRegistry

nutrition = NutritionCalculator.calculate_full_nutrition(
    weight_kg=75, height_m=1.75, age_years=30,
    activity_level='moderate', gender=0,
)

print('=== Nutrition (Male 75kg 175cm 30y moderate) ===')
print(f"BMR: {nutrition['bmr']:.0f} kcal")
print(f"Daily: {nutrition['daily_calories']} kcal")
print(f"BMI: {nutrition['bmi']} ({nutrition['bmi_category']})")
print(
    f"Protein: {nutrition['protein_grams']}g | "
    f"Carbs: {nutrition['carbs_grams']}g | "
    f"Fats: {nutrition['fats_grams']}g"
)
print(f"Water: {nutrition['water_with_exercise_liters']}L")

print('\n=== Calorie predictions ===')
for duration, heart_rate in [(20, 100), (30, 130), (60, 130), (45, 160)]:
    kcal = predict_calories(0, 30, 175, 75, duration, heart_rate)
    print(f'{duration}min @ {heart_rate}bpm -> {kcal} kcal ({kcal / duration:.1f} kcal/min)')

print('\n=== Fitness labels ===')
print(ModelRegistry.get_fitness_labels())
