# =============================================================================
# PROJECT 10: Full MLOps Platform — Everything Integrated
# =============================================================================
# WHAT YOU LEARN:
#   - How all 9 projects connect into ONE cohesive system
#   - The MLOps Platform class: orchestrates the full ML lifecycle
#   - Event-driven architecture: drift → retrain → test → deploy → monitor
#   - Configuration management with Hydra-style YAML
#   - Comprehensive logging and audit trail
#   - Production checklist: what you need before going live
#   - Real companies' MLOps stacks (Google Vertex AI, AWS SageMaker, Azure ML)
#
# THIS IS THE CAPSTONE: Read it, understand it, then build your own.
#
# ARCHITECTURE:
#
#  ┌─────────────────────────────────────────────────────────────────┐
#  │                    MLOps Platform                                │
#  │                                                                  │
#  │  Data Layer         Model Layer          Serving Layer           │
#  │  ─────────          ───────────          ─────────────           │
#  │  Feature Store  →   Experiment       →   Model Server            │
#  │  DVC versioning     Tracking             A/B Router              │
#  │  Data validation    Model Registry       Canary Deploy           │
#  │                     HPO (Optuna)         Shadow Mode             │
#  │                                                                  │
#  │  Monitoring Layer       Orchestration Layer                      │
#  │  ────────────────        ───────────────────                     │
#  │  Drift Detection    ←→   Airflow/Prefect DAGs                    │
#  │  Performance Monitor     CI/CD (GitHub Actions)                  │
#  │  Alerting                Event-driven triggers                   │
#  └─────────────────────────────────────────────────────────────────┘
#
# =============================================================================

import json
import logging
import os
import pickle
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.datasets import load_breast_cancer
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s"
)
logger = logging.getLogger("mlops_platform")


# =============================================================================
# PLATFORM EVENTS: Everything is event-driven
# =============================================================================

class EventType(Enum):
    """All possible events in the MLOps lifecycle."""
    DATA_VALIDATED       = "data_validated"
    DATA_DRIFT_DETECTED  = "data_drift_detected"
    TRAINING_STARTED     = "training_started"
    TRAINING_COMPLETED   = "training_completed"
    QUALITY_GATE_PASSED  = "quality_gate_passed"
    QUALITY_GATE_FAILED  = "quality_gate_failed"
    MODEL_REGISTERED     = "model_registered"
    MODEL_PROMOTED       = "model_promoted"
    MODEL_DEPLOYED       = "model_deployed"
    MODEL_ROLLED_BACK    = "model_rolled_back"
    PREDICTION_SERVED    = "prediction_served"
    ALERT_TRIGGERED      = "alert_triggered"
    RETRAINING_TRIGGERED = "retraining_triggered"


@dataclass
class PlatformEvent:
    """Immutable event record — the audit log of your entire ML system."""
    event_id:   str
    event_type: str
    timestamp:  str
    payload:    Dict[str, Any]
    source:     str    # Which component emitted this event


class EventBus:
    """
    Simple in-memory event bus.
    In production: use Kafka, RabbitMQ, or AWS EventBridge.
    Components publish events here; other components subscribe and react.
    """

    def __init__(self):
        self._handlers: Dict[str, List] = {}   # event_type → list of handlers
        self._log: List[PlatformEvent] = []     # Immutable audit log

    def subscribe(self, event_type: EventType, handler):
        """Register a handler to be called when an event fires."""
        key = event_type.value
        if key not in self._handlers:
            self._handlers[key] = []
        self._handlers[key].append(handler)

    def publish(self, event: PlatformEvent):
        """Fire an event — all subscribers are notified."""
        self._log.append(event)
        logger.info(f"Event: {event.event_type} from {event.source}")
        for handler in self._handlers.get(event.event_type, []):
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Event handler failed: {e}")

    def emit(self, source: str, event_type: EventType, payload: dict = None):
        """Convenience method to create and publish an event."""
        event = PlatformEvent(
            event_id=str(uuid.uuid4())[:8],
            event_type=event_type.value,
            timestamp=datetime.now().isoformat(),
            payload=payload or {},
            source=source,
        )
        self.publish(event)
        return event

    def get_audit_log(self, event_type: str = None) -> List[PlatformEvent]:
        if event_type:
            return [e for e in self._log if e.event_type == event_type]
        return self._log


