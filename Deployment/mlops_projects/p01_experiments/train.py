# =============================================================================
# PROJECT 1: Experiment Tracking with MLflow
# =============================================================================
# WHAT YOU LEARN:
#   - Log every experiment: params, metrics, artifacts, models
#   - Compare runs visually in the MLflow UI
#   - Organize runs into experiments
#   - Auto-logging vs manual logging
#   - Tag runs for easy filtering
#
# CORE CONCEPT:
#   An "experiment" = a named group of runs (e.g. "churn_model_v2")
#   A "run"         = one training execution with its own params/metrics
#   Every run is immutable and reproducible — the foundation of MLOps
#
# RUN THIS:
#   pip install mlflow scikit-learn pandas numpy
#   python train.py
#   mlflow ui  ← opens dashboard at http://localhost:5000
# =============================================================================

import mlflow                          # Core MLflow library
import mlflow.sklearn                  # MLflow's scikit-learn integration
import numpy as np
import pandas as pd
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, confusion_matrix
)
from sklearn.pipeline import Pipeline
import matplotlib.pyplot as plt
import seaborn as sns
import json, os, time
from pathlib import Path

# =============================================================================
# SETUP: Point MLflow at a local tracking server (file-based by default)
# In production, this would be: mlflow.set_tracking_uri("http://mlflow-server:5000")
# =============================================================================
MLFLOW_TRACKING_URI = "./mlruns"       # Store run data in ./mlruns folder
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

# Experimentslate group red runs together — like a project folder
# If the experiment already exists, mlflow just sets it as active
EXPERIMENT_NAME = "breast_cancer_classification"
mlflow.set_experiment(EXPERIMENT_NAME)

# =============================================================================
# DATA: Load and prepare the dataset
# =============================================================================
def load_data():
    """
    Loads the breast cancer dataset and returns train/test splits.
    In real MLOps you'd load from a feature store or data lake.
    """
    data = load_breast_cancer()
    X = pd.DataFrame(data.data, columns=data.feature_names)
    y = pd.Series(data.target, name="target")

    # Stratified split: ensures class balance in train and test sets
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.2,
        random_state=42,
        stratify=y          # IMPORTANT: preserves class distribution
    )
    return X_train, X_test, y_train, y_test

# =============================================================================
# EVALUATION: Compute all metrics + generate plots
# =============================================================================
def evaluate_model(model, X_test, y_test, run_dir: str) -> dict:
    """
    Evaluates model and returns metric dict.
    Saves confusion matrix as artifact.
    """
    y_pred      = model.predict(X_test)
    y_pred_prob = model.predict_proba(X_test)[:, 1]   # Probability of positive class

    metrics = {
        "accuracy":  round(accuracy_score(y_test, y_pred), 4),
        "precision": round(precision_score(y_test, y_pred), 4),
        "recall":    round(recall_score(y_test, y_pred), 4),
        "f1":        round(f1_score(y_test, y_pred), 4),
        "roc_auc":   round(roc_auc_score(y_test, y_pred_prob), 4),
    }

    # ---------- Confusion Matrix Plot ----------
    # Save as artifact — MLflow stores any file you attach to a run
    cm = confusion_matrix(y_test, y_pred)
    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", ax=ax)
    ax.set_xlabel("Predicted"); ax.set_ylabel("Actual")
    ax.set_title("Confusion Matrix")
    cm_path = os.path.join(run_dir, "confusion_matrix.png")
    os.makedirs(run_dir, exist_ok=True)
    fig.savefig(cm_path, dpi=100, bbox_inches="tight")
    plt.close(fig)

    return metrics, cm_path

# =============================================================================
# CORE TRAINING FUNCTION: One run = one call to this function
# =============================================================================
def train_and_log(model_name: str, model, params: dict,
                  X_train, X_test, y_train, y_test):
    """
    Trains a model and logs EVERYTHING to MLflow.
    This is the core MLOps pattern: every training run is fully reproducible.

    Args:
        model_name: Human-readable name for this run
        model:      Scikit-learn estimator
        params:     Hyperparameters (logged to MLflow)
        X_train, X_test, y_train, y_test: Data splits
    """

    # mlflow.start_run() creates a new run in the active experiment
    # Using a context manager ensures the run is always closed properly
    with mlflow.start_run(run_name=model_name) as run:
        run_id = run.info.run_id
        print(f"\n{'='*60}")
        print(f"  Run: {model_name} | ID: {run_id[:8]}...")
        print(f"{'='*60}")

        # ── STEP 1: Log tags (searchable labels, not numeric) ──────────────
        # Tags are great for filtering runs in the UI
        mlflow.set_tags({
            "model_family": model_name.split("_")[0],     # e.g. "RandomForest"
            "dataset":      "breast_cancer",
            "engineer":     "your_name_here",
            "version":      "1.0",
            "environment":  "development"
        })

        # ── STEP 2: Log hyperparameters ────────────────────────────────────
        # Params are immutable once logged — they define what was trained
        mlflow.log_params(params)
        mlflow.log_param("train_size", len(X_train))
        mlflow.log_param("test_size",  len(X_test))
        mlflow.log_param("n_features", X_train.shape[1])

        # ── STEP 3: Build pipeline (scaler + model) ────────────────────────
        # Pipeline ensures the same preprocessing is always applied
        pipeline = Pipeline([
            ("scaler", StandardScaler()),   # Normalize features
            ("model",  model)
        ])

        # ── STEP 4: Cross-validation (log per-fold metrics) ────────────────
        cv_scores = cross_val_score(pipeline, X_train, y_train, cv=5, scoring="roc_auc")
        mlflow.log_metric("cv_roc_auc_mean", round(cv_scores.mean(), 4))
        mlflow.log_metric("cv_roc_auc_std",  round(cv_scores.std(), 4))
        print(f"  CV ROC-AUC: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

        # ── STEP 5: Train the model ────────────────────────────────────────
        start_time = time.time()
        pipeline.fit(X_train, y_train)
        training_time = round(time.time() - start_time, 3)
        mlflow.log_metric("training_time_seconds", training_time)

        # ── STEP 6: Evaluate and log metrics ──────────────────────────────
        tmp_dir = f"./tmp_{run_id[:8]}"
        metrics, cm_path = evaluate_model(pipeline, X_test, y_test, tmp_dir)
        mlflow.log_metrics(metrics)   # Log all metrics at once
        print(f"  Metrics: {json.dumps(metrics, indent=2)}")

        # ── STEP 7: Log artifacts (files attached to this run) ─────────────
        mlflow.log_artifact(cm_path, artifact_path="plots")  # Folder in artifacts

        # Log feature importance (for tree-based models)
        if hasattr(model, "feature_importances_"):
            fi = pd.DataFrame({
                "feature":    X_train.columns,
                "importance": model.feature_importances_
            }).sort_values("importance", ascending=False)
            fi_path = os.path.join(tmp_dir, "feature_importance.csv")
            fi.to_csv(fi_path, index=False)
            mlflow.log_artifact(fi_path, artifact_path="data")

        # Log the training config as a JSON artifact (easy to load later)
        config = {"model": model_name, "params": params, "metrics": metrics}
        config_path = os.path.join(tmp_dir, "config.json")
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        mlflow.log_artifact(config_path, artifact_path="config")

        # ── STEP 8: Log the model itself ──────────────────────────────────
        # mlflow.sklearn.log_model() saves the model so it can be loaded later
        # The "model" artifact_path is the conventional name
        mlflow.sklearn.log_model(
            pipeline,
            artifact_path="model",
            registered_model_name=f"cancer_{model_name.lower().replace(' ', '_')}",
            input_example=X_test.head(3),   # Sample input for documentation
        )
        print(f"  Model saved to MLflow registry as: cancer_{model_name.lower()}")

        # Clean up temp files
        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)

        return run_id, metrics

