# =============================================================================
# PROJECT 8: Automated Retraining Pipeline
# =============================================================================
# WHAT YOU LEARN:
#   - Automated retraining triggered by drift alerts or schedules
#   - Hyperparameter optimization with Optuna (the best HPO library)
#   - Champion/Challenger model comparison (don't blindly deploy new models!)
#   - Automated rollout vs rollback decision logic
#   - Retraining with feedback loops (online learning pattern)
#   - Airflow DAG for scheduled retraining (config included)
#
# CORE CONCEPT:
#   Manual retraining = bottleneck. Automated retraining = scalable ML.
#   BUT automated doesn't mean blind! Always compare new model vs champion
#   before deploying. A "better" new model on stale eval data can still be
#   worse in production — test, compare, then promote.
#
# INSTALL:
#   pip install optuna mlflow scikit-learn pandas numpy
# =============================================================================

import os
import json
import time
import pickle
import logging
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Tuple

import numpy as np
import pandas as pd
import optuna                              # Best hyperparameter optimization library
from optuna.samplers import TPESampler    # Tree-structured Parzen Estimator
optuna.logging.set_verbosity(optuna.logging.WARNING)   # Suppress verbose output

import mlflow
import mlflow.sklearn
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import roc_auc_score, f1_score

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# =============================================================================
# RETRAINING TRIGGER: Defines when and why retraining should happen
# =============================================================================

@dataclass
class RetrainingTrigger:
    """
    Encapsulates the reason retraining was triggered.
    This metadata is logged alongside the model so you know WHY it was retrained.
    """
    reason:           str     # "drift", "scheduled", "performance_degradation", "manual"
    triggered_at:     str     = field(default_factory=lambda: datetime.now().isoformat())
    drift_percentage: float   = 0.0     # % of features drifted (from Project 7)
    performance_drop: float   = 0.0     # Drop in monitored metric
    schedule:         str     = ""      # e.g. "weekly" or "daily"
    triggered_by:     str     = "automated_system"


def should_retrain(
    drift_report: dict = None,
    current_metrics: dict = None,
    baseline_metrics: dict = None,
    last_retrain_date: datetime = None,
    schedule_days: int = 7,
) -> Tuple[bool, Optional[RetrainingTrigger]]:
    """
    Decision logic: should we retrain now?
    Returns (should_retrain: bool, trigger: RetrainingTrigger or None).

    This function is called by your monitoring system (Project 7) and scheduler.
    """

    # ── Rule 1: Drift-triggered retraining ────────────────────────────────────
    if drift_report is not None:
        drift_pct = drift_report.get("drift_percentage", 0)
        if drift_pct >= 30:   # 30%+ features drifted = trigger retraining
            return True, RetrainingTrigger(
                reason="data_drift",
                drift_percentage=drift_pct,
            )

    # ── Rule 2: Performance-triggered retraining ──────────────────────────────
    if current_metrics and baseline_metrics:
        perf_drop = baseline_metrics.get("roc_auc", 0) - current_metrics.get("roc_auc", 0)
        if perf_drop >= 0.05:   # 5% drop in ROC-AUC = significant degradation
            return True, RetrainingTrigger(
                reason="performance_degradation",
                performance_drop=perf_drop,
            )

    # ── Rule 3: Scheduled retraining ──────────────────────────────────────────
    if last_retrain_date is not None:
        days_since = (datetime.now() - last_retrain_date).days
        if days_since >= schedule_days:
            return True, RetrainingTrigger(
                reason="scheduled",
                schedule=f"every_{schedule_days}_days",
            )

    return False, None


# =============================================================================
# HYPERPARAMETER OPTIMIZATION with Optuna
# =============================================================================