# =============================================================================
# DATA COMPONENT (from Projects 2 + 4)
# =============================================================================

class DataManager:
    """Manages data loading, validation, and versioning."""

    def __init__(self, bus: EventBus):
        self.bus = bus

    def load_and_validate(self) -> tuple:
        """Loads data and validates it. Publishes events for both outcomes."""
        data = load_breast_cancer()
        X = pd.DataFrame(data.data, columns=data.feature_names)
        y = pd.Series(data.target, name="target")

        # Validate
        checks = {
            "no_nulls":       X.isnull().sum().sum() == 0,
            "min_rows":       len(X) >= 100,
            "binary_target":  y.nunique() == 2,
            "no_inf":         not np.isinf(X.values).any(),
        }
        all_passed = all(checks.values())
        failed     = [k for k, v in checks.items() if not v]

        self.bus.emit("data_manager", EventType.DATA_VALIDATED, {
            "n_rows": len(X), "n_features": X.shape[1],
            "passed": all_passed, "failed_checks": failed,
        })

        if not all_passed:
            raise ValueError(f"Data validation failed: {failed}")

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        return X_train, X_test, y_train, y_test, data.feature_names

    def check_drift(self, reference: pd.DataFrame,
                     current: pd.DataFrame) -> dict:
        """Simple drift check. Full version in Project 7."""
        from scipy import stats
        drifted_features = []
        for col in reference.columns:
            _, p = stats.ks_2samp(reference[col].values, current[col].values)
            if p < 0.05:
                drifted_features.append(col)

        drift_pct = len(drifted_features) / len(reference.columns) * 100
        drift_detected = drift_pct >= 30

        self.bus.emit("data_manager", EventType.DATA_DRIFT_DETECTED if drift_detected
                       else EventType.DATA_VALIDATED,
                       {"drift_percentage": drift_pct, "drifted": drift_detected})
        return {"drift_percentage": drift_pct, "drifted": drift_detected}


# =============================================================================
# TRAINING COMPONENT (from Projects 1 + 8)
# =============================================================================

