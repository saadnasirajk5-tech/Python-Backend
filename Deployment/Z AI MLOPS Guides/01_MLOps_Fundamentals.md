# MLOps Fundamentals — The Complete Guide

> "A model that's not in production is a research project. A model in production without monitoring is a liability."
> — Anonymous MLOps Engineer

---

## Table of Contents

1. [What is MLOps?](#1-what-is-mlops)
2. [Why MLOps Exists — The Problem It Solves](#2-why-mlops-exists--the-problem-it-solves)
3. [MLOps vs DevOps vs DataOps](#3-mlops-vs-devops-vs-dataops)
4. [The ML Lifecycle — End to End](#4-the-ml-lifecycle--end-to-end)
5. [MLOps Maturity Levels (Google's Model)](#5-mlops-maturity-levels-googles-model)
6. [Core Components of MLOps](#6-core-components-of-mlops)
7. [Model Versioning Deep Dive](#7-model-versioning-deep-dive)
8. [Data Versioning Deep Dive](#8-data-versioning-deep-dive)
9. [Experiment Tracking Deep Dive](#9-experiment-tracking-deep-dive)
10. [Feature Stores](#10-feature-stores)
11. [Model Registry](#11-model-registry)
12. [Model Serving Patterns](#12-model-serving-patterns)
13. [Model Monitoring & Observability](#13-model-monitoring--observability)
14. [MLOps Tooling Landscape](#14-mlops-tooling-landscape)
15. [Real-World MLOps Architecture](#15-real-world-mlops-architecture)
16. [Common Anti-Patterns](#16-common-anti-patterns)
17. [Hands-On: MLflow from Scratch](#17-hands-on-mlflow-from-scratch)
18. [Hands-On: DVC from Scratch](#18-hands-on-dvc-from-scratch)
19. [Summary & Next Steps](#19-summary--next-steps)

---

## 1. What is MLOps?

**MLOps (Machine Learning Operations)** is an engineering discipline that aims to unify ML systems development (Dev) and ML systems operations (Ops). Practicing MLOps means advocating for automation and monitoring at all steps of ML system construction, including integration, testing, releasing, deployment, and infrastructure management.

In plain English: **MLOps is to machine learning what DevOps is to traditional software engineering.** But it's harder, because ML has data, models, and drift that traditional software doesn't.

### The Three Pillars of MLOps

1. **Reproducibility** — Anyone, anywhere, at any time, can recreate a model with the exact same behavior.
2. **Automation** — Training, testing, deployment, monitoring happen without manual intervention.
3. **Monitoring** — Once a model is live, you know immediately when its performance degrades.

### Why is MLOps Different from DevOps?

| Aspect | DevOps | MLOps |
|--------|--------|-------|
| Inputs | Code | Code + Data + Hyperparameters |
| Outputs | Binary/App | Model + Code + Config |
| Testing | Unit/Integration/Functional | All of those + Data validation + Model quality + Bias/fairness |
| Deployment | Once per release | Continuously redeployed (model drift) |
| Monitoring | Uptime, latency, errors | All of those + Prediction distribution + Feature drift + Ground truth lag |
| Rollback | Previous version | Previous version + data snapshot + config |
| Performance decay | Rare | Guaranteed over time (drift) |

This table is **the most important table in this entire guide**. Read it three times. Every MLOps decision you make traces back to one of these differences.

---

## 2. Why MLOps Exists — The Problem It Solves

### The Tragic Statistics

- **87% of data science projects never make it to production** (Gartner, 2022).
- Of those that do, **most degrade silently** until someone notices the business is bleeding money.
- The average time from "model trained" to "model in production" in non-MLOps organizations is **3–9 months**. In mature MLOps orgs, it's **hours**.

### The Seven Pain Points MLOps Solves

1. **"It worked on my laptop."** — Notebooks don't translate to production. MLOps forces reproducibility.
2. **"Which model is in production right now?"** — Without a model registry, no one knows. MLOps enforces a single source of truth.
3. **"The model's accuracy dropped last week and no one noticed."** — Without monitoring, drift kills you silently. MLOps makes degradation visible.
4. **"We can't retrain because no one knows what data was used."** — Without data versioning, every model is a one-shot. MLOps makes datasets first-class artifacts.
5. **"The data scientist left, and we can't reproduce her model."** — Without experiment tracking, knowledge walks out the door. MLOps makes experiments queryable.
6. **"Deployment takes 2 weeks of engineering time."** — Without CI/CD, every model is a hand-crafted snowflake. MLOps makes deployment a button press.
7. **"Compliance wants to know why the model denied this loan."** — Without lineage tracking, you can't answer. MLOps makes auditability built-in.

If you've ever worked in a startup that "does ML," you've felt all seven of these. MLOps is the cure.

---

## 3. MLOps vs DevOps vs DataOps

These three are siblings, not synonyms. Confusing them is the #1 rookie mistake.

### DevOps
- **Subject:** Application code
- **Goal:** Ship reliable software fast
- **Key practice:** CI/CD for code
- **Tools:** Jenkins, GitHub Actions, GitLab CI, ArgoCD

### DataOps
- **Subject:** Data pipelines
- **Goal:** Deliver clean, fresh, reliable data
- **Key practice:** Pipeline orchestration, data quality tests
- **Tools:** Airflow, dbt, Prefect, Dagster, Great Expectations

### MLOps
- **Subject:** ML models + the systems around them
- **Goal:** Ship reliable ML fast, and keep it reliable as the world changes
- **Key practice:** Everything in DevOps + DataOps + experiment tracking + model registry + monitoring for drift
- **Tools:** MLflow, Kubeflow, DVC, Weights & Biases, Seldon, BentoML, Evidently

### The Venn Diagram You Should Memorize

```
        DevOps (code)
            |
       +----+----+
       |         |
   DataOps   MLOps
   (data)  (models)
```

MLOps is the **superset** in an ML organization: it inherits from DevOps (for the serving code) and from DataOps (for the training pipelines), and adds ML-specific concerns on top.

---

## 4. The ML Lifecycle — End to End

This is the canonical lifecycle you must memorize. Every interview question, every architecture diagram, every tool decision maps back to these stages.

### Stage 1: Business Problem Framing
- Translate "we want more revenue" into "we need a churn prediction model with 80%+ precision."
- Define **success metric** in business terms (revenue, retention, cost saved).
- Define **ML metric** that approximates it (F1, RMSE, etc.).
- Document constraints: latency budget, fairness requirements, explainability needs.

### Stage 2: Data Engineering
- Source data from warehouses, lakes, APIs, Kafka topics.
- Clean, deduplicate, validate.
- Engineer features (this is where most of the value is).
- Store in feature store for reuse across training + serving.

### Stage 3: Experimentation
- Train many models with many hyperparameter combos.
- Track everything: code commit, data version, hyperparams, metrics, artifacts.
- Use experiment tracking (MLflow, W&B) from day one — not as an afterthought.

### Stage 4: Validation
- Offline metrics (held-out test set).
- Fairness/bias audits across demographic slices.
- Robustness tests (adversarial inputs, distribution shift simulation).
- Latency/throughput benchmarks on representative hardware.

### Stage 5: Deployment
- Choose serving pattern (see Section 12).
- Canary, blue/green, shadow deployment.
- SLOs defined: p99 latency, error rate, model quality floor.

### Stage 6: Monitoring
- Operational metrics: latency, errors, traffic, CPU/GPU.
- ML metrics: input drift, output drift, prediction confidence.
- Business metrics: revenue, conversion, complaint rate.
- Ground truth feedback loop (when available) → retrain trigger.

### Stage 7: Retraining
- Triggered automatically by drift or scheduled (daily/weekly).
- Re-run the **same pipeline** that produced the original — no manual snowflakes.
- Validate the new model against the incumbent (champion/challenger).

### Stage 8: Retirement
- When a model is replaced, archive it (don't delete — for audit).
- Document why it was retired (drift, business change, fairness issue).

---

## 5. MLOps Maturity Levels (Google's Model)

Google published three maturity levels in their MLOps paper. **Memorize these.** Interviewers love this question.

### Level 0: Manual Process
- Notebook-driven development.
- Hand-coded training script.
- Manual export of model file.
- Engineering team manually integrates model into app.
- **No CI/CD, no monitoring, no automation.**
- 90% of "AI startups" are here. It's why they can't scale.

### Level 1: ML Pipeline Automation
- Training code is modularized and reproducible.
- Experiments are tracked.
- Data is versioned.
- Pipeline can be triggered automatically (e.g., on new data).
- Continuous Training (CT) is introduced.
- Deployment is still semi-manual but reproducible.

### Level 2: CI/CD Pipeline Automation
- Full CI/CD for both code and data.
- Any commit triggers tests → training → validation → staging → canary → prod.
- Multiple environments (dev/staging/prod) with promotion gates.
- Automated rollback on SLO breach.
- This is what Google, Meta, Netflix, Uber operate at.
- **This is where you want to be hired to build.**

---

## 6. Core Components of MLOps

Every mature MLOps system has these components. You should be able to name, explain, and pick a tool for each.

| Component | Purpose | Popular Tools |
|-----------|---------|---------------|
| Experiment Tracking | Log params, metrics, artifacts per run | MLflow, W&B, Comet, Neptune |
| Data Versioning | Version datasets like code | DVC, LakeFS, Pachyderm |
| Pipeline Orchestration | Schedule and execute multi-step pipelines | Airflow, Prefect, Dagster, Kubeflow Pipelines, Argo Workflows |
| Feature Store | Centralized feature definitions + serving | Feast, Tecton, Hopsworks, SageMaker Feature Store |
| Model Registry | Single source of truth for models | MLflow Model Registry, W&B Registry, Vertex AI Model Registry |
| Model Serving | Serve models behind an API | Seldon, BentoML, KServe, Triton, TorchServe, TF Serving |
| Model Monitoring | Detect drift, degradation | Evidently, Arize, Fiddler, WhyLabs, Prometheus + Grafana |
| CI/CD | Automate test/train/deploy | GitHub Actions, GitLab CI, Jenkins, CircleCI |
| Compute | Run training jobs | Kubernetes, Ray, SageMaker, Vertex AI, Databricks |
| Metadata Store | Queryable history of everything | MLflow, ML Metadata, Kubeflow Metadata |

---

## 7. Model Versioning Deep Dive

### What is a Model Version?

A model version is **not** just a `.pkl` file. A proper model version includes:

1. **The model artifact** (weights, architecture)
2. **The code** that trained it (git commit hash)
3. **The data** it was trained on (dataset version hash)
4. **The hyperparameters** (lr, batch size, etc.)
5. **The metrics** it achieved (accuracy, F1, latency)
6. **The environment** (Python version, library versions, CUDA version)
7. **The config** (feature list, preprocessing steps)

If any of these 7 things is missing, **you don't have a versioned model — you have a file.**

### Versioning Strategies

**Semantic versioning (SemVer) for models:**
- `MAJOR.MINOR.PATCH`
- MAJOR: trained on different data or different architecture (breaking change)
- MINOR: retrained on more data, same architecture (backward compatible)
- PATCH: hyperparameter tweak, same data + architecture

**CalVer for models:**
- `YYYY.MM.DD-RUNNUMBER`
- E.g., `2024.03.15-42`
- Pros: chronological, easy to know "when"
- Cons: doesn't convey compatibility

**Hybrid (recommended):**
- `churn-v2-2024.03.15-42` — model name + major version + date + run number

### MLflow Model Versioning in Practice

```python
import mlflow
import mlflow.sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split

# Set the tracking URI (where experiments live)
mlflow.set_tracking_uri("sqlite:///mlflow.db")
mlflow.set_experiment("churn-prediction")

# Start a run
with mlflow.start_run(run_name="rf-v2-baseline") as run:
    # Load + split data
    X, y = load_iris(return_X_y=True)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Hyperparameters (logged as params)
    params = {"n_estimators": 100, "max_depth": 5, "random_state": 42}
    mlflow.log_params(params)

    # Train
    model = RandomForestClassifier(**params)
    model.fit(X_train, y_train)

    # Evaluate
    accuracy = model.score(X_test, y_test)
    mlflow.log_metric("accuracy", accuracy)

    # Log the model with signature (input/output schema)
    from mlflow.models import infer_signature
    signature = infer_signature(X_train, model.predict(X_train))
    mlflow.sklearn.log_model(
        model,
        artifact_path="model",
        signature=signature,
        registered_model_name="churn-prediction"
    )

    print(f"Run ID: {run.info.run_id}")
    print(f"Accuracy: {accuracy:.4f}")
```

This single snippet demonstrates **everything** a real experiment tracking session should capture. Note the `signature` — this is critical for serving later, because it tells the serving framework what shape of input to expect.

---

## 8. Data Versioning Deep Dive

### Why Git Alone Doesn't Work for Data

Git is designed for **text files** that change a few KB at a time. ML datasets are:
- Often **GB or TB** in size
- **Binary** (images, audio, parquet)
- Updated **frequently** (new rows appended daily)

Git LFS helps but caps out around a few GB. Beyond that, you need purpose-built tooling.

### DVC (Data Version Control) — The De Facto Standard

DVC's mental model:
- Git tracks the **pointer** to the data (small text file with hash + remote URL).
- DVC tracks the **actual data** (stored in S3/GCS/Azure/local NAS).
- `git checkout` + `dvc checkout` together = restore the exact data state for that commit.

### DVC Walkthrough

```bash
# Initialize DVC in your repo
git init
dvc init
git commit -m "Initialize DVC"

# Configure remote storage (S3 in this example)
dvc remote add -d storage s3://my-bucket/dvc-storage
git commit -m "Configure DVC remote"

# Add a dataset — DVC creates a .dvc pointer file (commit THIS to git)
dvc add data/raw/customers.csv
git add data/raw/customers.csv.dvc .gitignore
git commit -m "Add customers.csv v1"

# Now imagine new data arrives — replace the file, re-add
dvc add data/raw/customers.csv
git commit -am "Update customers.csv with March data"

# To restore the March version later:
git checkout <march-commit>
dvc checkout
# data/raw/customers.csv is now the March version

# Push data to remote
dvc push

# Pull data from remote (e.g., on a fresh machine)
dvc pull
```

### DVC Pipeline (Reproducible Training)

DVC also lets you define **pipelines** in `dvc.yaml` — this is where it becomes truly powerful for MLOps.

```yaml
# dvc.yaml
stages:
  prepare:
    cmd: python src/prepare.py --raw data/raw/customers.csv --out data/processed
    deps:
      - src/prepare.py
      - data/raw/customers.csv
    outs:
      - data/processed/train.csv
      - data/processed/test.csv

  train:
    cmd: python src/train.py --train data/processed/train.csv --out models/model.pkl
    deps:
      - src/train.py
      - data/processed/train.csv
    outs:
      - models/model.pkl

  evaluate:
    cmd: python src/evaluate.py --model models/model.pkl --test data/processed/test.csv --out metrics/eval.json
    deps:
      - src/evaluate.py
      - models/model.pkl
      - data/processed/test.csv
    metrics:
      - metrics/eval.json
```

```bash
dvc repro        # runs all stages whose deps changed
dvc repro -f     # force re-run everything
dvc dag           # visualize the pipeline
```

Now your **entire pipeline is reproducible** with one command. This is Level 1 MLOps.

---

## 9. Experiment Tracking Deep Dive

### What Should You Track?

**Always:**
- Git commit hash
- Python environment (use `pip freeze > requirements.txt` or `conda env export`)
- Random seeds
- Hyperparameters
- Training metrics (per epoch/step)
- Final metrics
- Model artifact
- Input data version (DVC hash)

**Strongly recommended:**
- System metrics (CPU/GPU/memory over time)
- Training logs
- Sample predictions (for visual inspection)
- Feature importance
- Confusion matrix / residual plots

### MLflow Tracking API — Full Example

```python
import mlflow
import mlflow.xgboost
import xgboost as xgb
from sklearn.datasets import fetch_california_housing
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import numpy as np
import pandas as pd

# Enable autologging — captures everything XGBoost does automatically
mlflow.xgboost.autolog()

mlflow.set_tracking_uri("sqlite:///mlflow.db")
mlflow.set_experiment("california-housing")

data = fetch_california_housing(as_frame=True)
X_train, X_test, y_train, y_test = train_test_split(
    data.data, data.target, test_size=0.2, random_state=42
)

dtrain = xgb.DMatrix(X_train, label=y_train)
dtest = xgb.DMatrix(X_test, label=y_test)

params = {
    "max_depth": 6,
    "eta": 0.1,
    "objective": "reg:squarederror",
    "eval_metric": "rmse",
    "seed": 42,
}

with mlflow.start_run(run_name="xgb-baseline-v1") as run:
    # Manual param logging (autolog handles this too, but explicit is clearer)
    mlflow.log_params(params)

    # Train
    model = xgb.train(
        params,
        dtrain,
        num_boost_round=200,
        evals=[(dtrain, "train"), (dtest, "eval")],
        early_stopping_rounds=10,
        verbose_eval=20,
    )

    # Predict + metrics
    preds = model.predict(dtest)
    rmse = np.sqrt(mean_squared_error(y_test, preds))
    r2 = r2_score(y_test, preds)
    mlflow.log_metrics({"test_rmse": rmse, "test_r2": r2})

    # Log an artifact (a confusion matrix image, a feature importance plot, etc.)
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots()
    xgb.plot_importance(model, ax=ax, max_num_features=10)
    plt.savefig("feature_importance.png")
    mlflow.log_artifact("feature_importance.png")

    # Register the model
    mlflow.xgboost.log_model(
        model,
        artifact_path="model",
        registered_model_name="california-housing-regressor"
    )

print(f"Done. Run ID: {run.info.run_id}")
```

### MLflow UI

Run `mlflow ui` and open `http://localhost:5000`. You'll see:
- All experiments and runs
- Side-by-side metric comparison
- Parameter diffing
- Artifact browser
- Model registry

**Spend 30 minutes clicking through the UI after running the above code.** This is the fastest way to internalize what tracking gives you.

---

## 10. Feature Stores

### The Problem

Two big problems in ML engineering:

1. **Training/serving skew:** The features used to train are computed slightly differently than the features used at inference. Model performance drops.
2. **Feature duplication:** Two teams build the same "user_age" feature independently, with different bugs.

### The Solution: Feature Store

A feature store is a centralized system that:
- Defines features **once** as code
- Computes them for **both** training (batch) and serving (online, low-latency)
- Stores them with versioning
- Makes them discoverable across teams

### Feast — Open-Source Feature Store Walkthrough

```python
# feature_repo/example_repo.py
from feast import Entity, FeatureView, Field, FileSource, ValueType
from feast.types import Float32, Int64
from datetime import timedelta

# Define the entity (the "primary key" of your features)
customer = Entity(
    name="customer_id",
    join_keys=["customer_id"],
)

# Define the source — a parquet file
customer_stats_source = FileSource(
    name="customer_stats_source",
    path="data/features/customer_stats.parquet",
    timestamp_field="event_ts",
)

# Define a FeatureView — a group of features for an entity
customer_fv = FeatureView(
    name="customer_stats",
    entities=["customer_id"],
    ttl=timedelta(days=365),
    schema=[
        Field(name="age", dtype=Int64),
        Field(name="tenure_months", dtype=Int64),
        Field(name="monthly_spend", dtype=Float32),
        Field(name="churn_risk_score", dtype=Float32),
    ],
    source=customer_stats_source,
    online=True,
)
```

```python
# Use it for training (offline — batch read)
from feast import FeatureStore
import pandas as pd

store = FeatureStore(repo_path="feature_repo")

entity_df = pd.DataFrame({
    "customer_id": [1, 2, 3, 4, 5],
    "event_ts": pd.to_datetime(["2024-03-01"] * 5),
})

training_features = store.get_historical_features(
    entity_df=entity_df,
    features=[
        "customer_stats:age",
        "customer_stats:tenure_months",
        "customer_stats:monthly_spend",
        "customer_stats:churn_risk_score",
    ]
).to_df()

# Use it for serving (online — low-latency single-row read)
online_features = store.get_online_features(
    features=[
        "customer_stats:age",
        "customer_stats:monthly_spend",
    ],
    entity_rows=[{"customer_id": 1}],
).to_dict()
```

The **same feature definitions** power both. No skew. This is the killer value prop of feature stores.

---

## 11. Model Registry

### What It Is

A model registry is a **centralized, versioned, auditable catalog** of all ML models in an organization. It tracks:
- Model versions (v1, v2, v3...)
- Model stage (None → Staging → Production → Archived)
- Model metadata (who trained it, when, with what data, what metrics)
- Lineage (which experiment run produced it)
- Approvals (who promoted it to Production)

### MLflow Model Registry Workflow

```python
import mlflow

client = mlflow.tracking.MlflowClient()

# Create a registered model (one-time)
client.create_registered_model("churn-prediction")

# After training + logging a model (see Section 9), you get a run_id.
# Now create a version of the registered model from that run:
result = client.create_model_version(
    name="churn-prediction",
    source=f"mlruns/0/{run_id}/artifacts/model",
    run_id=run_id,
)
# result.version is the new version number (1, 2, 3...)

# Transition stages
client.transition_model_version_stage(
    name="churn-prediction",
    version=1,
    stage="Staging",
)

# After Staging validation:
client.transition_model_version_stage(
    name="churn-prediction",
    version=1,
    stage="Production",
    archive_existing_versions=True,  # auto-archive previous Production
)

# List all versions
for mv in client.search_model_versions("name='churn-prediction'"):
    print(f"v{mv.version}: {mv.current_stage}")

# Load the Production version for serving
import mlflow.sklearn
production_model = mlflow.sklearn.load_model(
    model_uri="models:/churn-prediction/Production"
)
```

### Why This Matters

Without a registry:
- "Which model is in prod?" — Slack channel / spreadsheet /shrug
- Audit: impossible
- Rollback: depends on whoever deployed last

With a registry:
- One SQL-like query to find current prod model
- Full audit trail for compliance
- Rollback = `transition_model_version_stage(..., version=N-1, stage="Production")`

---

## 12. Model Serving Patterns

There are **six canonical serving patterns**. Know them all.

### Pattern 1: Batch Inference
- Run predictions on a schedule (hourly/daily) for many rows.
- Write predictions to a database.
- App reads from DB, never calls the model.
- **Use case:** Churn scoring, recommendation pre-compute, fraud risk scoring overnight.
- **Tools:** Spark + MLlib, Airflow + sklearn, SageMaker Batch Transform.

### Pattern 2: Real-Time (Synchronous) Inference
- Client sends HTTP/gRPC request → gets prediction back immediately.
- Latency budget: typically 50–500ms.
- **Use case:** Credit card fraud check at checkout, content moderation.
- **Tools:** FastAPI + model, BentoML, Seldon, KServe, SageMaker Endpoints.

### Pattern 3: Asynchronous Inference
- Client submits job → gets a job ID → polls for result.
- For long-running models (LLM generation, batch scoring within an app).
- **Use case:** Large LLM completions, video processing, document OCR.
- **Tools:** Celery + Redis, AWS SQS + Lambda, KServe Async.

### Pattern 4: Streaming Inference
- Predictions triggered by events on a stream (Kafka/Kinesis).
- Results written back to a stream.
- **Use case:** Real-time anomaly detection on logs, IoT sensor alerts.
- **Tools:** Kafka + Faust/Quix, Flink + ML library, Spark Streaming.

### Pattern 5: Edge Inference
- Model runs on device (phone, IoT, browser).
- No network round-trip, privacy-preserving.
- **Use case:** Mobile photo classification, on-device voice wake word.
- **Tools:** TensorFlow Lite, ONNX Runtime Mobile, CoreML, WebGPU.

### Pattern 6: Multi-Model Serving
- One server hosts multiple models, shares GPU.
- Critical when you have 100s of models but limited GPUs.
- **Tools:** NVIDIA Triton, KServe Multi-Model Serving, Seldon MLServer.

### How to Choose

| Need | Pattern |
|------|---------|
| Latency < 100ms, per-request | Real-time |
| Latency OK in hours | Batch |
| Latency OK in minutes, model is slow | Async |
| Event-driven | Streaming |
| No network | Edge |
| 50+ models on 1 GPU | Multi-model |

---

## 13. Model Monitoring & Observability

### The Two Categories of Monitoring

**Operational monitoring** (same as any service):
- Latency (p50, p95, p99)
- Throughput (QPS)
- Error rate (4xx, 5xx)
- CPU/GPU/memory utilization
- Tooling: Prometheus + Grafana, Datadog

**ML monitoring** (specific to ML):
- **Input drift:** Distribution of features changes (e.g., age mean shifted from 35 to 42).
- **Output drift:** Distribution of predictions changes (e.g., model now predicts "churn" 30% more often).
- **Concept drift:** The relationship between X and y changes (retraining needed).
- **Data quality:** Missing values, schema violations.
- **Prediction quality:** When ground truth arrives, compare to prediction.
- **Tooling:** Evidently, Arize, Fiddler, WhyLabs.

### Evidently — Open-Source Drift Detection Walkthrough

```python
import pandas as pd
from sklearn.datasets import load_iris
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset, TargetDriftPreset

# Reference data (what the model was trained on)
# Current data (what it's seeing now in prod)
reference = pd.read_csv("data/reference.csv")
current = pd.read_csv("data/current.csv")

# Drift report
report = Report(metrics=[DataDriftPreset()])
report.run(reference_data=reference, current_data=current)
report.save_html("drift_report.html")

# Programmatically check if drift occurred
result = report.as_dict()
drift_detected = result["metrics"][0]["result"]["dataset_drift"]
if drift_detected:
    # Trigger retraining pipeline
    print("DRIFT DETECTED — triggering retraining...")
```

### What to Monitor at Each Stage

| Stage | What to Monitor |
|-------|-----------------|
| Request intake | Schema, types, missing fields |
| Preprocessing | Feature stats (mean, std, null rate) |
| Model input | Feature distribution vs training |
| Model output | Prediction distribution, confidence |
| Post-processing | Business rules applied correctly |
| Ground truth loop (later) | Actual outcome vs prediction |

### SLOs for ML Models

Define these **before** going to prod:
- **Availability:** 99.9% of requests succeed
- **Latency p99:** < 200ms
- **Throughput:** 1000 QPS sustained
- **Freshness:** Model retrained at most every 7 days
- **Quality floor:** F1 never drops below 0.75 on labeled feedback

When an SLO is violated → page the on-call → trigger rollback or retraining.

---

## 14. MLOps Tooling Landscape

This is the tool map you need in your head. Don't try to learn all of them — pick one per category and go deep.

### End-to-End Platforms (managed)
- **AWS SageMaker** — full stack, expensive, lock-in
- **GCP Vertex AI** — full stack, excellent AutoML
- **Azure ML** — full stack, strong on enterprise
- **Databricks** — Spark + MLflow unified, great for big data
- **Weights & Biases** — best experiment tracking UI, expensive at scale

### Self-Hosted Stack (the "modern startup" stack)
- Experiment tracking: **MLflow** (open source, free)
- Data versioning: **DVC** (open source, free)
- Pipeline orchestration: **Prefect** or **Airflow** (open source)
- Feature store: **Feast** (open source)
- Model serving: **BentoML** or **Seldon** (open source)
- Monitoring: **Evidently** + **Prometheus/Grafana**
- CI/CD: **GitHub Actions** (free for public repos)
- Compute: **Kubernetes** on EKS/GKE/AKS

### The "Resume Stack" — what most companies actually hire for
1. Python + SQL
2. Docker + Kubernetes (basics)
3. MLflow
4. FastAPI
5. GitHub Actions / GitLab CI
6. AWS (SageMaker, EKS, S3) OR GCP (Vertex AI, GKE, GCS)
7. Terraform (infrastructure as code)

If you can demonstrate competence in all 7, you can land a $120k+ MLOps role in 2024.

---

## 15. Real-World MLOps Architecture

Here's what a mature startup's MLOps stack actually looks like:

```
┌─────────────────────────────────────────────────────────────────┐
│                     DATA SOURCES                                │
│  Postgres  │  Kafka  │  S3 logs  │  Stripe API  │  Segment CDP  │
└──────┬──────────┬──────────┬──────────┬──────────┬──────────────┘
       │          │          │          │          │
       ▼          ▼          ▼          ▼          ▼
┌─────────────────────────────────────────────────────────────────┐
│              INGESTION (Airflow / Fivetran)                     │
└──────────────────────┬──────────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│       DATA WAREHOUSE (Snowflake / BigQuery / Redshift)          │
└──────────────────────┬──────────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│  FEATURE ENGINEERING (dbt + Feast)                              │
│  - Feature definitions versioned in git                         │
│  - Offline store: Snowflake                                     │
│  - Online store: Redis                                          │
└──────┬──────────────────────────────────────┬───────────────────┘
       │                                       │
       ▼                                       ▼
┌──────────────────────────┐         ┌───────────────────────────┐
│  TRAINING PIPELINE        │         │   FEATURE SERVING         │
│  (Prefect + DVC)         │         │   (Feast online API)      │
│                           │         └────────────┬──────────────┘
│  - Triggered daily or on  │                      │
│    drift                  │                      │
│  - Logs to MLflow         │                      │
│  - Pushes model to        │                      │
│    registry                │                      │
└──────────┬────────────────┘                      │
           ▼                                       │
┌──────────────────────────┐                       │
│  MODEL REGISTRY           │                       │
│  (MLflow Model Registry) │                       │
│                           │                       │
│  Staging → Production     │                       │
└──────────┬────────────────┘                       │
           ▼                                       ▼
┌─────────────────────────────────────────────────────────────────┐
│        SERVING (BentoML on Kubernetes + KServe)                 │
│  - Pulls Production model from registry                         │
│  - Pulls features from Feast online store                       │
│  - Exposes REST + gRPC endpoints                                │
│  - 3 replicas, autoscaling on QPS                              │
└──────┬───────────────────────────────────────────┬─────────────┘
       │                                           │
       ▼                                           ▼
┌────────────────────────────┐         ┌──────────────────────────┐
│  CLIENT (web/mobile/SDK)    │         │  MONITORING               │
│                             │         │  - Prometheus (ops)        │
└─────────────────────────────┘         │  - Evidently (drift)       │
                                        │  - Arize (predictions)     │
                                        │  - Alert on SLO breach     │
                                        └────────────┬──────────────┘
                                                     │
                                                     ▼
                                        ┌──────────────────────────┐
                                        │  RETRAINING TRIGGER       │
                                        │  - Drift detected?        │
                                        │  - Quality < floor?       │
                                        │  → Trigger pipeline above │
                                        └──────────────────────────┘
```

Print this. Stare at it. Every project in the **10 Projects file** builds you toward this architecture.

---

## 16. Common Anti-Patterns

Avoid these or be doomed to repeat them.

### Anti-Pattern 1: "Notebook is Production"
Jupyter notebooks are for exploration. They are **not** reproducible (execution order matters, hidden state, no version control of outputs). Convert to a Python module before going to prod.

### Anti-Pattern 2: "Hardcoded Paths and Magic Numbers"
```python
# BAD
df = pd.read_csv("/Users/bob/data/customers_v3_final_FINAL.csv")
model = XGBClassifier(learning_rate=0.0123)  # why 0.0123? no one knows

# GOOD
DATA_PATH = config["data_path"]  # from YAML/env
params = load_params("params.yaml")  # versioned in git
df = pd.read_csv(DATA_PATH)
model = XGBClassifier(**params)
```

### Anti-Pattern 3: "Training-Serving Skew"
Train preprocessing in Python, serve in Node.js, get different results. **Always** use the same preprocessing code in train and serve, or store engineered features in a feature store.

### Anti-Pattern 4: "The Hero Model"
One engineer built it, no one else understands it, it breaks when she's on vacation. Force code review, documentation, runbooks for every model.

### Anti-Pattern 5: "No Shadow Mode"
Promoting a model straight to prod without a shadow period is reckless. Always run new model in shadow (predict, don't act) for at least 1 week, compare to incumbent.

### Anti-Pattern 6: "Monitoring = Uptime"
An ML service with 100% uptime can still be 100% wrong. Operational monitoring is necessary but not sufficient — you need ML monitoring.

### Anti-Pattern 7: "Manual Retraining"
"Bob retrainings the model every Monday" is not MLOps — it's a single point of failure. Automate, schedule, alert on failure.

### Anti-Pattern 8: "No A/B Testing"
You deployed v2. Is it better than v1? "We think so" is not an answer. Always A/B test in prod before full cutover.

### Anti-Pattern 9: "Selling Models, Not Predictions"
Clients don't care about your model file. They care about the API that returns predictions. Design the API first, the model second.

### Anti-Pattern 10: "Ignoring Cost"
GPU inference is expensive. A naive deployment can burn $10k/month serving a model that gets 100 requests/day. Profile, optimize, autoscale.

---

## 17. Hands-On: MLflow from Scratch

Let's build a **complete, runnable** MLflow setup. By the end you'll have a local MLflow server with experiments, models, and a model registry.

### Step 1: Install
```bash
pip install mlflow scikit-learn pandas numpy matplotlib
```

### Step 2: Start the MLflow Server (in a separate terminal)
```bash
mkdir -p ~/mlflow_storage
mlflow server \
    --backend-store-uri sqlite:///~/mlflow_storage/mlflow.db \
    --default-artifact-root ~/mlflow_storage/artifacts \
    --host 0.0.0.0 \
    --port 5000
```
Open `http://localhost:5000` — that's your MLflow UI.

### Step 3: Train and Track a Model

Save this as `train.py`:

```python
import mlflow
import mlflow.sklearn
import pandas as pd
import numpy as np
from sklearn.datasets import load_wine
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from mlflow.models import infer_signature

# Connect to the MLflow server
mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("wine-classification")

# Load data
data = load_wine(as_frame=True)
X, y = data.data, data.target
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# Hyperparameter grid
param_grid = {
    "n_estimators": [50, 100, 200],
    "max_depth": [3, 5, 10, None],
    "min_samples_split": [2, 5],
}

best_f1 = 0
best_run_id = None

for n_est in param_grid["n_estimators"]:
    for max_d in param_grid["max_depth"]:
        for mss in param_grid["min_samples_split"]:
            with mlflow.start_run(run_name=f"rf-{n_est}-{max_d}-{mss}") as run:
                params = {
                    "n_estimators": n_est,
                    "max_depth": max_d,
                    "min_samples_split": mss,
                    "random_state": 42,
                }
                mlflow.log_params(params)

                model = RandomForestClassifier(**params)
                model.fit(X_train, y_train)
                preds = model.predict(X_test)

                acc = accuracy_score(y_test, preds)
                prec = precision_score(y_test, preds, average="weighted")
                rec = recall_score(y_test, preds, average="weighted")
                f1 = f1_score(y_test, preds, average="weighted")

                mlflow.log_metrics({
                    "accuracy": acc,
                    "precision": prec,
                    "recall": rec,
                    "f1": f1,
                })

                signature = infer_signature(X_train, model.predict(X_train))
                mlflow.sklearn.log_model(
                    model,
                    artifact_path="model",
                    signature=signature,
                    registered_model_name="wine-classifier"
                )

                if f1 > best_f1:
                    best_f1 = f1
                    best_run_id = run.info.run_id

                print(f"n_est={n_est} max_d={max_d} mss={mss} → f1={f1:.4f}")

print(f"\nBest F1: {best_f1:.4f}, Run ID: {best_run_id}")
```

### Step 4: Run It
```bash
python train.py
```

You should see ~24 runs in MLflow UI, each with different params and metrics. Click the "Compare" button to see them side-by-side.

### Step 5: Serve the Best Model

MLflow can deploy a model as a local REST API in one command:

```bash
mlflow models serve \
    -m "models:/wine-classifier/Production" \
    --port 5001 \
    --host 0.0.0.0
```

### Step 6: Call the Model

```bash
curl -X POST http://localhost:5001/invocations \
    -H "Content-Type: application/json" \
    -d '{
        "dataframe_split": {
            "columns": ["alcohol", "malic_acid", "ash", "alcalinity_of_ash", "magnesium", "total_phenols", "flavanoids", "nonflavanoid_phenols", "proanthocyanins", "color_intensity", "hue", "od280_od315_of_diluted_wines", "proline"],
            "data": [[14.23, 1.71, 2.43, 15.6, 127, 2.8, 3.06, 0.28, 2.29, 5.64, 1.04, 3.92, 1065]]
        }
    }'
```

**You now have a model in production.** This is the foundation — the rest of MLOps is making this process automatic, monitored, and scalable.

---

## 18. Hands-On: DVC from Scratch

### Step 1: Setup
```bash
pip install dvc
mkdir dvc-demo && cd dvc-demo
git init
dvc init
git commit -m "Initialize DVC"
```

### Step 2: Create Sample Data and Pipeline
```bash
mkdir -p data/raw data/processed models metrics src
```

`src/prepare.py`:
```python
import argparse
import pandas as pd
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
import os

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="data/processed")
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)
    data = load_iris(as_frame=True)
    df = data.data
    df["target"] = data.target

    train, test = train_test_split(df, test_size=0.2, random_state=42, stratify=df["target"])
    train.to_csv(os.path.join(args.out, "train.csv"), index=False)
    test.to_csv(os.path.join(args.out, "test.csv"), index=False)
    print(f"Wrote {len(train)} train rows, {len(test)} test rows")

if __name__ == "__main__":
    main()
```

`src/train.py`:
```python
import argparse
import pandas as pd
import pickle
from sklearn.ensemble import RandomForestClassifier
import os

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", default="data/processed/train.csv")
    parser.add_argument("--out", default="models/model.pkl")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    df = pd.read_csv(args.train)
    X, y = df.drop(columns=["target"]), df["target"]

    model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
    model.fit(X, y)

    with open(args.out, "wb") as f:
        pickle.dump(model, f)
    print(f"Saved model to {args.out}")

if __name__ == "__main__":
    main()
```

`src/evaluate.py`:
```python
import argparse
import pandas as pd
import pickle
import json
from sklearn.metrics import accuracy_score, f1_score

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="models/model.pkl")
    parser.add_argument("--test", default="data/processed/test.csv")
    parser.add_argument("--out", default="metrics/eval.json")
    args = parser.parse_args()

    with open(args.model, "rb") as f:
        model = pickle.load(f)

    df = pd.read_csv(args.test)
    X, y = df.drop(columns=["target"]), df["target"]
    preds = model.predict(X)

    metrics = {
        "accuracy": accuracy_score(y, preds),
        "f1_macro": f1_score(y, preds, average="macro"),
    }
    with open(args.out, "w") as f:
        json.dump(metrics, f, indent=2)
    print(json.dumps(metrics, indent=2))

if __name__ == "__main__":
    main()
```

### Step 3: Define the Pipeline (`dvc.yaml`)

```yaml
stages:
  prepare:
    cmd: python src/prepare.py --out data/processed
    deps:
      - src/prepare.py
    outs:
      - data/processed/train.csv
      - data/processed/test.csv

  train:
    cmd: python src/train.py --train data/processed/train.csv --out models/model.pkl
    deps:
      - src/train.py
      - data/processed/train.csv
    outs:
      - models/model.pkl

  evaluate:
    cmd: python src/evaluate.py --model models/model.pkl --test data/processed/test.csv --out metrics/eval.json
    deps:
      - src/evaluate.py
      - models/model.pkl
      - data/processed/test.csv
    metrics:
      - metrics/eval.json
```

### Step 4: Run the Pipeline
```bash
dvc repro
```

You should see DVC execute prepare → train → evaluate in order.

### Step 5: View Results
```bash
dvc metrics show
# accuracy, f1_macro
cat metrics/eval.json
```

### Step 6: Visualize the DAG
```bash
dvc dag
```

### Step 7: Modify and Re-run
Edit `src/train.py` to change `n_estimators` to 200. Then:
```bash
dvc repro
# Only the train and evaluate stages re-run (prepare is unaffected)
```

### Step 8: Configure Remote Storage
```bash
# Local remote (for demo)
mkdir -p /tmp/dvc-storage
dvc remote add -d storage /tmp/dvc-storage
git commit -am "Add DVC remote"

# Push artifacts
dvc push

# Simulate a fresh machine
rm -rf .dvc/cache data/processed models
dvc pull  # restores everything from remote
```

**You now have a fully reproducible ML pipeline.** Any teammate can clone the repo, run `dvc repro`, and get the same model with the same metrics.

---

## 19. Summary & Next Steps

### What You Learned in This File

1. MLOps is **DevOps + DataOps + ML-specific concerns** (drift, registry, monitoring).
2. The ML lifecycle has 8 stages — know each one cold.
3. MLOps has 3 maturity levels — aim for Level 2.
4. The 10 core components: experiment tracking, data versioning, orchestration, feature store, registry, serving, monitoring, CI/CD, compute, metadata.
5. Model versioning is more than a file — it's 7 things bundled together.
6. DVC gives you data versioning + reproducible pipelines.
7. MLflow gives you experiment tracking + model registry + serving.
8. There are 6 serving patterns — choose based on latency/throughput needs.
9. ML monitoring is different from ops monitoring — drift, concept drift, quality.
10. There are 10 common anti-patterns — avoid them or pay the price.

### What's Next

- Read **02_CI_CD_for_ML.md** — how to automate everything you just learned.
- Read **03_AI_API_Development_FastAPI.md** — how to wrap models in production APIs.
- Read **04_Docker_Kubernetes_for_ML.md** — how to deploy at scale.
- Read **05_10_Projects_Beginner_to_Pro.md** — apply everything in 10 graded projects.

### How to Actually Master This

Don't just read. **Build every example.** Type the code yourself (don't copy-paste). Break it on purpose and fix it. When you finish all 10 projects, you'll be hireable. No exaggeration.

---

**End of File 1. Continue to 02_CI_CD_for_ML.md.**
