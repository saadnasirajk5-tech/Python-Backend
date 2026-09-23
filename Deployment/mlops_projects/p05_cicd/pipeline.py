# =============================================================================
# PROJECT 5: CI/CD Pipeline for Machine Learning
# =============================================================================
# WHAT YOU LEARN:
#   - Full CI/CD pipeline for ML (train → test → validate → deploy)
#   - Automated model quality gates (min performance, regression tests)
#   - GitHub Actions workflow for ML (the YAML you'll use in production)
#   - Model packaging for deployment (Docker, MLflow serving)
#   - Blue-green deployment strategy for zero-downtime model swaps
#   - How to test ML code (unit tests, integration tests, model tests)
#
# CORE CONCEPT:
#   CI (Continuous Integration) = every code push triggers automated
#     training, testing, and validation.
#   CD (Continuous Deployment) = if CI passes, automatically deploy to staging.
#     Production promotion requires a human approval gate.
#
# FILES IN THIS PROJECT:
#   pipeline.py          ← This file: the ML pipeline logic
#   test_model.py        ← Automated tests for the model
#   github_actions.yaml  ← CI/CD workflow (copy to .github/workflows/)
#   Dockerfile           ← Container for model serving
# =============================================================================

import subprocess
import sys
import json
import pickle
import hashlib
import os
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
import pandas as pd
import numpy as np
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import roc_auc_score, accuracy_score, f1_score

# =============================================================================
# CONFIGURATION: All pipeline settings in one place
# In CI/CD, these come from environment variables or a config file
# =============================================================================
@dataclass
class PipelineConfig:
    # Model training
    model_type:        str   = "random_forest"
    n_estimators:      int   = 100
    max_depth:         int   = 10
    random_seed:       int   = 42
    test_size:         float = 0.20

    # Quality gates — pipeline FAILS if model doesn't meet these
    min_roc_auc:       float = 0.90     # Minimum acceptable ROC-AUC
    min_accuracy:      float = 0.88     # Minimum acceptable accuracy
    min_f1:            float = 0.85     # Minimum acceptable F1
    max_regression:    float = 0.03     # Max allowed drop vs previous best model

    # Paths
    model_output_dir:  str   = "./model_artifacts"
    metrics_file:      str   = "./metrics.json"
    baseline_file:     str   = "./baseline_metrics.json"


# =============================================================================
# STEP 1: DATA PIPELINE
# =============================================================================
def run_data_pipeline(config: PipelineConfig) -> tuple:
    """
    Data pipeline stage: load, validate, split.
    In CI/CD this runs first. If data validation fails, the whole pipeline fails.
    """
    print("\n[STAGE 1/4] Data Pipeline")
    print("─" * 40)

    # Load data (in production: query from data warehouse / feature store)
    data = load_breast_cancer()
    X = pd.DataFrame(data.data, columns=data.feature_names)
    y = pd.Series(data.target, name="target")

    # ── Data validation (fail fast if data is bad) ────────────────────────────
    assert X.isnull().sum().sum() == 0,  "❌ Null values found in features!"
    assert len(X) >= 100,                "❌ Dataset too small (< 100 rows)!"
    assert y.nunique() == 2,             "❌ Expected binary target!"
    assert X.shape[1] > 0,              "❌ No feature columns found!"

    # Check class balance (warn but don't fail)
    class_balance = y.value_counts(normalize=True)
    if class_balance.min() < 0.1:
        print(f"  ⚠️  Severe class imbalance: {class_balance.to_dict()}")
    else:
        print(f"  ✅ Data validated: {len(X)} rows, {X.shape[1]} features, balanced={class_balance.min():.2%}")

    # Compute data fingerprint for reproducibility tracking
    data_hash = hashlib.md5(pd.util.hash_pandas_object(X).values.tobytes()).hexdigest()
    print(f"  📌 Data fingerprint: {data_hash[:12]}...")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=config.test_size,
        random_state=config.random_seed, stratify=y
    )
    print(f"  Split: {len(X_train)} train, {len(X_test)} test")
    return X_train, X_test, y_train, y_test, data_hash


# =============================================================================
# STEP 2: TRAINING PIPELINE
# =============================================================================
def run_training_pipeline(X_train, y_train, config: PipelineConfig):
    """
    Training stage: builds and fits the model pipeline.
    Logs training metadata for traceability.
    """
    print("\n[STAGE 2/4] Training Pipeline")
    print("─" * 40)

    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("model",  RandomForestClassifier(
            n_estimators=config.n_estimators,
            max_depth=config.max_depth,
            random_state=config.random_seed,
            n_jobs=-1   # Use all CPU cores
        ))
    ])

    start = datetime.now()
    pipeline.fit(X_train, y_train)
    train_time = (datetime.now() - start).total_seconds()

    print(f"  ✅ Model trained in {train_time:.2f}s")
    print(f"  Config: n_estimators={config.n_estimators}, max_depth={config.max_depth}")
    return pipeline


