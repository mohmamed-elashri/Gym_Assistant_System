"""Unit and integration tests for tools/train_synthetic_models.py."""

import os
import sys

import joblib
import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
import train_synthetic_models as pipe  # noqa: E402


def test_keytel_equation_known_values():
    # Hand-computed from the published coefficients.
    male = pipe.keytel_kcal_per_min(np.array([0]), 30, 70, 130)[0]
    female = pipe.keytel_kcal_per_min(np.array([1]), 30, 70, 130)[0]
    assert male == pytest.approx(
        (-55.0969 + 0.6309 * 130 + 0.1988 * 70 + 0.2017 * 30) / 4.184
    )
    assert female == pytest.approx(
        (-20.4022 + 0.4472 * 130 - 0.1263 * 70 + 0.074 * 30) / 4.184
    )
    assert 4 < male < 15 and 3 < female < 15


def test_data_generation_is_deterministic_and_in_range():
    a = pipe.make_calorie_data(np.random.default_rng(7), 200)
    b = pipe.make_calorie_data(np.random.default_rng(7), 200)
    assert a.equals(b)
    assert a["Heart_Rate"].le(200).all() and a["Calories"].gt(0).all()
    assert list(a.columns[:-1]) == pipe.CALORIE_FEATURES
    f = pipe.make_fitness_data(np.random.default_rng(7), 400)
    assert set(f["Experience_Level"].unique()) == {1, 2, 3}
    assert list(f.columns[:-1]) == pipe.FITNESS_FEATURES


@pytest.fixture(scope="module")
def trained(tmp_path_factory):
    out = tmp_path_factory.mktemp("models")
    metrics = pipe.train(seed=42, rows=1500, out=str(out))
    return out, metrics


def test_artifacts_and_metrics_written(trained):
    out, metrics = trained
    for name in [
        "calories_model_final.pkl",
        "scaler_final.pkl",
        "features_list.pkl",
        "fitness_level_model.pkl",
        "preprocessing_config.pkl",
        "training_metrics.json",
    ]:
        assert (out / name).exists(), name
    assert metrics["data"] == "synthetic"
    assert metrics["calorie_model"]["r2"] > 0.9
    assert metrics["fitness_model"]["accuracy"] > 0.7


def test_training_is_reproducible(tmp_path):
    m1 = pipe.train(seed=3, rows=600, out=str(tmp_path / "a"))
    m2 = pipe.train(seed=3, rows=600, out=str(tmp_path / "b"))
    assert m1["calorie_model"] == m2["calorie_model"]
    assert m1["fitness_model"] == m2["fitness_model"]


def test_trained_calorie_model_is_monotonic_in_duration(trained):
    out, _ = trained
    model = joblib.load(out / "calories_model_final.pkl")
    scaler = joblib.load(out / "scaler_final.pkl")
    feats = joblib.load(out / "features_list.pkl")
    import pandas as pd

    rows = pd.DataFrame([[0, 30, 175, 70, d, 130] for d in (20, 40, 80)], columns=feats)
    p = model.predict(scaler.transform(rows[feats]))
    assert p[0] < p[1] < p[2]


def test_pipeline_artifacts_work_with_the_app(trained, monkeypatch):
    """Integration: the Django model registry loads the generated files."""
    out, _ = trained
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gym_config.settings")
    import django

    django.setup()
    from fitness_api.model_manager import ModelRegistry

    paths = {
        "fitness": "fitness_level_model.pkl",
        "calorie": "calories_model_final.pkl",
        "calorie_scaler": "scaler_final.pkl",
        "calorie_features": "features_list.pkl",
        "preprocessing": "preprocessing_config.pkl",
    }
    monkeypatch.setattr(
        ModelRegistry, "MODEL_PATHS", {k: str(out / v) for k, v in paths.items()}
    )
    monkeypatch.setattr(ModelRegistry, "_models", {})
    from fitness_api.calorie_predictor import predict_calories

    kcal = predict_calories(0, 30, 175, 70, 30, 130)
    assert 100 < kcal < 600
