# Project 01 — Experiment Tracking with MLflow

## What This Is
The FOUNDATION of MLOps. Before you can improve a model, you need to track
what you already tried. MLflow is the industry standard for this.

## What You Learn
- Logging params, metrics, tags, and artifacts to MLflow
- Comparing multiple model runs in the UI
- Saving and loading models from the registry
- Auto-logging with zero boilerplate

## Files
- `train.py` — Full experiment tracking example (heavily commented)

## Run It
```bash
pip install mlflow scikit-learn pandas numpy matplotlib seaborn
python train.py
mlflow ui
# Open http://localhost:5000 to see all runs
```

## Key Concepts
| Term       | Meaning                                      |
|------------|----------------------------------------------|
| Experiment | Named group of runs (e.g. "churn_model_v2")  |
| Run        | One training execution                       |
| Params     | Inputs to training (hyperparams, config)     |
| Metrics    | Outputs of training (accuracy, loss, etc.)   |
| Artifacts  | Files attached to a run (model, plots, data) |
| Tags       | Searchable labels (team, version, env)       |

## Elite Tips
1. **Always log `random_seed`** as a param — reproducibility requires it
2. **Log metrics at each epoch** with `mlflow.log_metric("loss", val, step=epoch)` for curves
3. **Use nested runs** for hyperparameter sweeps: parent run = sweep, child runs = trials
4. **Log input data hash** so you know which data version trained this model