def optimize_hyperparameters(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    n_trials: int = 50,           # More trials = better params but longer runtime
    n_cv_folds: int = 5,
    timeout_seconds: int = 120,   # Hard stop even if n_trials not reached
) -> dict:
    """
    Uses Optuna to find optimal hyperparameters using Bayesian optimization.

    Bayesian optimization vs grid search:
    - Grid search: tries every combination (exponential cost)
    - Random search: tries random combinations (better but still wastes trials)
    - Bayesian (Optuna TPE): learns from previous trials, focuses on promising regions
    Result: finds better params in fewer trials (often 3-10x more efficient).
    """

    def objective(trial: optuna.Trial) -> float:
        """
        Optuna calls this function for each trial.
        `trial.suggest_*` methods define the hyperparameter search space.
        Return the metric to MAXIMIZE (ROC-AUC).
        """
        # Choose model type as a hyperparameter (Optuna can compare model families!)
        model_name = trial.suggest_categorical("model", ["random_forest", "gradient_boosting"])

        if model_name == "random_forest":
            model = RandomForestClassifier(
                n_estimators=trial.suggest_int("n_estimators", 50, 500),
                max_depth=trial.suggest_int("max_depth", 3, 20),
                min_samples_split=trial.suggest_int("min_samples_split", 2, 20),
                min_samples_leaf=trial.suggest_int("min_samples_leaf", 1, 10),
                max_features=trial.suggest_categorical("max_features", ["sqrt", "log2", None]),
                random_state=42, n_jobs=-1
            )
        else:  # gradient_boosting
            model = GradientBoostingClassifier(
                n_estimators=trial.suggest_int("n_estimators", 50, 300),
                learning_rate=trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
                max_depth=trial.suggest_int("max_depth", 2, 8),
                subsample=trial.suggest_float("subsample", 0.5, 1.0),
                min_samples_split=trial.suggest_int("min_samples_split", 2, 20),
                random_state=42,
            )

        pipeline = Pipeline([("scaler", StandardScaler()), ("model", model)])

        # Use cross-validation to estimate performance (more robust than single split)
        scores = cross_val_score(
            pipeline, X_train, y_train,
            cv=n_cv_folds, scoring="roc_auc", n_jobs=-1
        )

        # Optuna minimizes by default — return negative if using minimize
        # But we configured to maximize, so return positive
        return scores.mean()

    # Create study with TPE sampler (Bayesian optimization)
    sampler = TPESampler(seed=42)   # Seed for reproducibility
    study   = optuna.create_study(
        direction="maximize",       # We want to maximize ROC-AUC
        sampler=sampler,
        pruner=optuna.pruners.MedianPruner(n_startup_trials=10)  # Prune bad trials early
    )

    logger.info(f"Starting HPO: {n_trials} trials, {timeout_seconds}s timeout...")
    study.optimize(objective, n_trials=n_trials, timeout=timeout_seconds,
                   show_progress_bar=False)

    best_params = study.best_params
    best_score  = study.best_value

    logger.info(f"HPO complete: best ROC-AUC={best_score:.4f}")
    logger.info(f"Best params: {best_params}")

    # Show trial history (useful for debugging HPO)
    df_trials = study.trials_dataframe()
    logger.info(f"Trials summary:\n{df_trials[['number','value','params_model']].head(10)}")

    return best_params, best_score, study


def build_model_from_params(params: dict) -> Pipeline:
    """Constructs a Pipeline from the optimized params dict."""
    model_name = params.get("model", "random_forest")

    if model_name == "random_forest":
        model = RandomForestClassifier(
            n_estimators=params.get("n_estimators", 100),
            max_depth=params.get("max_depth", 10),
            min_samples_split=params.get("min_samples_split", 2),
            min_samples_leaf=params.get("min_samples_leaf", 1),
            max_features=params.get("max_features", "sqrt"),
            random_state=42, n_jobs=-1
        )
    else:
        model = GradientBoostingClassifier(
            n_estimators=params.get("n_estimators", 100),
            learning_rate=params.get("learning_rate", 0.1),
            max_depth=params.get("max_depth", 3),
            subsample=params.get("subsample", 0.8),
            random_state=42,
        )

    return Pipeline([("scaler", StandardScaler()), ("model", model)])


# =============================================================================
# CHAMPION / CHALLENGER FRAMEWORK
# =============================================================================