class TrainingManager:
    """Manages model training, HPO, and experiment tracking."""

    def __init__(self, bus: EventBus, artifacts_dir: str = "./platform_artifacts"):
        self.bus           = bus
        self.artifacts_dir = Path(artifacts_dir)
        self.artifacts_dir.mkdir(exist_ok=True)

    def train(self, X_train, y_train, config: dict = None) -> Pipeline:
        """Trains a model pipeline and logs to MLflow."""
        config = config or {"n_estimators": 100, "max_depth": 10, "random_state": 42}

        self.bus.emit("training_manager", EventType.TRAINING_STARTED, {"config": config})

        pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("model",  RandomForestClassifier(**config, n_jobs=-1))
        ])

        start = time.time()
        pipeline.fit(X_train, y_train)
        train_time = time.time() - start

        self.bus.emit("training_manager", EventType.TRAINING_COMPLETED,
                      {"train_time_seconds": round(train_time, 2)})
        return pipeline

    def evaluate(self, pipeline, X_test, y_test) -> dict:
        """Computes evaluation metrics."""
        y_pred = pipeline.predict(X_test)
        y_prob = pipeline.predict_proba(X_test)[:, 1]
        return {
            "roc_auc":  round(roc_auc_score(y_test, y_prob), 4),
            "accuracy": round(accuracy_score(y_test, y_pred), 4),
            "f1":       round(f1_score(y_test, y_pred), 4),
        }

    def check_quality_gates(self, metrics: dict, thresholds: dict) -> bool:
        """Runs quality gates. Publishes pass/fail event."""
        failures = []
        for metric, threshold in thresholds.items():
            if metrics.get(metric, 0) < threshold:
                failures.append(f"{metric}={metrics.get(metric, 0):.4f} < {threshold}")

        passed = len(failures) == 0
        event  = EventType.QUALITY_GATE_PASSED if passed else EventType.QUALITY_GATE_FAILED
        self.bus.emit("training_manager", event,
                      {"passed": passed, "failures": failures, "metrics": metrics})
        return passed

    def save_model(self, pipeline, metadata: dict) -> str:
        """Saves model + metadata to artifacts dir."""
        version    = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_path = self.artifacts_dir / f"model_{version}.pkl"

        with open(model_path, "wb") as f:
            pickle.dump(pipeline, f)

        meta_path = self.artifacts_dir / f"model_{version}_meta.json"
        metadata["version"] = version
        metadata["saved_at"] = datetime.now().isoformat()
        with open(meta_path, "w") as f:
            json.dump(metadata, f, indent=2)

        # Update "latest" symlink equivalent
        latest_path = self.artifacts_dir / "model_latest.pkl"
        with open(latest_path, "wb") as f:
            pickle.dump(pipeline, f)

        self.bus.emit("training_manager", EventType.MODEL_REGISTERED,
                      {"version": version, "path": str(model_path)})
        return version

    def compare_with_champion(self, challenger, X_test, y_test) -> tuple:
        """Champion/Challenger comparison. Full version in Project 8."""
        champion_path = self.artifacts_dir / "model_latest.pkl"
        if not champion_path.exists():
            return True, None   # No champion → auto-promote

        with open(champion_path, "rb") as f:
            champion = pickle.load(f)

        champ_score = roc_auc_score(y_test, champion.predict_proba(X_test.values)[:, 1])
        chall_score = roc_auc_score(y_test, challenger.predict_proba(X_test.values)[:, 1])
        improvement = chall_score - champ_score

        return (improvement >= 0.005), {
            "champion_roc_auc": round(champ_score, 4),
            "challenger_roc_auc": round(chall_score, 4),
            "improvement": round(improvement, 4),
        }


# =============================================================================
# SERVING COMPONENT (from Project 6)
# =============================================================================

class ServingManager:
    """Manages model deployment and predictions."""

    def __init__(self, bus: EventBus):
        self.bus           = bus
        self.active_model  = None
        self.active_version = "none"
        self.prediction_count = 0

    def deploy(self, pipeline, version: str):
        """Deploys a model for serving."""
        self.active_model   = pipeline
        self.active_version = version
        self.bus.emit("serving_manager", EventType.MODEL_DEPLOYED,
                      {"version": version})
        logger.info(f"  ✅ Model v{version} deployed and serving")

    def predict(self, features: np.ndarray) -> dict:
        """Serves a prediction."""
        if self.active_model is None:
            raise RuntimeError("No model deployed!")

        start  = time.time()
        pred   = int(self.active_model.predict(features.reshape(1, -1))[0])
        proba  = float(self.active_model.predict_proba(features.reshape(1, -1))[0, pred])
        latency = (time.time() - start) * 1000

        self.prediction_count += 1
        self.bus.emit("serving_manager", EventType.PREDICTION_SERVED,
                      {"prediction": pred, "confidence": proba,
                       "latency_ms": round(latency, 2),
                       "model_version": self.active_version})
        return {"prediction": pred, "confidence": proba, "model_version": self.active_version}

    def rollback(self, reason: str):
        """Emergency rollback — would reload previous version in production."""
        self.bus.emit("serving_manager", EventType.MODEL_ROLLED_BACK,
                      {"reason": reason, "from_version": self.active_version})
        logger.warning(f"  ⚠️  ROLLBACK triggered: {reason}")


# =============================================================================
# MONITORING COMPONENT (from Project 7)
# =============================================================================

