"""
Retrain the fitness level classifier from the gym members dataset.

Usage (from project root):
    python tools/train_fitness_model.py
"""

import os
from datetime import datetime

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split

EXPERIENCE_LEVEL_LABELS = {
    1: 'مبتدئ',
    2: 'متوسط',
    3: 'متقدم',
}

FEATURES = [
    'Age', 'Gender', 'Weight (kg)', 'Height (m)', 'Max_BPM', 'Avg_BPM',
    'Resting_BPM', 'Fat_Percentage', 'Water_Intake (liters)', 'Workout_Frequency (days/week)',
]


def main():
    models_dir = 'models'
    os.makedirs(models_dir, exist_ok=True)

    dataset_path = 'data/gym_members_exercise_tracking.cv.csv'
    print(f'Loading dataset: {dataset_path}')
    df = pd.read_csv(dataset_path)

    df['Gender'] = df['Gender'].map({'Male': 0, 'Female': 1})
    X = df[FEATURES]
    y = df['Experience_Level']

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    print('Training fitness level classifier...')
    fitness_model = RandomForestClassifier(n_estimators=100, random_state=42)
    fitness_model.fit(X_train, y_train)

    y_pred = fitness_model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f'Fitness model accuracy: {accuracy * 100:.2f}%')
    print('\nClassification report:')
    print(classification_report(y_test, y_pred))

    joblib.dump(fitness_model, os.path.join(models_dir, 'fitness_level_model.pkl'))

    preprocessing_config = {
        'version': '1.1',
        'training_date': datetime.now().isoformat(),
        'gender_mapping': {'Male': 0, 'Female': 1},
        'fitness_labels': fitness_model.classes_.tolist(),
        'fitness_label_names': {
            int(level): EXPERIENCE_LEVEL_LABELS.get(int(level), str(level))
            for level in fitness_model.classes_.tolist()
        },
        'feature_names': FEATURES,
        'feature_dtypes': {col: str(X[col].dtype) for col in FEATURES},
        'bmr_formula': 'Mifflin-St Jeor',
        'activity_multipliers': {
            'sedentary': 1.2,
            'light': 1.375,
            'moderate': 1.55,
            'active': 1.725,
            'very_active': 1.9,
        },
    }
    joblib.dump(
        preprocessing_config,
        os.path.join(models_dir, 'preprocessing_config.pkl'),
    )

    print('Saved:')
    print(f'  - {models_dir}/fitness_level_model.pkl')
    print(f'  - {models_dir}/preprocessing_config.pkl')
    print(f'  - Labels: {preprocessing_config["fitness_label_names"]}')


if __name__ == '__main__':
    main()