class ChampionChallenger:
    """
    The golden rule of automated deployment:
    Never deploy a new model just because training finished.
    Always compare new (Challenger) vs current production (Champion).
    Only promote if Challenger is statistically better.
    """

    def __init__(self, min_improvement: float = 0.005):
        # Challenger must beat champion by at least 0.5% to be worth deploying
        # Avoids unnecessary deployments for noise-level improvements
        self.min_improvement = min_improvement

    def compare(
        self,
        champion:    Pipeline,
        challenger:  Pipeline,
        X_test:      pd.DataFrame,
        y_test:      pd.Series,
        n_bootstrap: int = 1000,     # Bootstrap samples for confidence interval
    ) -> dict:
        """
        Compares champion vs challenger using bootstrap confidence intervals.
        Bootstrap is more statistically rigorous than a single test split.
        """
        champ_preds  = champion.predict_proba(X_test.values)[:, 1]
        chall_preds  = challenger.predict_proba(X_test.values)[:, 1]
        y_arr        = y_test.values

        # Bootstrap: sample with replacement n_bootstrap times
        champ_scores = []
        chall_scores = []
        np.random.seed(42)

        for _ in range(n_bootstrap):
            idx = np.random.choice(len(y_arr), len(y_arr), replace=True)
            champ_scores.append(roc_auc_score(y_arr[idx], champ_preds[idx]))
            chall_scores.append(roc_auc_score(y_arr[idx], chall_preds[idx]))

        champ_mean = np.mean(champ_scores)
        chall_mean = np.mean(chall_scores)
        improvement = chall_mean - champ_mean

        # 95% confidence interval
        champ_ci = np.percentile(champ_scores, [2.5, 97.5])
        chall_ci = np.percentile(chall_scores, [2.5, 97.5])

        # Probability that challenger is better (proportion of bootstrap samples where challenger wins)
        p_challenger_better = np.mean(np.array(chall_scores) > np.array(champ_scores))

        should_promote = (improvement >= self.min_improvement and p_challenger_better >= 0.75)

        result = {
            "champion_roc_auc":       round(champ_mean, 4),
            "challenger_roc_auc":     round(chall_mean, 4),
            "improvement":            round(improvement, 4),
            "champion_ci_95":         [round(champ_ci[0], 4), round(champ_ci[1], 4)],
            "challenger_ci_95":       [round(chall_ci[0], 4), round(chall_ci[1], 4)],
            "p_challenger_better":    round(p_challenger_better, 3),
            "should_promote":         should_promote,
            "decision":               "PROMOTE CHALLENGER" if should_promote else "KEEP CHAMPION",
        }

        print(f"\n{'─'*50}")
        print(f"Champion vs Challenger Comparison")
        print(f"{'─'*50}")
        print(f"  Champion:   ROC-AUC={result['champion_roc_auc']} CI=[{result['champion_ci_95'][0]}, {result['champion_ci_95'][1]}]")
        print(f"  Challenger: ROC-AUC={result['challenger_roc_auc']} CI=[{result['challenger_ci_95'][0]}, {result['challenger_ci_95'][1]}]")
        print(f"  Improvement: {improvement:+.4f} | P(challenger better): {p_challenger_better:.1%}")
        print(f"  Decision: {'🚀 ' if should_promote else '🔒 '}{result['decision']}")

        return result


# =============================================================================
# FULL AUTOMATED RETRAINING PIPELINE
# =============================================================================

def run_retraining_pipeline(trigger: RetrainingTrigger, n_hpo_trials: int = 30):
    """
    Full automated retraining pipeline:
    1. Load data
    2. Run HPO
    3. Train challenger
    4. Compare vs champion
    5. Promote if better
    6. Log everything to MLflow
    """
    mlflow.set_tracking_uri("./mlruns")
    mlflow.set_experiment("automated_retraining")

    logger.info(f"🔄 Retraining triggered: reason={trigger.reason}")

    with mlflow.start_run(run_name=f"retrain_{trigger.reason}_{datetime.now():%Y%m%d_%H%M}"):

        mlflow.set_tags({
            "trigger_reason":   trigger.reason,
            "triggered_by":     trigger.triggered_by,
            "drift_percentage": trigger.drift_percentage,
            "performance_drop": trigger.performance_drop,
        })

        # ── 1. Load data ──────────────────────────────────────────────────────
        data = load_breast_cancer()
        X = pd.DataFrame(data.data, columns=data.feature_names)
        y = pd.Series(data.target)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        logger.info(f"Data loaded: {len(X_train)} train, {len(X_test)} test")

        # ── 2. Hyperparameter optimization ────────────────────────────────────
        best_params, best_cv_score, study = optimize_hyperparameters(
            X_train, y_train, n_trials=n_hpo_trials
        )
        mlflow.log_params(best_params)
        mlflow.log_metric("hpo_best_cv_roc_auc", best_cv_score)
        mlflow.log_metric("hpo_n_trials", len(study.trials))

        # ── 3. Train challenger with best params ──────────────────────────────
        challenger = build_model_from_params(best_params)
        challenger.fit(X_train, y_train)

        challenger_score = roc_auc_score(y_test, challenger.predict_proba(X_test.values)[:, 1])
        mlflow.log_metric("challenger_test_roc_auc", challenger_score)

        # ── 4. Load champion (previous best model) ────────────────────────────
        champion_path = Path("./model_artifacts/model.pkl")
        if champion_path.exists():
            with open(champion_path, "rb") as f:
                champion = pickle.load(f)
            logger.info("Champion loaded from disk")
        else:
            # No existing champion → challenger becomes champion automatically
            champion = None
            logger.info("No existing champion — challenger will be auto-promoted")

        # ── 5. Champion/Challenger comparison ────────────────────────────────
        if champion is not None:
            cc = ChampionChallenger(min_improvement=0.005)
            comparison = cc.compare(champion, challenger, X_test, y_test)
            mlflow.log_metrics({
                "champion_roc_auc":    comparison["champion_roc_auc"],
                "challenger_roc_auc":  comparison["challenger_roc_auc"],
                "improvement":         comparison["improvement"],
            })
            should_deploy = comparison["should_promote"]
        else:
            should_deploy = True
            comparison   = {"decision": "AUTO-PROMOTED (no champion)"}

        # ── 6. Deploy if challenger wins ──────────────────────────────────────
        if should_deploy:
            os.makedirs("./model_artifacts", exist_ok=True)
            with open("./model_artifacts/model.pkl", "wb") as f:
                pickle.dump(challenger, f)

            version_info = {
                "version":          datetime.now().strftime("%Y%m%d_%H%M%S"),
                "roc_auc":          challenger_score,
                "trigger_reason":   trigger.reason,
                "best_params":      best_params,
                "comparison":       comparison,
            }
            with open("./model_artifacts/metadata.json", "w") as f:
                json.dump(version_info, f, indent=2)

            mlflow.sklearn.log_model(challenger, artifact_path="model")
            mlflow.set_tag("deployed", "true")
            logger.info(f"✅ Challenger deployed! ROC-AUC={challenger_score:.4f}")
        else:
            mlflow.set_tag("deployed", "false")
            logger.info(f"🔒 Champion retained. Challenger not better enough.")

        return should_deploy, comparison