# =============================================================================
# STEP 3: EVALUATION + QUALITY GATES
# =============================================================================
def run_evaluation_pipeline(pipeline, X_test, y_test, config: PipelineConfig) -> dict:
    """
    Evaluation stage: compute metrics and CHECK QUALITY GATES.
    Quality gates are non-negotiable thresholds — if the model doesn't meet them,
    the CI/CD pipeline FAILS and nothing gets deployed. This prevents regressions.
    """
    print("\n[STAGE 3/4] Evaluation & Quality Gates")
    print("─" * 40)

    y_pred      = pipeline.predict(X_test)
    y_pred_prob = pipeline.predict_proba(X_test)[:, 1]

    metrics = {
        "roc_auc":  round(roc_auc_score(y_test, y_pred_prob), 4),
        "accuracy": round(accuracy_score(y_test, y_pred), 4),
        "f1":       round(f1_score(y_test, y_pred), 4),
        "timestamp": datetime.now().isoformat(),
        "n_test_samples": len(y_test),
    }

    print(f"  Metrics: ROC-AUC={metrics['roc_auc']} | Accuracy={metrics['accuracy']} | F1={metrics['f1']}")

    # ── QUALITY GATES ─────────────────────────────────────────────────────────
    # These are your automated guardrails. Think of them as unit tests for model quality.
    gates = {
        f"roc_auc >= {config.min_roc_auc}":   metrics["roc_auc"]  >= config.min_roc_auc,
        f"accuracy >= {config.min_accuracy}": metrics["accuracy"] >= config.min_accuracy,
        f"f1 >= {config.min_f1}":             metrics["f1"]       >= config.min_f1,
    }

    # Regression gate: compare vs previously deployed model (stored in baseline file)
    if Path(config.baseline_file).exists():
        with open(config.baseline_file) as f:
            baseline = json.load(f)
        delta = metrics["roc_auc"] - baseline.get("roc_auc", 0)
        gates[f"no_regression (Δ >= -{config.max_regression})"] = delta >= -config.max_regression
        print(f"  Baseline ROC-AUC: {baseline.get('roc_auc', 'N/A')} | Delta: {delta:+.4f}")

    all_passed = True
    for gate_name, passed in gates.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}  {gate_name}")
        if not passed:
            all_passed = False

    metrics["gates_passed"] = all_passed
    return metrics, all_passed


# =============================================================================
# STEP 4: PACKAGING + DEPLOYMENT ARTIFACTS
# =============================================================================
def run_packaging_pipeline(pipeline, metrics: dict, data_hash: str, config: PipelineConfig):
    """
    Packaging stage: saves model artifacts in a structured, deployable format.
    Creates everything needed to serve the model in production.
    """
    print("\n[STAGE 4/4] Packaging & Artifacts")
    print("─" * 40)

    output_dir = Path(config.model_output_dir)
    output_dir.mkdir(exist_ok=True)

    # ── Save model ─────────────────────────────────────────────────────────────
    model_path = output_dir / "model.pkl"
    with open(model_path, "wb") as f:
        pickle.dump(pipeline, f)

    model_size = model_path.stat().st_size
    print(f"  💾 Model saved: {model_path} ({model_size:,} bytes)")

    # ── Save metadata (everything needed to understand this model) ─────────────
    metadata = {
        "model_version":    datetime.now().strftime("%Y%m%d_%H%M%S"),
        "data_fingerprint": data_hash,
        "metrics":          metrics,
        "config":           {
            "model_type":   config.model_type,
            "n_estimators": config.n_estimators,
            "max_depth":    config.max_depth,
            "random_seed":  config.random_seed,
        },
        "python_version":   sys.version,
        "created_at":       datetime.now().isoformat(),
    }
    meta_path = output_dir / "metadata.json"
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)

    # ── Save metrics (used by next CI run for regression gating) ───────────────
    with open(config.metrics_file, "w") as f:
        json.dump(metrics, f, indent=2)

    # ── Generate a simple prediction contract (schema) ────────────────────────
    # This documents what inputs the model expects — critical for API teams
    contract = {
        "model_name":     "breast_cancer_classifier",
        "version":        metadata["model_version"],
        "input_features": list(load_breast_cancer().feature_names),
        "output":         {"type": "binary", "classes": [0, 1], "probabilities": True},
        "latency_sla_ms": 100,
    }
    contract_path = output_dir / "contract.json"
    with open(contract_path, "w") as f:
        json.dump(contract, f, indent=2)

    print(f"  📋 Metadata saved: {meta_path}")
    print(f"  📑 Contract saved: {contract_path}")
    print(f"  Version: {metadata['model_version']}")

    return output_dir, metadata


# =============================================================================
# FULL PIPELINE RUNNER
# =============================================================================
def run_pipeline(config: PipelineConfig = None) -> bool:
    """
    Runs the complete CI/CD pipeline. Returns True if all stages pass.
    This is what your GitHub Actions workflow calls.
    """
    config = config or PipelineConfig()
    print("=" * 50)
    print("MLOps CI/CD Pipeline")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    try:
        # Stage 1: Data
        X_train, X_test, y_train, y_test, data_hash = run_data_pipeline(config)

        # Stage 2: Training
        model = run_training_pipeline(X_train, y_train, config)

        # Stage 3: Evaluation
        metrics, gates_passed = run_evaluation_pipeline(model, X_test, y_test, config)
        if not gates_passed:
            print("\n❌ PIPELINE FAILED: Quality gates not met. Aborting deployment.")
            return False

        # Stage 4: Packaging
        output_dir, metadata = run_packaging_pipeline(model, metrics, data_hash, config)

        # Update baseline for next run's regression gating
        with open(config.baseline_file, "w") as f:
            json.dump({"roc_auc": metrics["roc_auc"]}, f)

        print("\n" + "=" * 50)
        print("✅ PIPELINE PASSED — Model ready for deployment")
        print(f"   Version: {metadata['model_version']}")
        print(f"   ROC-AUC: {metrics['roc_auc']}")
        print(f"   Artifacts: {output_dir}/")
        print("=" * 50)
        return True

    except AssertionError as e:
        print(f"\n❌ PIPELINE FAILED (data validation): {e}")
        return False
    except Exception as e:
        print(f"\n❌ PIPELINE FAILED (unexpected error): {e}")
        raise


if __name__ == "__main__":
    success = run_pipeline()
    sys.exit(0 if success else 1)   # Return non-zero exit code on failure (CI/CD reads this)