class MonitoringManager:
    """Monitors model performance and data drift in production."""

    def __init__(self, bus: EventBus):
        self.bus             = bus
        self.prediction_log  = []
        self.performance_log = []

        # React to prediction events — log them for drift analysis
        bus.subscribe(EventType.PREDICTION_SERVED, self._on_prediction)

    def _on_prediction(self, event: PlatformEvent):
        """Automatically logs every prediction for monitoring."""
        self.prediction_log.append({
            "timestamp":  event.timestamp,
            "confidence": event.payload.get("confidence", 0),
            "prediction": event.payload.get("prediction", -1),
        })

    def check_confidence_drift(self, window: int = 100) -> bool:
        """
        Quick monitoring: if average confidence drops significantly,
        the model may be seeing out-of-distribution data.
        """
        if len(self.prediction_log) < window * 2:
            return False

        recent = [r["confidence"] for r in self.prediction_log[-window:]]
        hist   = [r["confidence"] for r in self.prediction_log[-window*2:-window]]

        recent_mean = np.mean(recent)
        hist_mean   = np.mean(hist)
        drop        = hist_mean - recent_mean

        if drop > 0.1:   # 10% drop in confidence = alert
            self.bus.emit("monitoring_manager", EventType.ALERT_TRIGGERED,
                          {"alert_type": "confidence_drop",
                           "drop": round(drop, 4),
                           "recent_mean": round(recent_mean, 4)})
            return True
        return False


# =============================================================================
# THE MLOPS PLATFORM: Orchestrates all components
# =============================================================================