# =============================================================================
# AIRFLOW DAG (printed as config — shows the orchestration approach)
# =============================================================================

AIRFLOW_DAG = '''
# airflow_dag.py — Save this in your Airflow DAGs folder
# Runs retraining pipeline every Sunday at 2 AM

from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.empty import EmptyOperator
from datetime import datetime, timedelta
from automated_retrain import should_retrain, run_retraining_pipeline, RetrainingTrigger

default_args = {
    "owner":            "ml_team",
    "retries":          2,
    "retry_delay":      timedelta(minutes=5),
    "email_on_failure": True,
    "email":            ["ml-team@company.com"],
}

with DAG(
    dag_id="ml_retraining_pipeline",
    schedule_interval="0 2 * * 0",     # Every Sunday at 2 AM
    start_date=datetime(2024, 1, 1),
    default_args=default_args,
    catchup=False,
    tags=["mlops", "retraining"],
) as dag:

    # Task 1: Check if retraining is needed
    def check_retrain_needed(**context):
        retrain, trigger = should_retrain(schedule_days=7)
        if retrain:
            context["ti"].xcom_push("trigger", trigger.__dict__)
            return "retrain_model"       # Branch: go to retraining
        return "skip_retraining"         # Branch: skip

    check_task = BranchPythonOperator(
        task_id="check_retrain_needed",
        python_callable=check_retrain_needed,
    )

    # Task 2a: Run retraining
    def run_retrain(**context):
        trigger_dict = context["ti"].xcom_pull(task_ids="check_retrain_needed", key="trigger")
        trigger = RetrainingTrigger(**trigger_dict)
        run_retraining_pipeline(trigger)

    retrain_task = PythonOperator(
        task_id="retrain_model",
        python_callable=run_retrain,
    )

    # Task 2b: Skip (no retraining needed)
    skip_task = EmptyOperator(task_id="skip_retraining")

    # Task 3: Post-deployment validation (runs after both branches)
    validate_task = EmptyOperator(task_id="validate_deployment", trigger_rule="none_failed")

    check_task >> [retrain_task, skip_task] >> validate_task
'''


# =============================================================================
# MAIN
# =============================================================================
if __name__ == "__main__":
    print("PROJECT 8: Automated Retraining Pipeline\n")

    # Simulate a drift-triggered retraining
    drift_trigger = RetrainingTrigger(
        reason="data_drift",
        drift_percentage=45.0,
        triggered_by="monitoring_system"
    )

    should_retrain_now, _ = should_retrain(
        drift_report={"drift_percentage": 45.0},
        last_retrain_date=datetime.now() - timedelta(days=10)
    )
    print(f"Should retrain? {should_retrain_now}")

    if should_retrain_now:
        deployed, comparison = run_retraining_pipeline(drift_trigger, n_hpo_trials=15)
        print(f"\nResult: {'Deployed' if deployed else 'Not deployed'}")

    print("\n✅ Project 8 complete!")
    print("KEY INSIGHT: HPO + Champion/Challenger = automated quality control.")
    print("Never blindly deploy. Always compare. Always log. Always have rollback.")
