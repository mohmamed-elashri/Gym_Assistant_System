"""Reproducible REPLACEMENT training pipeline (synthetic data).

The original training data for this project could not be recovered (see
docs/MODEL_PROVENANCE.md). This script does NOT reproduce the original
models. It builds a fully synthetic, seeded dataset from a published
equation and a documented rule, trains models, and writes artifacts under
models/ using the file names that fitness_api.model_manager expects.

Usage:
    python tools/train_synthetic_models.py [--seed 42] [--rows 5000] [--out models]

Metrics are written to <out>/training_metrics.json. They measure how well the
models recover the generating rule on held-out synthetic data. They say
nothing about accuracy on real people.
"""

import argparse
import json
import os
import platform
from datetime import datetime, timezone

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import accuracy_score, mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

CALORIE_FEATURES = ["Gender", "Age", "Height", "Weight", "Duration", "Heart_Rate"]
FITNESS_FEATURES = [
    "Age",
    "Gender",
    "Weight (kg)",
    "Height (m)",
    "Max_BPM",
    "Avg_BPM",
    "Resting_BPM",
    "Fat_Percentage",
    "Water_Intake (liters)",
    "Workout_Frequency (days/week)",
]
EXPERIENCE_LEVEL_LABELS = {1: "مبتدئ", 2: "متوسط", 3: "متقدم"}


def keytel_kcal_per_min(gender, age, weight_kg, heart_rate):
    """Keytel et al. (2005), J Sports Sci 23(3):289-297.

    Published regression for energy expenditure from heart rate.
    gender: 0 male, 1 female. Returns kcal per minute.
    """
    male = (-55.0969 + 0.6309 * heart_rate + 0.1988 * weight_kg + 0.2017 * age) / 4.184
    female = (-20.4022 + 0.4472 * heart_rate - 0.1263 * weight_kg + 0.074 * age) / 4.184
    return np.where(gender == 0, male, female)


def make_calorie_data(rng, rows):
    gender = rng.integers(0, 2, rows)
    age = rng.integers(16, 70, rows)
    height = np.where(gender == 0, rng.normal(176, 7, rows), rng.normal(163, 6, rows))
    height = np.clip(height, 140, 210).round(1)
    bmi = rng.normal(24.5, 3.5, rows).clip(17, 38)
    weight = (bmi * (height / 100) ** 2).clip(40, 140).round(1)
    duration = rng.integers(5, 121, rows)
    max_hr = 220 - age
    heart_rate = (max_hr * rng.uniform(0.5, 0.92, rows)).round().clip(60, 200)
    kcal = keytel_kcal_per_min(gender, age, weight, heart_rate) * duration
    kcal = np.clip(kcal + rng.normal(0, 3, rows), 1, None)  # small measurement noise
    return pd.DataFrame(
        {
            "Gender": gender,
            "Age": age,
            "Height": height,
            "Weight": weight,
            "Duration": duration,
            "Heart_Rate": heart_rate,
            "Calories": kcal.round(1),
        }
    )


def make_fitness_data(rng, rows):
    """Synthetic profiles. Labels come from a documented HEURISTIC, not from
    measured fitness or any real dataset: score = more weekly sessions, lower
    resting heart rate and lower body fat give a higher level."""
    gender = rng.integers(0, 2, rows)
    age = rng.integers(18, 60, rows)
    weight = rng.normal(75, 14, rows).clip(45, 130).round(1)
    height = rng.normal(1.72, 0.09, rows).clip(1.5, 2.0).round(2)
    resting = rng.normal(65, 8, rows).clip(45, 95).round()
    max_bpm = (220 - age + rng.normal(0, 4, rows)).round()
    avg_bpm = (max_bpm * rng.uniform(0.6, 0.85, rows)).round()
    fat = rng.normal(24, 7, rows).clip(8, 45).round(1)
    water = rng.normal(2.5, 0.6, rows).clip(1, 4.5).round(1)
    freq = rng.integers(1, 7, rows)
    score = (
        freq * 1.0 + (70 - resting) / 8.0 + (30 - fat) / 8.0 + rng.normal(0, 0.4, rows)
    )
    level = np.where(score < 3.0, 1, np.where(score < 5.0, 2, 3))
    return pd.DataFrame(
        {
            "Age": age,
            "Gender": gender,
            "Weight (kg)": weight,
            "Height (m)": height,
            "Max_BPM": max_bpm,
            "Avg_BPM": avg_bpm,
            "Resting_BPM": resting,
            "Fat_Percentage": fat,
            "Water_Intake (liters)": water,
            "Workout_Frequency (days/week)": freq,
            "Experience_Level": level,
        }
    )


