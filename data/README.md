# Datasets

Two public Kaggle datasets are included so the models can be trained on real, openly licensed data. Both were downloaded by the repository owner from Kaggle and are committed unmodified.

| File | Kaggle dataset | Uploader | License (as declared on the Kaggle page) | Rows x columns |
| --- | --- | --- | --- | --- |
| `gym_members_exercise_tracking.csv` | Gym Members Exercise Dataset | valakhorasani | Apache 2.0 | 973 x 15 |
| `calories.csv` | Calories Burnt Prediction | ruchikakumbhar | CC0 1.0 (public domain) | 15000 x 9 |

SHA-256:

```
cfa58990806ea6e1594fb1977d875a0158038e6d492fb95ec9107d29eb632307  gym_members_exercise_tracking.csv
2fa1f6ab63d1b835f1f849ee0825043e456fde84c177600577a7090916b9b7c4  calories.csv
```

## Caveats

- The licenses are the ones the uploaders declared on Kaggle. This project did not verify that the uploaders had the right to apply them, and it does not know how the data were collected. They may be self-reported, simulated or otherwise not clinical measurements.
- The column names match what the original code expected (`tools/train_fitness_model.py` and the six calorie features in `fitness_api/utils.py`). That is consistent with these being the original sources, but it is not proof, so the earlier statement in `docs/MODEL_PROVENANCE.md` that the original data are unrecovered still stands.
- Do not use model outputs as medical or training advice.

## Use

```
python tools/train_real_models.py --out models
```

The script writes the model files the app loads plus `training_metrics.json` with held-out metrics on these datasets. See `docs/MODEL_PROVENANCE.md`.
