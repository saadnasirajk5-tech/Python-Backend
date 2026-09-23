# =============================================================================
# PROJECT 3: Model Registry & Lifecycle Management
# =============================================================================
# WHAT YOU LEARN:
#   - Model Registry: centralized catalog of all trained models
#   - Model stages: None → Staging → Production → Archived
#   - Model versioning: multiple versions of the same model
#   - Promotion/demotion workflows with approval checks
#   - Loading models by stage (not hardcoded versions!)
#   - Model aliases and tags for governance
#
# CORE CONCEPT:
#   The Registry is the "source of truth" for which model is in production.
#   Deployment systems don't reference run IDs — they reference stages.
#   When you promote v5 to Production, all your serving code updates automatically
#   because it queries "give me the Production model" not "give me run abc123".
#
# INSTALL:
#   pip install mlflow scikit-learn pandas
# =============================================================================

import mlflow
import mlflow.sklearn
from mlflow.tracking import MlflowClient
from mlflow.entities.model_registry import ModelVersion
import pandas as pd
import numpy as np
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import roc_auc_score, accuracy_score, f1_score
from datetime import datetime
import json, time

# =============================================================================
# SETUP
# =============================================================================
TRACKING_URI   = "./mlruns"
MODEL_NAME     = "breast_cancer_classifier"    # The registered model name
mlflow.set_tracking_uri(TRACKING_URI)
mlflow.set_experiment("model_registry_demo")

# MlflowClient gives you programmatic access to the registry API
client = MlflowClient(tracking_uri=TRACKING_URI)

# =============================================================================
# HELPER: Load and prepare data
# =============================================================================
def get_data():
    data = load_breast_cancer()
    X = pd.DataFrame(data.data, columns=data.feature_names)
    y = pd.Series(data.target)
    return train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# =============================================================================
# STEP 1: Train models and register them
# Multiple versions of the same model name = natural version history
# =============================================================================
def train_and_register(model_class, params: dict, description: str) -> str:
    """
    Trains a model, logs it to MLflow, and REGISTERS it.
    Registration = adds the model to the registry with a version number.
    Each call increments the version number automatically.

    Returns: run_id
    """
    X_train, X_test, y_train, y_test = get_data()

    with mlflow.start_run(run_name=f"{model_class.__name__}_v{int(time.time())}") as run:
        # Train
        pipeline = Pipeline([("scaler", StandardScaler()), ("model", model_class(**params))])
        pipeline.fit(X_train, y_train)

        # Evaluate
        y_pred      = pipeline.predict(X_test)
        y_pred_prob = pipeline.predict_proba(X_test)[:, 1]

        metrics = {
            "test_roc_auc":  round(roc_auc_score(y_test, y_pred_prob), 4),
            "test_accuracy": round(accuracy_score(y_test, y_pred), 4),
            "test_f1":       round(f1_score(y_test, y_pred), 4),
        }

        mlflow.log_params(params)
        mlflow.log_metrics(metrics)
        mlflow.set_tag("model_class", model_class.__name__)
        mlflow.set_tag("description", description)

        # Register the model — this adds it to the Model Registry
        # If MODEL_NAME doesn't exist yet, it's created automatically
        model_info = mlflow.sklearn.log_model(
            pipeline,
            artifact_path="model",
            registered_model_name=MODEL_NAME,   # ← This is what registers it!
        )

        version = client.get_latest_versions(MODEL_NAME, stages=["None"])[0].version
        print(f"  Registered: {MODEL_NAME} v{version} | ROC-AUC={metrics['test_roc_auc']}")

        return run.info.run_id, version, metrics