def train(seed=42, rows=5000, out="models"):
    os.makedirs(out, exist_ok=True)
    rng = np.random.default_rng(seed)
    metrics = {
        "data": "synthetic",
        "seed": seed,
        "rows": rows,
        "trained_at_utc": datetime.now(timezone.utc).isoformat(),
        "versions": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scikit-learn": sklearn.__version__,
        },
        "note": "Metrics are on held-out SYNTHETIC data and do not estimate real-world accuracy.",
    }

    cal = make_calorie_data(rng, rows)
    Xc, yc = cal[CALORIE_FEATURES], cal["Calories"]
    Xtr, Xte, ytr, yte = train_test_split(Xc, yc, test_size=0.2, random_state=seed)
    scaler = StandardScaler().fit(Xtr)
    reg = RandomForestRegressor(n_estimators=150, random_state=seed, n_jobs=1)
    reg.fit(scaler.transform(Xtr), ytr)
    pred = reg.predict(scaler.transform(Xte))
    metrics["calorie_model"] = {
        "algorithm": "RandomForestRegressor(n_estimators=150)",
        "mae_kcal": round(float(mean_absolute_error(yte, pred)), 2),
        "r2": round(float(r2_score(yte, pred)), 4),
        "test_rows": int(len(yte)),
    }
    joblib.dump(reg, os.path.join(out, "calories_model_final.pkl"))
    joblib.dump(scaler, os.path.join(out, "scaler_final.pkl"))
    joblib.dump(CALORIE_FEATURES, os.path.join(out, "features_list.pkl"))

    fit = make_fitness_data(rng, rows)
    Xf, yf = fit[FITNESS_FEATURES], fit["Experience_Level"]
    Xtr, Xte, ytr, yte = train_test_split(
        Xf, yf, test_size=0.2, random_state=seed, stratify=yf
    )
    clf = RandomForestClassifier(n_estimators=100, random_state=seed, n_jobs=1)
    clf.fit(Xtr, ytr)
    metrics["fitness_model"] = {
        "algorithm": "RandomForestClassifier(n_estimators=100)",
        "accuracy": round(float(accuracy_score(yte, clf.predict(Xte))), 4),
        "label_counts": {
            int(k): int(v) for k, v in yf.value_counts().sort_index().items()
        },
        "test_rows": int(len(yte)),
    }
    joblib.dump(clf, os.path.join(out, "fitness_level_model.pkl"))
    joblib.dump(
        {
            "version": "synthetic-1",
            "data": "synthetic",
            "gender_mapping": {"Male": 0, "Female": 1},
            "fitness_labels": clf.classes_.tolist(),
            "fitness_label_names": {
                int(k): EXPERIENCE_LEVEL_LABELS[int(k)] for k in clf.classes_.tolist()
            },
            "feature_names": FITNESS_FEATURES,
            "feature_dtypes": {c: str(Xf[c].dtype) for c in FITNESS_FEATURES},
        },
        os.path.join(out, "preprocessing_config.pkl"),
    )
    with open(os.path.join(out, "training_metrics.json"), "w", encoding="utf-8") as fh:
        json.dump(metrics, fh, indent=2, ensure_ascii=False)
    return metrics


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--rows", type=int, default=5000)
    p.add_argument("--out", default="models")
    a = p.parse_args()
    print(json.dumps(train(a.seed, a.rows, a.out), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