class MLOpsPlatform:
    """
    The top-level orchestrator.
    Wires all components together and defines the full ML lifecycle.
    """

    QUALITY_THRESHOLDS = {
        "roc_auc":  0.90,
        "accuracy": 0.88,
        "f1":       0.85,
    }

    def __init__(self):
        self.bus        = EventBus()
        self.data       = DataManager(self.bus)
        self.training   = TrainingManager(self.bus)
        self.serving    = ServingManager(self.bus)
        self.monitoring = MonitoringManager(self.bus)

        # Subscribe retraining_manager to drift events
        self.bus.subscribe(EventType.DATA_DRIFT_DETECTED, self._on_drift_detected)

        logger.info("MLOps Platform initialized ✅")

    def _on_drift_detected(self, event: PlatformEvent):
        """Automatically triggers retraining when drift is detected."""
        drift_pct = event.payload.get("drift_percentage", 0)
        if drift_pct >= 30:
            logger.warning(f"🔄 Auto-retraining triggered by drift ({drift_pct:.0f}%)")
            self.bus.emit("platform", EventType.RETRAINING_TRIGGERED,
                          {"trigger": "data_drift", "drift_percentage": drift_pct})

    def run_full_lifecycle(self) -> dict:
        """
        Runs the complete ML lifecycle end-to-end.
        This is what your Airflow DAG calls on a schedule.
        """
        print("\n" + "="*60)
        print("  MLOps Platform — Full Lifecycle Run")
        print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)

        results = {}

        # ── Phase 1: Data ───────────────────────────────────────────────────
        print("\n[Phase 1] Data Management")
        X_train, X_test, y_train, y_test, feature_names = self.data.load_and_validate()
        print(f"  ✅ Data loaded: {len(X_train)} train, {len(X_test)} test")

        # ── Phase 2: Training ───────────────────────────────────────────────
        print("\n[Phase 2] Model Training")
        pipeline = self.training.train(
            X_train, y_train,
            config={"n_estimators": 150, "max_depth": 8, "random_state": 42}
        )
        metrics = self.training.evaluate(pipeline, X_test, y_test)
        print(f"  Metrics: {json.dumps(metrics)}")

        # ── Phase 3: Quality Gates ──────────────────────────────────────────
        print("\n[Phase 3] Quality Gates")
        gates_passed = self.training.check_quality_gates(metrics, self.QUALITY_THRESHOLDS)
        if not gates_passed:
            print("  ❌ Quality gates failed — aborting deployment")
            return {"status": "failed", "reason": "quality_gates", "metrics": metrics}

        # ── Phase 4: Champion/Challenger ─────────────────────────────────────
        print("\n[Phase 4] Champion/Challenger Comparison")
        should_deploy, comparison = self.training.compare_with_champion(
            pipeline, X_test, y_test
        )
        print(f"  Comparison: {comparison}")
        print(f"  Decision: {'DEPLOY' if should_deploy else 'KEEP CHAMPION'}")

        if not should_deploy:
            return {"status": "kept_champion", "comparison": comparison}

        # ── Phase 5: Deploy ─────────────────────────────────────────────────
        print("\n[Phase 5] Deployment")
        version = self.training.save_model(pipeline, {"metrics": metrics})
        self.serving.deploy(pipeline, version)

        # ── Phase 6: Serve (simulation) ──────────────────────────────────────
        print("\n[Phase 6] Serving Simulation (100 predictions)")
        for i in range(100):
            feat = X_test.values[i % len(X_test)]
            self.serving.predict(feat)

        # ── Phase 7: Monitoring ─────────────────────────────────────────────
        print("\n[Phase 7] Monitoring")
        drift_detected = self.monitoring.check_confidence_drift()
        print(f"  Confidence drift: {'DETECTED ⚠️' if drift_detected else 'Normal ✅'}")

        # ── Audit Summary ────────────────────────────────────────────────────
        audit_log = self.bus.get_audit_log()
        event_counts = {}
        for event in audit_log:
            event_counts[event.event_type] = event_counts.get(event.event_type, 0) + 1

        print(f"\n{'─'*60}")
        print("PLATFORM AUDIT LOG SUMMARY")
        print(f"{'─'*60}")
        for event_type, count in sorted(event_counts.items()):
            print(f"  {event_type:<35} × {count}")
        print(f"  Total events: {len(audit_log)}")

        results = {
            "status":       "success",
            "version":      version,
            "metrics":      metrics,
            "comparisons":  comparison,
            "predictions":  self.serving.prediction_count,
            "audit_events": len(audit_log),
        }
        return results

    def generate_production_checklist(self):
        """Prints the complete production readiness checklist."""
        checklist = """
╔══════════════════════════════════════════════════════════════════╗
║         MLOPS PRODUCTION READINESS CHECKLIST                     ║
╚══════════════════════════════════════════════════════════════════╝

DATA LAYER
  □ Data versioned with DVC + remote storage (S3/GCS)
  □ Data validation runs on every pipeline execution
  □ Point-in-time correct features (no leakage)
  □ Feature store with offline + online stores

MODEL LAYER
  □ All experiments tracked in MLflow (params, metrics, artifacts)
  □ Model registry with staging/production/archived stages
  □ Hyperparameter optimization (not manual tuning)
  □ Champion/Challenger comparison before every deployment
  □ Rollback capability (< 5 minutes to previous version)

CI/CD LAYER
  □ Automated training pipeline (DVC pipeline or Airflow DAG)
  □ Unit tests + model tests with pytest
  □ Quality gates: min accuracy, regression test vs baseline
  □ Docker container for reproducible serving environment
  □ Staging environment with smoke tests before production

SERVING LAYER
  □ API with input validation (Pydantic)
  □ Health checks for Kubernetes liveness/readiness
  □ Prediction logging (every inference logged)
  □ Response caching for repeated requests
  □ Rate limiting and authentication

MONITORING LAYER
  □ Feature drift detection (KS test, PSI)
  □ Prediction distribution monitoring
  □ Performance metrics (latency P50/P95/P99)
  □ Business metrics (conversion, revenue per variant)
  □ Alerting: Slack/PagerDuty on threshold breaches

GOVERNANCE LAYER
  □ Complete audit log of all model versions deployed
  □ Model cards documenting bias, fairness, limitations
  □ Data lineage: know which data trained each model
  □ Compliance: data retention, PII handling, GDPR

PEOPLE / PROCESS
  □ On-call runbook for model incidents
  □ Defined SLA for model performance degradation response
  □ Regular model review cadence (monthly)
  □ A/B testing framework for new model evaluation
"""
        print(checklist)

    def generate_stack_comparison(self):
        """Shows how this platform maps to real cloud ML platforms."""
        print("""
REAL-WORLD MLOPS STACKS
═══════════════════════

Component         | This Project    | AWS                | GCP               | Azure
──────────────────|─────────────────|--------------------|-------------------|──────────────────
Experiment Track  | MLflow          | SageMaker Exp.     | Vertex Experiments| Azure ML Studio
Model Registry    | MLflow Registry | SageMaker Registry | Vertex Model Reg. | Azure ML Registry
Feature Store     | Custom          | SageMaker FS       | Vertex FS         | Azure Feature Store
Pipeline Orch.    | Airflow         | SageMaker Pipeline | Vertex Pipelines  | Azure ML Pipelines
Model Serving     | FastAPI         | SageMaker Endpoints| Vertex Endpoints  | Azure ML Endpoints
Monitoring        | Custom/Evidently| SageMaker Monitor  | Vertex Monitor    | Azure Monitor
HPO               | Optuna          | SageMaker HPO      | Vertex HP Tuning  | Azure HPO
CI/CD             | GitHub Actions  | CodePipeline       | Cloud Build       | Azure DevOps
Container Reg.    | Docker/GHCR     | ECR                | Artifact Registry | ACR
Data Versioning   | DVC             | SageMaker Data     | DVC on GCS        | DVC on Azure Blob

OPEN SOURCE ALTERNATIVES (fully self-hosted):
  Kubeflow    = full ML platform on Kubernetes
  MLflow      = experiment tracking + registry (we used this!)
  Feast       = feature store
  Evidently   = model monitoring
  Airflow     = pipeline orchestration
  Optuna      = hyperparameter optimization
  FastAPI     = model serving
  DVC         = data versioning
  ArgoCD      = GitOps deployment
""")