# =============================================================================
# STEP 2: The model lifecycle — stages and transitions
# =============================================================================
class ModelLifecycleManager:
    """
    Manages the full lifecycle of a model in the registry.
    This is what your MLOps platform / CI/CD pipeline calls.
    """

    def __init__(self, client: MlflowClient, model_name: str):
        self.client     = client
        self.model_name = model_name

    def list_all_versions(self):
        """Shows all registered versions and their current stage."""
        print(f"\n{'─'*60}")
        print(f"Registered versions of '{self.model_name}'")
        print(f"{'─'*60}")
        versions = self.client.search_model_versions(f"name='{self.model_name}'")
        for v in sorted(versions, key=lambda x: int(x.version)):
            print(f"  v{v.version:>3}  Stage={v.current_stage:<12}  "
                  f"Status={v.status:<10}  Run={v.run_id[:8]}...")

    def promote_to_staging(self, version: str, justification: str):
        """
        Moves a model version from None → Staging.
        Staging = "ready for integration testing"
        Always add a comment so you have an audit trail.
        """
        self.client.transition_model_version_stage(
            name=self.model_name,
            version=version,
            stage="Staging",
            archive_existing_versions=False   # Keep other staging models for comparison
        )
        # Add a comment to the version — this creates an audit log
        self.client.update_model_version(
            name=self.model_name,
            version=version,
            description=f"[{datetime.now().isoformat()}] Promoted to Staging. Reason: {justification}"
        )
        print(f"  📦 v{version} → Staging")

    def run_staging_tests(self, version: str) -> bool:
        """
        Automated quality gate: runs tests on the staged model.
        In real MLOps, this is called by your CI/CD pipeline.
        Returns True if model passes all quality checks.
        """
        print(f"\n  Running quality gates for v{version}...")

        # Load the staged model
        model_uri = f"models:/{self.model_name}/{version}"
        model = mlflow.sklearn.load_model(model_uri)

        # Get test data
        _, X_test, _, y_test = get_data()
        y_pred      = model.predict(X_test)
        y_pred_prob = model.predict_proba(X_test)[:, 1]

        roc_auc = roc_auc_score(y_test, y_pred_prob)

        # ── Quality Gate Checks ──────────────────────────────────────────────
        # These are your deployment guardrails — model MUST pass all of these
        checks = {
            "roc_auc >= 0.90":    roc_auc >= 0.90,          # Minimum performance
            "no_nan_predictions": not np.isnan(y_pred).any(), # Sanity check
            "correct_output_dim": len(y_pred) == len(y_test), # Correct shape
            "predicts_both_classes": len(np.unique(y_pred)) > 1, # Not degenerate
        }

        passed = all(checks.values())
        for check_name, result in checks.items():
            status = "✅" if result else "❌"
            print(f"    {status} {check_name}")

        print(f"  Quality gate: {'PASSED ✅' if passed else 'FAILED ❌'} (ROC-AUC={roc_auc:.4f})")
        return passed

    def promote_to_production(self, version: str, approved_by: str):
        """
        Moves model to Production stage.
        IMPORTANT: archive_existing_versions=True automatically moves
        the current production model to Archived — zero-downtime swap!
        """
        self.client.transition_model_version_stage(
            name=self.model_name,
            version=version,
            stage="Production",
            archive_existing_versions=True  # ← Previous production → Archived automatically
        )
        self.client.update_model_version(
            name=self.model_name,
            version=version,
            description=f"[{datetime.now().isoformat()}] PRODUCTION. Approved by: {approved_by}"
        )
        print(f"  🚀 v{version} → Production (previous production auto-archived)")

    def rollback(self, target_version: str, reason: str):
        """
        Emergency rollback: promotes an older version back to Production.
        This is the MOST important operation in production MLOps.
        If a new model breaks things, you can rollback in seconds.
        """
        print(f"\n  ⚠️  ROLLBACK initiated: reverting to v{target_version}")
        self.promote_to_production(target_version, approved_by=f"ROLLBACK: {reason}")
        print(f"  ✅ Rollback complete — v{target_version} is now Production")

    def get_production_model(self):
        """
        THE key pattern: load model by STAGE, not by version number.
        This means your serving code NEVER needs to change when you promote a new version.
        """
        # "models:/model_name/Production" always gets the current production model
        model_uri = f"models:/{self.model_name}/Production"
        model = mlflow.sklearn.load_model(model_uri)
        print(f"  Loaded Production model from registry")
        return model

    def get_model_by_alias(self, alias: str):
        """
        Model aliases (MLflow 2.x feature) = human-readable pointers to versions.
        Better than stages for complex deployment scenarios.
        Example: alias "champion" = current best model
                 alias "challenger" = A/B test candidate
        """
        # Set an alias: client.set_registered_model_alias(name, alias, version)
        model_uri = f"models:/{self.model_name}@{alias}"
        return mlflow.sklearn.load_model(model_uri)


