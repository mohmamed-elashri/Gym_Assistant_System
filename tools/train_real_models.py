"""Train the two models on the Kaggle datasets in data/ (see data/README.md).

Writes the same artifact names as tools/train_synthetic_models.py, so the app
loads them unchanged. Metrics are computed on a held-out 20 percent split and
describe only these datasets, not accuracy for real users.

Usage:
    python tools/train_real_models.py [--seed 42] [--data data] [--out models]
"""

import argparse
import json
import os
import platform
import sys
from datetime import datetime, timezone

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import accuracy_score, mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, os.path.dirname(__file__))
from train_synthetic_models import (  # noqa: E402
    CALORIE_FEATURES,
    EXPERIENCE_LEVEL_LABELS,
    FITNESS_FEATURES,
)

GYM_FILE = "gym_members_exercise_tracking.csv"
CAL_FILE = "calories.csv"


def load_calories(path):
    df = pd.read_csv(path)
    df["Gender"] = df["Gender"].str.lower().map({"male": 0, "female": 1})
    if df[CALORIE_FEATURES + ["Calories"]].isna().any().any():
        raise ValueError("calories.csv has missing or unknown values")
    return df


def load_fitness(path):
    df = pd.read_csv(path)
    df["Gender"] = df["Gender"].map({"Male": 0, "Female": 1})
    if df[FITNESS_FEATURES + ["Experience_Level"]].isna().any().any():
        raise ValueError("gym members file has missing or unknown values")
    return df


def train(seed=42, data="data", out="models"):
    os.makedirs(out, exist_ok=True)
    metrics = {
        "data": "kaggle",
        "datasets": {
            GYM_FILE: "Gym Members Exercise Dataset (valakhorasani), Apache 2.0 as declared",
            CAL_FILE: "Calories Burnt Prediction (ruchikakumbhar), CC0 as declared",
        },
        "seed": seed,
        "trained_at_utc": datetime.now(timezone.utc).isoformat(),
        "versions": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scikit-learn": sklearn.__version__,
        },
        "note": "Held-out metrics on these datasets only; not real-world accuracy.",
    }

    cal = load_calories(os.path.join(data, CAL_FILE))
    Xtr, Xte, ytr, yte = train_test_split(
        cal[CALORIE_FEATURES], cal["Calories"], test_size=0.2, random_state=seed
    )
    scaler = StandardScaler().fit(Xtr)
    reg = RandomForestRegressor(n_estimators=150, random_state=seed, n_jobs=1)
    reg.fit(scaler.transform(Xtr), ytr)
    pred = reg.predict(scaler.transform(Xte))
    metrics["calorie_model"] = {
        "algorithm": "RandomForestRegressor(n_estimators=150)",
        "rows": int(len(cal)),
        "test_rows": int(len(yte)),
        "mae_kcal": round(float(mean_absolute_error(yte, pred)), 2),
        "r2": round(float(r2_score(yte, pred)), 4),
    }
    joblib.dump(reg, os.path.join(out, "calories_model_final.pkl"))
    joblib.dump(scaler, os.path.join(out, "scaler_final.pkl"))
    joblib.dump(CALORIE_FEATURES, os.path.join(out, "features_list.pkl"))

    fit = load_fitness(os.path.join(data, GYM_FILE))
    Xf, yf = fit[FITNESS_FEATURES], fit["Experience_Level"]
    Xtr, Xte, ytr, yte = train_test_split(
        Xf, yf, test_size=0.2, random_state=seed, stratify=yf
    )
    clf = RandomForestClassifier(n_estimators=100, random_state=seed, n_jobs=1)
    clf.fit(Xtr, ytr)
    majority = float(yte.value_counts(normalize=True).max())
    metrics["fitness_model"] = {
        "algorithm": "RandomForestClassifier(n_estimators=100)",
        "rows": int(len(fit)),
        "test_rows": int(len(yte)),
        "accuracy": round(float(accuracy_score(yte, clf.predict(Xte))), 4),
        "majority_class_baseline": round(majority, 4),
        "label_counts": {
            int(k): int(v) for k, v in yf.value_counts().sort_index().items()
        },
    }
    joblib.dump(clf, os.path.join(out, "fitness_level_model.pkl"))
    joblib.dump(
        {
            "version": "kaggle-1",
            "data": "kaggle",
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
    p.add_argument("--data", default="data")
    p.add_argument("--out", default="models")
    a = p.parse_args()
    print(json.dumps(train(a.seed, a.data, a.out), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