# =============================================================================
# EXPERIMENT: Run multiple models and compare
# =============================================================================
def run_experiment():
    """
    Runs multiple model configurations and logs them all.
    This is the MLOps workflow: try many things, track everything, pick the best.
    """
    X_train, X_test, y_train, y_test = load_data()
    print(f"Data loaded: {X_train.shape[0]} train, {X_test.shape[0]} test samples")

    # Define experiments: (run_name, model, hyperparams)
    experiments = [
        (
            "RandomForest_baseline",
            RandomForestClassifier(n_estimators=100, random_state=42),
            {"n_estimators": 100, "max_depth": "none", "model_type": "random_forest"}
        ),
        (
            "RandomForest_deep",
            RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42),
            {"n_estimators": 200, "max_depth": 10, "model_type": "random_forest"}
        ),
        (
            "GradientBoosting",
            GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, random_state=42),
            {"n_estimators": 100, "learning_rate": 0.1, "model_type": "gradient_boosting"}
        ),
        (
            "LogisticRegression_L2",
            LogisticRegression(C=1.0, max_iter=1000, random_state=42),
            {"C": 1.0, "penalty": "l2", "model_type": "logistic_regression"}
        ),
    ]

    results = []
    for name, model, params in experiments:
        run_id, metrics = train_and_log(
            name, model, params, X_train, X_test, y_train, y_test
        )
        results.append({"run": name, "run_id": run_id, **metrics})

    # ── COMPARE RESULTS ────────────────────────────────────────────────────
    print("\n" + "="*60)
    print("EXPERIMENT SUMMARY")
    print("="*60)
    df_results = pd.DataFrame(results).sort_values("roc_auc", ascending=False)
    print(df_results[["run", "accuracy", "f1", "roc_auc"]].to_string(index=False))

    best = df_results.iloc[0]
    print(f"\n🏆 Best model: {best['run']} with ROC-AUC={best['roc_auc']}")
    print(f"\nView all runs: mlflow ui --backend-store-uri {MLFLOW_TRACKING_URI}")
    print("Then open: http://localhost:5000")

    return df_results

# =============================================================================
# DEMO: How to load a logged model back from MLflow
# =============================================================================
def load_best_model_demo(run_id: str):
    """
    Shows how to reload any model from MLflow using its run ID.
    This is how CI/CD pipelines promote models to production.
    """
    # Load model directly from a run ID — completely reproducible
    model_uri = f"runs:/{run_id}/model"
    loaded_model = mlflow.sklearn.load_model(model_uri)
    print(f"\nSuccessfully loaded model from run {run_id[:8]}...")
    return loaded_model


# =============================================================================
# BONUS: MLflow Autologging — zero-code logging
# =============================================================================
def demo_autolog():
    """
    mlflow.sklearn.autolog() automatically logs params + metrics + model.
    Zero lines of log_* code needed. Great for quick experiments.
    """
    mlflow.sklearn.autolog(
        log_input_examples=True,
        log_model_signatures=True,
        log_models=True,
        silent=False
    )
    X_train, X_test, y_train, y_test = load_data()
    with mlflow.start_run(run_name="autolog_demo"):
        rf = RandomForestClassifier(n_estimators=50, random_state=0)
        rf.fit(X_train, y_train)
        # MLflow automatically captured: all RF params, fit time, training metrics!
    print("Autolog run complete — check MLflow UI for auto-captured metrics")


if __name__ == "__main__":
    results = run_experiment()
    best_run_id = results.iloc[0]["run_id"]
    load_best_model_demo(best_run_id)
    print("\n✅ Project 1 complete! Run: mlflow ui")