# =============================================================================
# STEP 3: Model comparison — choosing which version to promote
# =============================================================================
def compare_model_versions(model_name: str, versions: list) -> str:
    """
    Compares multiple model versions on a held-out test set.
    Returns the best version number.
    This is what your automated promotion logic should call.
    """
    _, X_test, _, y_test = get_data()
    best_score   = -1
    best_version = None

    print(f"\n{'─'*50}")
    print("Model Version Comparison")
    print(f"{'─'*50}")

    for version in versions:
        model_uri = f"models:/{model_name}/{version}"
        try:
            model = mlflow.sklearn.load_model(model_uri)
            y_pred_prob = model.predict_proba(X_test)[:, 1]
            score = roc_auc_score(y_test, y_pred_prob)
            print(f"  v{version}: ROC-AUC = {score:.4f}")
            if score > best_score:
                best_score   = score
                best_version = version
        except Exception as e:
            print(f"  v{version}: Error loading — {e}")

    print(f"\n  🏆 Best: v{best_version} (ROC-AUC={best_score:.4f})")
    return best_version


# =============================================================================
# MAIN: Full lifecycle demo
# =============================================================================
if __name__ == "__main__":
    print("PROJECT 3: Model Registry & Lifecycle Management\n")

    # ── Train and register 3 model versions ──────────────────────────────────
    print("Training and registering models...")
    run_id1, v1, m1 = train_and_register(
        RandomForestClassifier,
        {"n_estimators": 50, "random_state": 42},
        "Initial baseline — RandomForest 50 trees"
    )
    run_id2, v2, m2 = train_and_register(
        RandomForestClassifier,
        {"n_estimators": 200, "max_depth": 10, "random_state": 42},
        "Improved RF — more trees, depth-limited"
    )
    run_id3, v3, m3 = train_and_register(
        GradientBoostingClassifier,
        {"n_estimators": 100, "learning_rate": 0.1, "random_state": 42},
        "GBM challenger model"
    )

    # ── Run lifecycle operations ──────────────────────────────────────────────
    mgr = ModelLifecycleManager(client, MODEL_NAME)
    mgr.list_all_versions()

    # Promote best candidate to staging
    best_version = compare_model_versions(MODEL_NAME, [v1, v2, v3])
    print(f"\nPromoting best model (v{best_version}) through lifecycle...")

    mgr.promote_to_staging(best_version, "Best ROC-AUC in comparison test")

    # Run automated quality gates
    if mgr.run_staging_tests(best_version):
        mgr.promote_to_production(best_version, approved_by="ml_engineer_team")
    else:
        print("  Model failed quality gates — not promoting to Production")

    mgr.list_all_versions()

    # Demo: load production model (this is what your API would call)
    prod_model = mgr.get_production_model()
    print(f"\n  Production model loaded. Type: {type(prod_model)}")

    # Demo: rollback scenario
    print("\n--- Rollback Demo ---")
    other_version = v1 if best_version != v1 else v2
    mgr.rollback(other_version, "New model causing increased false negatives in production")
    mgr.list_all_versions()

    print("\n✅ Project 3 complete!")
