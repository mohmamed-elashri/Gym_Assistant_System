"""Integrity and training smoke tests for the Kaggle datasets in data/."""

import hashlib
import os
import sys

import joblib

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(ROOT, "tools"))
import train_real_models as real  # noqa: E402

DATA = os.path.join(ROOT, "data")


def sha256(name):
    with open(os.path.join(DATA, name), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def test_checksums_match_readme():
    readme = open(os.path.join(DATA, "README.md"), encoding="utf-8").read()
    assert sha256(real.GYM_FILE) in readme
    assert sha256(real.CAL_FILE) in readme


def test_row_counts_and_no_missing_values():
    cal = real.load_calories(os.path.join(DATA, real.CAL_FILE))
    fit = real.load_fitness(os.path.join(DATA, real.GYM_FILE))
    assert len(cal) == 15000
    assert len(fit) == 973
    assert set(fit["Experience_Level"].unique()) == {1, 2, 3}


def test_training_writes_loadable_artifacts(tmp_path):
    m = real.train(seed=1, data=DATA, out=str(tmp_path))
    assert m["calorie_model"]["r2"] > 0.5
    assert (
        m["fitness_model"]["accuracy"]
        > m["fitness_model"]["majority_class_baseline"] - 0.05
    )
    for name in (
        "calories_model_final.pkl",
        "fitness_level_model.pkl",
        "scaler_final.pkl",
    ):
        assert joblib.load(tmp_path / name) is not None
