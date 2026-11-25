# Model provenance

## Status of the original models: unrecoverable

The repository never contained the trained models (`models/*.pkl` is in `.gitignore`) or the training data (`*.csv` is ignored). The history was exported as a single clean import, so it holds no earlier copies. What can be established from the code:

| Model | Evidence in the repository | What is unknown |
| --- | --- | --- |
| Fitness level classifier | `tools/train_fitness_model.py` reads `data/gym_members_exercise_tracking.cv.csv` and uses the columns Age, Gender, Weight (kg), Height (m), Max_BPM, Avg_BPM, Resting_BPM, Fat_Percentage, Water_Intake (liters), Workout_Frequency (days/week) with the label Experience_Level (1 to 3). Random forest, `random_state=42`, 80/20 split. | Where the CSV came from, its license, its row count, and the accuracy of the original model. |
| Calorie model | `fitness_api/utils.py` and `calorie_predictor.py` show a 6-feature input (Gender, Age, Height in cm, Weight, Duration, Heart_Rate), a scaler, and a feature list. No training script exists. | The data source, the algorithm, the training procedure, and any metrics. |

The repository contains no reference to a dataset name, URL, author or license, and there are no notebooks. The file name and column names resemble publicly available gym-tracking datasets, but a resemblance is not a source. **No dataset is credited here because none can be verified.** If the author remembers the source, record it here with its license.

## Replacement pipeline (separate, for review)

`tools/train_synthetic_models.py` creates fully synthetic data and trains replacement models with the same artifact names the app expects.

- Calorie data: heart rate, age, weight and sex are sampled, and calories follow the published Keytel et al. (2005) equation plus small noise. The model therefore learns a published formula, not real measurements.
- Fitness-level data: profiles are sampled and labelled by a simple documented heuristic (sessions per week, resting heart rate, body fat). The labels are not measured fitness levels.
- Determinism: one seed (default 42) drives data generation, the split and the models. Library versions are written to `models/training_metrics.json`.
- No third-party data is used, so there is no dataset license to comply with.

### What the metrics mean

`training_metrics.json` reports MAE/R2 and accuracy on held-out synthetic rows. They show the models recover the generating rule. They do not estimate accuracy for real users, and these models do not reproduce the original ones. Do not present them as medical or training advice.

### Tests

`tests_pipeline/` covers the equation, determinism, artifact creation, reproducibility, monotonic behaviour and loading through `ModelRegistry` and `predict_calories`. CI trains the models before running the suite, so the two previously skipped model tests run.

### If a real dataset is preferred

Choose a dataset whose license permits use and redistribution, record its URL, version and license in this file, and replace `make_*_data` with a loader. Review the license yourself before adding it.

## Kaggle datasets (added)

Two public datasets are committed under `data/` (details, licenses and SHA-256 checksums in `data/README.md`):

- Gym Members Exercise Dataset, uploader valakhorasani, Apache 2.0 as declared, 973 rows.
- Calories Burnt Prediction, uploader ruchikakumbhar, CC0 as declared, 15000 rows.

`tools/train_real_models.py` trains both models on them with the same artifact names. Their columns match what the original code expected, which is consistent with being the original sources but does not prove it, so the original models and data remain unrecovered. The licenses are as displayed on Kaggle; the uploaders' rights and the data collection method were not verified. The calorie model reaches R2 0.998 on held-out rows, which points to a formula-like target in that dataset rather than measured expenditure. Treat all outputs as demonstrations.