# =============================================================================
# MAIN
# =============================================================================
if __name__ == "__main__":
    print("PROJECT 10: Full MLOps Platform\n")

    platform = MLOpsPlatform()

    # Run the full lifecycle
    result = platform.run_full_lifecycle()
    print(f"\nFinal result: {json.dumps({k: v for k, v in result.items() if k != 'audit_events'}, indent=2)}")

    # Show production checklist
    platform.generate_production_checklist()

    # Show stack comparison
    platform.generate_stack_comparison()

    print("\n" + "="*60)
    print("✅ ALL 10 MLOPS PROJECTS COMPLETE!")
    print("="*60)
    print("""
You have now learned:
  P01 → Experiment Tracking (MLflow)
  P02 → Data Versioning (DVC)
  P03 → Model Registry (MLflow Registry + Lifecycle)
  P04 → Feature Store (Offline + Online stores)
  P05 → CI/CD for ML (GitHub Actions + Quality Gates)
  P06 → Model Serving (FastAPI + Caching + Streaming)
  P07 → Monitoring + Drift Detection (KS, PSI, CUSUM)
  P08 → Automated Retraining (Optuna HPO + Champion/Challenger)
  P09 → A/B Testing (Shadow mode, Bandit, Canary deploy)
  P10 → Full Platform (Event-driven, integrated lifecycle)

NEXT STEPS:
  1. Take one real project and implement it from scratch
  2. Set up a local Airflow instance and wire the DAG
  3. Deploy to Kubernetes with Helm charts
  4. Learn Kubeflow Pipelines for cloud-native MLOps
  5. Study the MLOps maturity model: https://ml-ops.org
""")
"""   
The patterns stay the same. The tools and scale change.

This Code's Implementation	Production-Ready Equivalent (2026)
pickle model serialization	ONNX, MLflow Model format, or BentoML (cross-framework, safer).
In-memory EventBus	Apache Kafka, NATS, or cloud-specific event services.
Local file artifacts	S3 / GCS / Azure Blob with proper versioning and lifecycle policies.
DataManager.check_drift() with KS test	Evidently AI, Alibi Detect, or cloud-native monitoring (SageMaker Model Monitor).
TrainingManager.train() manual loops	Optuna (already mentioned), Hyperopt, or Kubernetes Job orchestration.
ServingManager with in-memory model	KServe (Kubernetes), SageMaker Endpoints, or Vertex AI Prediction with auto-scaling.
compare_with_champion manual metric check	Statistical significance testing (bootstrap), Bayesian A/B testing frameworks.

"""