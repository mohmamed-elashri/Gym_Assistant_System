import logging

from .model_manager import ModelRegistry
from .utils import prepare_calorie_model_input

logger = logging.getLogger(__name__)
CALORIE_MODEL_VERSION = 'calories_model_final_v1'


def _validate_inputs(gender, age, height_cm, weight_kg, duration, heart_rate):
    if gender not in [0, 1]:
        raise ValueError("Gender must be 0 (male) or 1 (female)")
    if not (10 <= age <= 100):
        raise ValueError("Age must be between 10 and 100")
    if not (100 <= height_cm <= 220):
        raise ValueError("Height must be between 100 and 220 cm")
    if not (30 <= weight_kg <= 200):
        raise ValueError("Weight must be between 30 and 200 kg")
    if not (1 <= duration <= 300):
        raise ValueError("Duration must be between 1 and 300 minutes")
    if not (40 <= heart_rate <= 220):
        raise ValueError("Heart rate must be between 40 and 220 bpm")

    max_hr = 220 - age
    if heart_rate > max_hr:
        raise ValueError(f"Heart rate {heart_rate} exceeds age-adjusted max {max_hr}")


def predict_calories(gender, age, height_cm, weight_kg, duration, heart_rate):
    """
    Predict workout calories using the centralized calorie model pipeline.

    Args:
        gender: 0 = male, 1 = female
        age: age in years
        height_cm: height in centimeters
        weight_kg: weight in kilograms
        duration: workout duration in minutes
        heart_rate: average heart rate in bpm

    Returns:
        float: predicted calories burned
    """
    _validate_inputs(gender, age, height_cm, weight_kg, duration, heart_rate)

    input_data = prepare_calorie_model_input(
        gender=gender,
        age=age,
        height_cm=height_cm,
        weight_kg=weight_kg,
        duration_min=duration,
        heart_rate=heart_rate
    )

    scaler = ModelRegistry.get_model('calorie_scaler')
    model = ModelRegistry.get_model('calorie')
    features = ModelRegistry.get_model('calorie_features')

    input_scaled = scaler.transform(input_data[features])
    prediction = float(model.predict(input_scaled)[0])

    expected_min = duration * 3
    expected_max = duration * 20
    if not (expected_min * 0.3 <= prediction <= expected_max * 2):
        raise ValueError(
            f"النتيجة غير منطقية: {prediction:.0f} kcal لمدة {duration} دقيقة"
        )

    logger.info(
        "Calorie prediction | version=%s | input=%s | output_kcal=%.1f",
        CALORIE_MODEL_VERSION,
        {
            "gender": gender,
            "age": age,
            "height_cm": height_cm,
            "weight_kg": weight_kg,
            "duration_min": duration,
            "heart_rate": heart_rate,
        },
        prediction,
    )

    return round(prediction, 1)
