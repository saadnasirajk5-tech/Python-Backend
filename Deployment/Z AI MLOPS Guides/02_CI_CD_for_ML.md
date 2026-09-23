# CI/CD for ML — The Complete Guide

> "In traditional software, CI/CD tests if your code works. In ML, CI/CD tests if your code works, if your data is sane, if your model still performs, and if your model is fair — all before it ever touches a user."

---

## Table of Contents

1. [CI/CD Fundamentals Refresher](#1-cicd-fundamentals-refresher)
2. [Why ML CI/CD is Different](#2-why-ml-cicd-is-different)
3. [The 4 Pipeline Types in ML](#3-the-4-pipeline-types-in-ml)
4. [Continuous Integration (CI) for ML](#4-continuous-integration-ci-for-ml)
5. [Continuous Delivery (CD) for ML](#5-continuous-delivery-cd-for-ml)
6. [Continuous Training (CT) — ML-Specific](#6-continuous-training-ct--ml-specific)
7. [Continuous Monitoring (CM)](#7-continuous-monitoring-cm)
8. [GitHub Actions for ML — Deep Dive](#8-github-actions-for-ml--deep-dive)
9. [GitLab CI for ML](#9-gitlab-ci-for-ml)
10. [Jenkins for ML](#10-jenkins-for-ml)
11. [Testing ML Systems — The 5 Layers](#11-testing-ml-systems--the-5-layers)
12. [Model Promotion Strategies](#12-model-promotion-strategies)
13. [Blue/Green, Canary, Shadow Deployments](#13-bluegreen-canary-shadow-deployments)
14. [Rollback Strategies for ML](#14-rollback-strategies-for-ml)
15. [End-to-End Real-World CI/CD Pipeline](#15-end-to-end-real-world-cicd-pipeline)
16. [Security & Compliance in ML Pipelines](#16-security--compliance-in-ml-pipelines)
17. [Cost Optimization in CI/CD](#17-cost-optimization-in-cicd)
18. [Common Failures and How to Prevent Them](#18-common-failures-and-how-to-prevent-them)
19. [Summary & Next Steps](#19-summary--next-steps)

---

## 1. CI/CD Fundamentals Refresher

Before ML, let's nail down vanilla CI/CD. If this section feels basic, skip ahead — but most "ML engineers" I've interviewed can't actually explain CI vs CD, so let's be thorough.

### Continuous Integration (CI)
Every code change is **automatically built and tested** before merge. Goal: catch bugs at commit time, not at deploy time.

Flow:
```
Developer commits → CI server builds → runs tests → reports pass/fail → if pass, allow merge
```

### Continuous Delivery (CD)
Every successful CI build is **automatically deployable** to production with a single click (or command). The deployment is **always ready**, even if you don't always deploy.

### Continuous Deployment (also CD)
Every successful CI build is **automatically deployed** to production, no human approval. Higher risk, higher velocity. Companies like Netflix/Facebook do this.

### Continuous Training (CT) — ML-specific
ML pipelines automatically **retrain** models when new data arrives, when drift is detected, or on a schedule. This is what makes ML CI/CD fundamentally different from traditional CI/CD.

### The CI/CD/CT Triangle for ML

```
            Code commit
                │
                ▼
       ┌────────────────┐
       │   CI for code  │  ← unit tests, lint, type check
       └───────┬────────┘
               │ pass
               ▼
       ┌────────────────┐
       │   CI for data  │  ← schema, quality, bias checks
       └───────┬────────┘
               │ pass
               ▼
       ┌────────────────┐
       │   CI for model │  ← train, evaluate, fairness
       └───────┬────────┘
               │ pass
               ▼
       ┌────────────────┐
       │   CD for model │  ← promote Staging → Prod
       └───────┬────────┘
               │ deployed
               ▼
       ┌────────────────┐
       │       CM       │  ← monitor drift, latency, quality
       └───────┬────────┘
               │ drift detected
               ▼
       ┌────────────────┐
       │   CT (retrain) │  ← loop back to CI for data
       └────────────────┘
```

---

## 2. Why ML CI/CD is Different

### The Data Dimension
Traditional CI: code in → tests run → pass/fail.
ML CI: code + data + model in → tests run on all three → much more complex pass/fail.

### The Performance Dimension
Traditional CI: tests are deterministic — same input, same output, every time.
ML CI: tests are **statistical** — accuracy varies by ±0.5% across runs. You need statistical significance tests, not exact equality.

### The Time Dimension
Traditional CI: changes are infrequent (humans push code).
ML CI: data changes constantly (new users, new behaviors). Your pipeline may need to run **daily** without any code commit.

### The Cost Dimension
Traditional CI: cheap (run unit tests on a CPU).
ML CI: expensive (train an XGBoost model for 30 minutes on a GPU; or fine-tune an LLM for 4 hours on 8 GPUs).

### The Validation Dimension
Traditional CI: business logic verified by unit tests.
ML CI: business logic verified by unit tests + **offline evaluation** (held-out test set) + **online evaluation** (A/B test in prod).

### Side-by-Side Comparison

| Dimension | Traditional CI/CD | ML CI/CD |
|-----------|-------------------|----------|
| Inputs | Code | Code + Data + Config |
| Trigger | Git push | Git push + schedule + drift + new data |
| Tests | Deterministic | Statistical + Deterministic |
| Build time | Seconds to minutes | Minutes to hours |
| Build cost | Cents | Dollars to thousands of dollars |
| Artifacts | Binary | Model + Data + Config + Metrics |
| Deployment | Once per release | Continuous + automatic retraining |
| Validation | Unit + Integration | + Offline eval + Online A/B |
| Rollback | Binary rollback | Binary + Model + Data snapshot |

---

## 3. The 4 Pipeline Types in ML

A mature ML org runs **four** distinct pipelines. Knowing which one you're debugging is half the battle.

### Type 1: Code Pipeline (Traditional CI/CD)
- **Trigger:** Git push
- **What runs:** Lint, type check, unit tests, integration tests, build Docker image
- **Output:** Pass/fail signal, container image
- **Frequency:** Many times per day per developer
- **Tools:** GitHub Actions, GitLab CI, Jenkins, CircleCI

### Type 2: Training Pipeline (CT)
- **Trigger:** Schedule (daily/weekly), drift detection, manual
- **What runs:** Data validation → feature engineering → train → evaluate → register
- **Output:** New model version in registry (Staging)
- **Frequency:** Daily to weekly
- **Tools:** Airflow, Prefect, Dagster, Kubeflow Pipelines, Argo Workflows

### Type 3: Deployment Pipeline (CD)
- **Trigger:** Manual approval, schedule, auto-promotion rules
- **What runs:** Pull Staging model → deploy to canary → monitor → promote to prod
- **Output:** Live model in production
- **Frequency:** Weekly to monthly
- **Tools:** ArgoCD, Flux, Seldon, KServe, BentoML deployment

### Type 4: Monitoring Pipeline (CM)
- **Trigger:** Continuous (every 1-15 min)
- **What runs:** Compute drift metrics, SLO checks, alert if breach
- **Output:** Alerts, dashboards, retrain triggers
- **Frequency:** Every few minutes
- **Tools:** Evidently, Prometheus, Grafana, Arize, WhyLabs

---

## 4. Continuous Integration (CI) for ML

### The Three Layers of ML CI

#### Layer 1: Code CI (same as traditional)
```yaml
# .github/workflows/code-ci.yml
name: Code CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"
      - run: pip install -r requirements.txt
      - run: pip install black flake8 mypy pytest
      - run: black --check .
      - run: flake8 .
      - run: mypy src/
      - run: pytest tests/unit -v --cov=src --cov-report=xml
      - uses: codecov/codecov-action@v4
```

#### Layer 2: Data CI
Validates that the **data itself** is OK before it can be used in training.

```python
# tests/test_data_quality.py
import pandas as pd
import pytest
from pathlib import Path

@pytest.fixture
def raw_data():
    return pd.read_csv("data/raw/customers.csv")

def test_schema(raw_data):
    """Ensure required columns exist."""
    required = {"customer_id", "age", "signup_date", "monthly_spend"}
    assert required.issubset(raw_data.columns), f"Missing: {required - set(raw_data.columns)}"

def test_no_nulls_in_critical_columns(raw_data):
    """Critical columns must not have nulls."""
    for col in ["customer_id", "age"]:
        assert raw_data[col].isnull().sum() == 0, f"Nulls in {col}"

def test_age_range(raw_data):
    """Age must be between 18 and 120."""
    assert raw_data["age"].between(18, 120).all()

def test_row_count_drift(raw_data):
    """Row count shouldn't drop by more than 20% from baseline."""
    baseline_count = 10000  # stored in config
    current_count = len(raw_data)
    assert current_count >= 0.8 * baseline_count, f"Row count dropped: {current_count} vs {baseline_count}"

def test_unique_ids(raw_data):
    """Customer IDs must be unique."""
    assert raw_data["customer_id"].is_unique
```

#### Layer 3: Model CI
Validates that the **trained model** meets quality thresholds before promotion.

```python
# tests/test_model_quality.py
import pickle
import pandas as pd
import pytest
from sklearn.metrics import accuracy_score, f1_score
import json

@pytest.fixture
def model():
    with open("models/model.pkl", "rb") as f:
        return pickle.load(f)

@pytest.fixture
def test_data():
    df = pd.read_csv("data/processed/test.csv")
    return df.drop(columns=["target"]), df["target"]

@pytest.fixture
def baseline_metrics():
    with open("metrics/baseline.json") as f:
        return json.load(f)

def test_accuracy_above_threshold(model, test_data):
    X, y = test_data
    preds = model.predict(X)
    acc = accuracy_score(y, preds)
    assert acc >= 0.85, f"Accuracy {acc:.4f} below threshold 0.85"

def test_no_regression_vs_baseline(model, test_data, baseline_metrics):
    X, y = test_data
    preds = model.predict(X)
    current_acc = accuracy_score(y, preds)
    baseline_acc = baseline_metrics["accuracy"]
    # Allow 1% regression
    assert current_acc >= baseline_acc - 0.01, (
        f"Regression: {current_acc:.4f} vs baseline {baseline_acc:.4f}"
    )

def test_fairness_across_groups(model, test_data):
    """Model accuracy should not differ by more than 5% across demographic groups."""
    X, y = test_data
    X_with_demo = X.copy()
    X_with_demo["y_true"] = y.values
    X_with_demo["y_pred"] = model.predict(X)

    # Suppose we have a "gender" column for fairness check
    accs = X_with_demo.groupby("gender").apply(
        lambda g: accuracy_score(g["y_true"], g["y_pred"])
    )
    spread = accs.max() - accs.min()
    assert spread < 0.05, f"Fairness violation: accuracy spread = {spread:.4f}"

def test_latency(model, test_data):
    """Model inference must be fast enough for prod SLO."""
    import time
    X, _ = test_data
    sample = X.iloc[:100]

    start = time.perf_counter()
    for _ in range(10):
        model.predict(sample)
    elapsed = time.perf_counter() - start
    per_request_ms = (elapsed / 10) * 1000 / 100
    assert per_request_ms < 50, f"Too slow: {per_request_ms:.2f}ms/sample"
```

---

## 5. Continuous Delivery (CD) for ML

### Model Promotion Flow

```
MLflow Registry
    │
    ├─ None ──── (just trained, no validation yet)
    │
    ├─ Staging ─ (passed offline eval, awaiting online A/B)
    │
    ├─ Production (won A/B, serving live traffic)
    │
    └─ Archived ─ (replaced by newer version, kept for audit)
```

### Promotion Criteria

A model should be promoted Staging → Production only when ALL of:

1. ✅ Offline F1 ≥ current Production F1 (no regression)
2. ✅ Fairness audit passed (spread < 5% across protected groups)
3. ✅ Latency p99 ≤ SLO (e.g., 100ms)
4. ✅ A/B test in shadow showed ≥ 1% lift in business metric
5. ✅ Human approval (required for regulated industries)
6. ✅ Compliance docs attached (model card, data sheet)

### Promotion Script

```python
# scripts/promote_model.py
import mlflow
import argparse
import sys

def promote(model_name: str, version: int, stage: str):
    client = mlflow.tracking.MlflowClient()

    # Validate version exists
    mv = client.get_model_version(model_name, version)
    print(f"Promoting {model_name} v{version} from {mv.current_stage} → {stage}")

    # Check if it's in Staging first (if going to Production)
    if stage == "Production" and mv.current_stage != "Staging":
        print(f"ERROR: Model must be in Staging first. Currently: {mv.current_stage}")
        sys.exit(1)

    # Check latest Staging metrics
    runs = client.search_runs(
        experiment_ids=[mv.run_id[:32]],  # MLflow experiment IDs
        filter_string=f"attributes.run_id = '{mv.run_id}'",
    )
    if not runs:
        print("ERROR: Could not find run for this model version.")
        sys.exit(1)
    metrics = runs[0].data.metrics
    if "f1" not in metrics or metrics["f1"] < 0.85:
        print(f"ERROR: F1 {metrics.get('f1')} below threshold 0.85")
        sys.exit(1)

    # Promote
    client.transition_model_version_stage(
        name=model_name,
        version=version,
        stage=stage,
        archive_existing_versions=(stage == "Production"),
    )
    print(f"✓ Promoted {model_name} v{version} to {stage}")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--model", required=True)
    p.add_argument("--version", type=int, required=True)
    p.add_argument("--stage", choices=["Staging", "Production", "Archived"], required=True)
    args = p.parse_args()
    promote(args.model, args.version, args.stage)
```

---

## 6. Continuous Training (CT) — ML-Specific

CT is what makes MLOps MLOps. Without it, you're just doing DevOps for an ML app.

### CT Triggers

| Trigger Type | Example | Use Case |
|---|---|---|
| Schedule | "Every Sunday at 2am" | Stable models, regular refresh |
| Data-driven | "When 10k new labeled rows arrive" | When you have a labeling pipeline |
| Drift-driven | "When PSI > 0.2" | When distribution shifts are the main concern |
| Performance-driven | "When F1 drops below 0.80" | Reactive — bad UX before trigger |
| Manual | "When Bob clicks Retrain" | OK for low-stakes models |
| Event-driven | "When a new product launches" | Business context changes |

### CT Pipeline Architecture

```
        ┌──────────────────────────────────┐
        │  Trigger (cron / drift / data)   │
        └────────────┬─────────────────────┘
                     ▼
        ┌──────────────────────────────────┐
        │  Step 1: Pull latest data        │
        │  (DVC pull / SQL query)          │
        └────────────┬─────────────────────┘
                     ▼
        ┌──────────────────────────────────┐
        │  Step 2: Data validation         │
        │  (Great Expectations / pytest)   │
        └────────────┬─────────────────────┘
                     ▼ (pass)
        ┌──────────────────────────────────┐
        │  Step 3: Feature engineering     │
        │  (dbt / Feast)                   │
        └────────────┬─────────────────────┘
                     ▼
        ┌──────────────────────────────────┐
        │  Step 4: Train model             │
        │  (sklearn / XGBoost / PyTorch)   │
        └────────────┬─────────────────────┘
                     ▼
        ┌──────────────────────────────────┐
        │  Step 5: Evaluate offline        │
        │  (vs. current Production model)  │
        └────────────┬─────────────────────┘
                     ▼ (better)
        ┌──────────────────────────────────┐
        │  Step 6: Register as Staging     │
        │  (MLflow)                        │
        └────────────┬─────────────────────┘
                     ▼
        ┌──────────────────────────────────┐
        │  Step 7: Notify humans to A/B    │
        │  (Slack / email)                 │
        └──────────────────────────────────┘
```

### Prefect Example — A Real CT Pipeline

```python
# pipelines/ct_pipeline.py
from prefect import flow, task
import pandas as pd
import pickle
import mlflow
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score, accuracy_score
from sklearn.model_selection import train_test_split
from datetime import datetime
import os

@task(retries=3, retry_delay_seconds=60)
def fetch_data():
    """Pull latest labeled data from warehouse."""
    # In real life: query Snowflake/BigQuery
    df = pd.read_csv("data/raw/customers.csv")
    print(f"Fetched {len(df)} rows")
    return df

@task
def validate_data(df):
    """Schema + quality checks."""
    assert df["customer_id"].is_unique
    assert df["age"].between(18, 120).all()
    assert df["monthly_spend"].ge(0).all()
    assert df.isnull().sum().sum() / df.size < 0.05  # < 5% nulls
    print("Data validation passed")
    return df

@task
def engineer_features(df):
    df["tenure_days"] = (pd.Timestamp.now() - pd.to_datetime(df["signup_date"])).dt.days
    df["spend_per_day"] = df["monthly_spend"] / df["tenure_days"].clip(lower=1)
    return df

@task
def train_model(df):
    X = df.drop(columns=["customer_id", "signup_date", "churn"])
    y = df["churn"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    model = RandomForestClassifier(n_estimators=200, max_depth=8, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)
    return model, X_test, y_test

@task
def evaluate_model(model, X_test, y_test):
    preds = model.predict(X_test)
    return {
        "f1": f1_score(y_test, preds),
        "accuracy": accuracy_score(y_test, preds),
    }

@task
def compare_to_production(new_metrics):
    """Compare new model's metrics to current Production model."""
    client = mlflow.tracking.MlflowClient()
    try:
        prod_versions = client.get_latest_versions("churn-prediction", stages=["Production"])
        if not prod_versions:
            return True  # No prod model yet, accept this one
        prod_run = client.get_run(prod_versions[0].run_id)
        prod_f1 = prod_run.data.metrics.get("f1", 0)
        print(f"New F1: {new_metrics['f1']:.4f}, Prod F1: {prod_f1:.4f}")
        return new_metrics["f1"] > prod_f1  # strictly better
    except Exception as e:
        print(f"Could not compare: {e}")
        return False

@task
def register_model(model, metrics, is_better):
    if not is_better:
        print("New model not better than Production — skipping registration")
        return None

    mlflow.set_tracking_uri("http://mlflow:5000")
    mlflow.set_experiment("churn-prediction")

    with mlflow.start_run(run_name=f"ct-{datetime.now().isoformat()}") as run:
        mlflow.log_params({"n_estimators": 200, "max_depth": 8})
        mlflow.log_metrics(metrics)
        mlflow.sklearn.log_model(
            model,
            artifact_path="model",
            registered_model_name="churn-prediction"
        )
        # Transition to Staging
        client = mlflow.tracking.MlflowClient()
        versions = client.search_model_versions(f"name='churn-prediction'")
        latest_version = max(v.version for v in versions)
        client.transition_model_version_stage(
            name="churn-prediction",
            version=latest_version,
            stage="Staging",
        )
        print(f"Registered v{latest_version} to Staging")
        return latest_version

@task
def notify_slack(version, metrics):
    # Use slack_sdk in real life
    print(f"📢 New model v{version} in Staging. F1: {metrics['f1']:.4f}. Please A/B test.")

@flow(name="churn-retrain", log_prints=True)
def retrain_pipeline():
    df = fetch_data()
    df = validate_data(df)
    df = engineer_features(df)
    model, X_test, y_test = train_model(df)
    metrics = evaluate_model(model, X_test, y_test)
    is_better = compare_to_production(metrics)
    version = register_model(model, metrics, is_better)
    if version:
        notify_slack(version, metrics)

if __name__ == "__main__":
    # Run once
    retrain_pipeline()

    # Or schedule (in production, use Prefect Deployments)
    # from prefect.deployments import Deployment
    # Deployment(retrain_pipeline).serve(name="weekly-retrain", cron="0 2 * * 0")
```

---

## 7. Continuous Monitoring (CM)

See File 1, Section 13 for the deep dive. Here's the CI/CD angle:

### Monitoring Should Trigger CT

```python
# monitoring/drift_check.py (runs every hour via cron or Airflow)
import pandas as pd
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset
import requests
import os

def check_drift():
    reference = pd.read_csv("data/reference.csv")
    current = pd.read_csv("data/last_hour_predictions.csv")

    report = Report(metrics=[DataDriftPreset()])
    report.run(reference_data=reference, current_data=current)
    result = report.as_dict()
    drift_detected = result["metrics"][0]["result"]["dataset_drift"]

    if drift_detected:
        print("🚨 DRIFT DETECTED — triggering CT pipeline")
        # Trigger Prefect deployment
        requests.post(
            f"{os.environ['PREFECT_API_URL']}/deployments/churn-retrain/execute",
            headers={"Authorization": f"Bearer {os.environ['PREFECT_API_KEY']}"},
        )

if __name__ == "__main__":
    check_drift()
```

---

## 8. GitHub Actions for ML — Deep Dive

GitHub Actions is the most accessible CI/CD tool for ML. Free for public repos, generous free tier for private, integrates with everything.

### Anatomy of a Workflow

```yaml
name: ML Pipeline  # workflow name

on:  # trigger
  push:
    branches: [main]
    paths:
      - "src/**"
      - "data/**"
      - "models/**"
      - ".github/workflows/ml-pipeline.yml"
  schedule:
    - cron: "0 2 * * 0"  # every Sunday 2am UTC
  workflow_dispatch:  # manual trigger

permissions:
  contents: read
  packages: write

env:
  PYTHON_VERSION: "3.11"
  MLFLOW_TRACKING_URI: ${{ secrets.MLFLOW_TRACKING_URI }}

jobs:
  # ---------- JOB 1: code quality ----------
  lint-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: pip
      - run: pip install -r requirements.txt -r requirements-dev.txt
      - run: black --check .
      - run: ruff check .
      - run: mypy src/
      - run: pytest tests/unit -v --cov=src

  # ---------- JOB 2: data validation ----------
  data-validation:
    needs: lint-and-test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: pip
      - run: pip install -r requirements.txt
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      - name: Pull latest data
        run: dvc pull
      - name: Run data tests
        run: pytest tests/data -v

  # ---------- JOB 3: train + evaluate ----------
  train:
    needs: data-validation
    runs-on: ubuntu-latest  # use self-hosted GPU runner for real models
    timeout-minutes: 60
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: pip
      - run: pip install -r requirements.txt
      - name: Configure AWS
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      - run: dvc pull
      - name: Run training pipeline
        run: dvc repro
      - name: Run model tests
        run: pytest tests/model -v
      - name: Upload metrics
        uses: actions/upload-artifact@v4
        with:
          name: metrics
          path: metrics/
      - name: Push to MLflow
        run: python scripts/register_model.py
        env:
          MLFLOW_TRACKING_URI: ${{ secrets.MLFLOW_TRACKING_URI }}

  # ---------- JOB 4: build & push Docker image ----------
  build-image:
    needs: train
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}
      - uses: docker/build-push-action@v5
        with:
          context: .
          file: ./Dockerfile
          push: true
          tags: |
            myuser/churn-api:latest
            myuser/churn-api:${{ github.sha }}

  # ---------- JOB 5: deploy to staging ----------
  deploy-staging:
    needs: build-image
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment: staging
    steps:
      - uses: actions/checkout@v4
      - uses: azure/setup-kubectl@v4
      - name: Configure kubectl
        run: |
          echo "${{ secrets.KUBECONFIG_STAGING }}" > kubeconfig
          export KUBECONFIG=kubeconfig
      - name: Deploy
        run: |
          kubectl set image deployment/churn-api churn-api=myuser/churn-api:${{ github.sha }} -n staging
          kubectl rollout status deployment/churn-api -n staging --timeout=300s

  # ---------- JOB 6: deploy to production (manual approval) ----------
  deploy-production:
    needs: deploy-staging
    runs-on: ubuntu-latest
    environment:
      name: production  # requires manual approval in GitHub UI
    steps:
      - uses: actions/checkout@v4
      - uses: azure/setup-kubectl@v4
      - name: Configure kubectl
        run: |
          echo "${{ secrets.KUBECONFIG_PROD }}" > kubeconfig
          export KUBECONFIG=kubeconfig
      - name: Canary deploy (10% traffic)
        run: |
          kubectl set image deployment/churn-api-canary churn-api=myuser/churn-api:${{ github.sha }} -n production
          kubectl rollout status deployment/churn-api-canary -n production
      - name: Wait 1 hour for canary metrics
        run: sleep 3600
      - name: Full rollout
        run: |
          kubectl set image deployment/churn-api churn-api=myuser/churn-api:${{ github.sha }} -n production
          kubectl rollout status deployment/churn-api -n production
```

### Key Concepts in This Workflow

1. **`needs:`** — serializes jobs (data-validation runs only after lint-and-test passes).
2. **`environment:`** — GitHub Environments let you require manual approvals per environment.
3. **`paths:`** — only trigger on relevant file changes (avoid running ML pipeline on README edits).
4. **`schedule:`** — cron syntax for daily/weekly triggers (CT).
5. **`workflow_dispatch:`** — manual trigger button in GitHub UI.
6. **Self-hosted runners** — for GPU work, attach your own runner with NVIDIA runtime.
7. **`actions/cache`** — speeds up dependency install and DVC data pulls.

---

## 9. GitLab CI for ML

GitLab CI is similar to GitHub Actions but with `.gitlab-ci.yml`. Many enterprises use GitLab, so it's worth knowing.

```yaml
# .gitlab-ci.yml
stages:
  - test
  - data
  - train
  - build
  - deploy

variables:
  PYTHON_IMAGE: "python:3.11-slim"
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"

cache:
  paths:
    - .cache/pip
    - venv/

# ---------- Stage: test ----------
lint:
  stage: test
  image: $PYTHON_IMAGE
  script:
    - pip install black ruff mypy
    - black --check .
    - ruff check .
    - mypy src/

unit-test:
  stage: test
  image: $PYTHON_IMAGE
  script:
    - pip install -r requirements.txt -r requirements-dev.txt
    - pytest tests/unit -v --cov=src
  coverage: '/TOTAL.*\s+(\d+\%)$/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml

# ---------- Stage: data ----------
data-validation:
  stage: data
  image: $PYTHON_IMAGE
  script:
    - pip install dvc[s3] pandas pytest
    - dvc pull
    - pytest tests/data -v
  rules:
    - if: $CI_PIPELINE_SOURCE == "schedule"
    - if: $CI_COMMIT_BRANCH == "main"

# ---------- Stage: train ----------
train:
  stage: train
  image: $PYTHON_IMAGE
  script:
    - pip install -r requirements.txt
    - dvc pull
    - dvc repro
    - pytest tests/model -v
  artifacts:
    paths:
      - metrics/
      - models/
    expire_in: 1 week
  rules:
    - if: $CI_PIPELINE_SOURCE == "schedule"
    - if: $CI_COMMIT_BRANCH == "main"

# ---------- Stage: build ----------
build-image:
  stage: build
  image: docker:24
  services:
    - docker:24-dind
  script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA
  rules:
    - if: $CI_COMMIT_BRANCH == "main"

# ---------- Stage: deploy ----------
deploy-staging:
  stage: deploy
  image: bitnami/kubectl:latest
  environment:
    name: staging
  script:
    - kubectl set image deployment/churn-api churn-api=$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA -n staging
    - kubectl rollout status deployment/churn-api -n staging
  rules:
    - if: $CI_COMMIT_BRANCH == "main"

deploy-production:
  stage: deploy
  image: bitnami/kubectl:latest
  environment:
    name: production
  when: manual  # manual approval gate
  script:
    - kubectl set image deployment/churn-api churn-api=$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA -n production
    - kubectl rollout status deployment/churn-api -n production
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
```

### Differences from GitHub Actions

- **No `actions/checkout`** — GitLab auto-checks-out the repo.
- **`rules:` instead of `if:`** — more powerful conditional logic.
- **`environment:` with `when: manual`** — manual approval gates (like GitHub Environments).
- **Built-in Docker registry** — `$CI_REGISTRY_IMAGE` is your project's registry.
- **`services:`** — sidecar containers (like Docker-in-Docker).

---

## 10. Jenkins for ML

Jenkins is the OG. Still dominant in enterprises, especially regulated industries. Here's a Jenkinsfile for ML:

```groovy
// Jenkinsfile
pipeline {
    agent {
        kubernetes {
            yaml '''
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: python
    image: python:3.11-slim
    command: ["sleep", "infinity"]
    resources:
      limits:
        memory: "4Gi"
        cpu: "2"
  - name: docker
    image: docker:24
    command: ["sleep", "infinity"]
    securityContext:
      privileged: true
'''
        }
    }

    environment {
        MLFLOW_TRACKING_URI = credentials('mlflow-uri')
        AWS_ACCESS_KEY_ID = credentials('aws-key-id')
        AWS_SECRET_ACCESS_KEY = credentials('aws-secret')
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Setup') {
            steps {
                container('python') {
                    sh 'pip install -r requirements.txt -r requirements-dev.txt'
                }
            }
        }

        stage('Lint & Test') {
            parallel {
                stage('Lint') {
                    steps {
                        container('python') {
                            sh 'black --check .'
                            sh 'ruff check .'
                            sh 'mypy src/'
                        }
                    }
                }
                stage('Unit Tests') {
                    steps {
                        container('python') {
                            sh 'pytest tests/unit -v --cov=src --cov-report=xml'
                        }
                    }
                    post {
                        always {
                            junit 'test-results.xml'
                            cobertura coberturaReportFile: 'coverage.xml'
                        }
                    }
                }
            }
        }

        stage('Data Validation') {
            steps {
                container('python') {
                    sh 'dvc pull'
                    sh 'pytest tests/data -v'
                }
            }
        }

        stage('Train') {
            steps {
                container('python') {
                    sh 'dvc repro'
                    sh 'pytest tests/model -v'
                    sh 'python scripts/register_model.py'
                }
            }
        }

        stage('Build Image') {
            steps {
                container('docker') {
                    sh "docker build -t myregistry/churn-api:${env.BUILD_NUMBER} ."
                    sh "docker push myregistry/churn-api:${env.BUILD_NUMBER}"
                }
            }
        }

        stage('Deploy Staging') {
            when { branch 'main' }
            steps {
                sh "kubectl set image deployment/churn-api churn-api=myregistry/churn-api:${env.BUILD_NUMBER} -n staging"
                sh "kubectl rollout status deployment/churn-api -n staging"
            }
        }

        stage('Deploy Production') {
            when {
                branch 'main'
                beforeInput true
            }
            input {
                message "Deploy to production?"
                ok "Deploy"
            }
            steps {
                sh "kubectl set image deployment/churn-api churn-api=myregistry/churn-api:${env.BUILD_NUMBER} -n production"
                sh "kubectl rollout status deployment/churn-api -n production"
            }
        }
    }

    post {
        failure {
            slackSend channel: '#ml-alerts', color: 'danger',
                message: "Pipeline failed: ${env.JOB_NAME} #${env.BUILD_NUMBER}"
        }
        success {
            slackSend channel: '#ml-alerts', color: 'good',
                message: "Pipeline passed: ${env.JOB_NAME} #${env.BUILD_NUMBER}"
        }
    }
}
```

### When to Use Jenkins

- Enterprise with existing Jenkins infra
- Heavy on-prem requirements (banks, government)
- Need fine-grained RBAC + audit logs
- Many pipelines share common library (use Jenkins Shared Libraries)

### When NOT to Use Jenkins

- Greenfield startup — use GitHub Actions / GitLab CI
- Heavy GPU/ML workloads without K8s — managing Jenkins agents is painful
- Want modern developer experience — Jenkins UI feels dated

---

## 11. Testing ML Systems — The 5 Layers

Most ML teams only do Layer 1. Mature teams do all 5. Aim for all 5.

### Layer 1: Unit Tests
Test individual functions in isolation.
```python
def test_feature_engineering():
    df = pd.DataFrame({"monthly_spend": [100, 200], "tenure_days": [30, 60]})
    result = engineer_features(df)
    assert "spend_per_day" in result.columns
    assert result["spend_per_day"].iloc[0] == pytest.approx(100/30, rel=1e-3)
```

### Layer 2: Integration Tests
Test that components work together.
```python
def test_train_pipeline_runs_end_to_end(tmp_path):
    # Use small synthetic dataset
    df = generate_synthetic_data(n=100)
    df.to_csv(tmp_path / "data.csv")
    
    # Run full pipeline
    run_pipeline(data_path=tmp_path / "data.csv", model_path=tmp_path / "model.pkl")
    
    # Assert artifacts exist
    assert (tmp_path / "model.pkl").exists()
    assert (tmp_path / "metrics.json").exists()
```

### Layer 3: Data Tests
Test data quality + schema (see Section 4 Layer 2).

### Layer 4: Model Tests
Test model behavior + performance (see Section 4 Layer 3).
- Accuracy threshold
- No regression vs baseline
- Fairness across groups
- Latency SLO
- Robustness to noise
- Edge cases (empty input, all zeros, max values)

### Layer 5: Production Tests
Test the **served** model behaves correctly.
```python
def test_served_model_endpoint():
    response = requests.post(
        "http://staging-api.example.com/predict",
        json={"features": {"age": 35, "spend": 100}}
    )
    assert response.status_code == 200
    result = response.json()
    assert "prediction" in result
    assert "probability" in result
    assert 0 <= result["probability"] <= 1
    assert response.elapsed.total_seconds() < 0.5  # 500ms SLO

def test_served_model_handles_bad_input():
    response = requests.post(
        "http://staging-api.example.com/predict",
        json={"features": {}}  # missing fields
    )
    assert response.status_code == 422  # FastAPI validation error

def test_served_model_is_deterministic():
    payload = {"features": {"age": 35, "spend": 100}}
    r1 = requests.post("http://staging-api.example.com/predict", json=payload).json()
    r2 = requests.post("http://staging-api.example.com/predict", json=payload).json()
    assert r1 == r2
```

---

## 12. Model Promotion Strategies

### Strategy 1: Champion-Challenger
- Champion = current Production model
- Challenger = new model in Staging
- Run both, compare on same test set
- Promote challenger if it wins
- **Best for:** offline evaluation

### Strategy 2: A/B Testing
- Split live traffic: 90% to A (champion), 10% to B (challenger)
- Measure business metric (conversion, revenue, CTR)
- After N users + statistical significance, declare winner
- **Best for:** online evaluation with clear business metric

### Strategy 3: Multi-Armed Bandit
- Dynamically shift traffic to better-performing arm
- No fixed experiment end — continuous optimization
- **Best for:** short-feedback-loop scenarios (recommendations, ads)

### Strategy 4: Shadow Deployment
- New model runs alongside old, predictions logged but NOT served to users
- Compare predictions to gauge what would change
- **Best for:** high-stakes models where you can't A/B test (medical, fraud)

### Strategy 5: Canary Deployment
- New model serves 1% → 5% → 25% → 100% of traffic progressively
- Auto-rollback if any SLO breach
- **Best for:** risk-averse production rollouts

### Sample A/B Test Design

```python
# ab_test_design.py
import math

def sample_size_for_ab_test(
    baseline_rate: float,  # e.g., 0.10 (10% conversion)
    mde: float,  # minimum detectable effect, e.g., 0.01 (1% absolute)
    alpha: float = 0.05,
    power: float = 0.8,
):
    """
    Returns sample size per arm.
    """
    z_alpha = 1.96  # two-tailed, alpha=0.05
    z_beta = 0.84   # power=0.8
    p1 = baseline_rate
    p2 = baseline_rate + mde
    p_avg = (p1 + p2) / 2
    n = ((z_alpha * math.sqrt(2 * p_avg * (1 - p_avg))) 
         + (z_beta * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))))**2 / (p1 - p2)**2
    return math.ceil(n)

# 10% baseline conversion, want to detect 1% absolute lift
n = sample_size_for_ab_test(0.10, 0.01)
print(f"Need {n:,} users per arm, {2*n:,} total")
# Output: Need ~14,750 users per arm
```

---

## 13. Blue/Green, Canary, Shadow Deployments

### Blue/Green
- Two identical environments (Blue = current, Green = new)
- Switch traffic from Blue → Green all at once
- Easy rollback (switch back)
- **Cost:** 2x infrastructure during switch
- **Risk:** all users hit any new bugs simultaneously

### Canary
- Progressive rollout: 1% → 5% → 25% → 50% → 100%
- Each stage waits for SLO confirmation
- Auto-rollback on SLO breach
- **Cost:** minimal extra infra
- **Risk:** low — caught early

### Shadow
- New model receives copy of live traffic
- Predictions logged, NOT served to users
- Compare new vs old predictions on same inputs
- **Cost:** 2x model compute
- **Risk:** very low — no user impact

### Kubernetes Canary Example

```yaml
# canary-deployment.yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: churn-api
spec:
  replicas: 10
  strategy:
    canary:
      canaryService: churn-api-canary
      stableService: churn-api-stable
      trafficRouting:
        nginx:
          stableIngress: churn-api-ingress
      steps:
      - setWeight: 5
      - pause: { duration: 1h }
      - setWeight: 25
      - pause: { duration: 2h }
      - setWeight: 50
      - pause: { duration: 2h }
      - setWeight: 100
  selector:
    matchLabels:
      app: churn-api
  template:
    metadata:
      labels:
        app: churn-api
    spec:
      containers:
      - name: api
        image: myuser/churn-api:v2
        ports:
        - containerPort: 8000
        resources:
          requests:
            cpu: 500m
            memory: 1Gi
          limits:
            cpu: 1000m
            memory: 2Gi
```

With ArgoCD/Argo Rollouts, this gives you **automated progressive delivery with auto-rollback**.

---

## 14. Rollback Strategies for ML

### What to Roll Back

| Layer | Rollback action |
|---|---|
| Code | `kubectl rollout undo deployment/churn-api` |
| Model | `mlflow models transition ... -v N-1 -s Production` |
| Data | `git checkout <commit> && dvc checkout` |
| Config | `kubectl rollout undo configmap/churn-api-config` |

### Automated Rollback Trigger

```python
# rollback_monitor.py (runs continuously)
import requests
import time
import mlflow
from kubernetes import client, config

PROMETHEUS_URL = "http://prometheus:9090"
ERROR_RATE_THRESHOLD = 0.05  # 5% errors → rollback
LATENCY_P99_THRESHOLD = 2.0  # 2s p99 → rollback

def get_slo_breaches():
    queries = {
        "error_rate": 'rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])',
        "latency_p99": 'histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))',
    }
    breaches = []
    for name, q in queries.items():
        r = requests.get(f"{PROMETHEUS_URL}/api/v1/query", params={"query": q})
        value = float(r.json()["data"]["result"][0]["value"][1])
        threshold = {"error_rate": ERROR_RATE_THRESHOLD, "latency_p99": LATENCY_P99_THRESHOLD}[name]
        if value > threshold:
            breaches.append((name, value, threshold))
    return breaches

def rollback_model():
    client_mlflow = mlflow.tracking.MlflowClient()
    versions = client_mlflow.search_model_versions("name='churn-prediction'")
    prod_version = next(v for v in versions if v.current_stage == "Production")
    archived = [v for v in versions if v.current_stage == "Archived"]
    archived.sort(key=lambda v: v.version, reverse=True)
    previous = archived[0]
    client_mlflow.transition_model_version_stage(
        name="churn-prediction",
        version=previous.version,
        stage="Production",
        archive_existing_versions=True,
    )
    print(f"Rolled back to v{previous.version}")

def rollback_k8s():
    config.load_incluster_config()
    apps_v1 = client.AppsV1Api()
    apps_v1.rollout_undo_deployment_with_retry("churn-api", namespace="production")
    print("Rolled back K8s deployment")

if __name__ == "__main__":
    while True:
        breaches = get_slo_breaches()
        if breaches:
            print(f"SLO breaches: {breaches}")
            rollback_k8s()
            rollback_model()
            # Alert on-call
            requests.post(os.environ["SLACK_WEBHOOK"], json={"text": "ROLLBACK TRIGGERED"})
            break
        time.sleep(60)
```

---

## 15. End-to-End Real-World CI/CD Pipeline

Let's tie it all together. Here's the **complete** GitHub Actions workflow for a real ML service.

### Repo Structure
```
churn-prediction/
├── .github/workflows/
│   ├── ci.yml                  # code CI
│   ├── training.yml            # CT (scheduled)
│   └── deploy.yml              # CD (manual)
├── src/
│   ├── __init__.py
│   ├── data.py                 # data loading
│   ├── features.py             # feature engineering
│   ├── train.py                # training
│   ├── evaluate.py             # evaluation
│   └── serve.py                # FastAPI app
├── tests/
│   ├── unit/
│   ├── data/
│   └── model/
├── dvc.yaml
├── params.yaml
├── Dockerfile
├── k8s/
│   ├── deployment.yaml
│   ├── service.yaml
│   └── canary.yaml
├── requirements.txt
└── README.md
```

### .github/workflows/ci.yml
```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11", cache: pip }
      - run: pip install black ruff mypy
      - run: black --check .
      - run: ruff check .
      - run: mypy src/

  unit-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11", cache: pip }
      - run: pip install -r requirements.txt -r requirements-dev.txt
      - run: pytest tests/unit -v --cov=src --cov-report=xml
      - uses: codecov/codecov-action@v4

  integration-test:
    needs: unit-test
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
        ports: ["5432:5432"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11", cache: pip }
      - run: pip install -r requirements.txt
      - run: pytest tests/integration -v
        env:
          DATABASE_URL: postgresql://postgres:test@localhost:5432/postgres
```

### .github/workflows/training.yml
```yaml
name: Continuous Training

on:
  schedule:
    - cron: "0 2 * * 0"  # Weekly Sunday 2am UTC
  workflow_dispatch:

jobs:
  train:
    runs-on: ubuntu-latest
    timeout-minutes: 120
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11", cache: pip }

      - name: Configure AWS
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_KEY }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET }}
          aws-region: us-east-1

      - run: pip install -r requirements.txt

      - name: Pull latest data
        run: dvc pull

      - name: Run pipeline
        run: dvc repro -f

      - name: Run model tests
        run: pytest tests/model -v

      - name: Compare to production
        id: compare
        run: |
          python scripts/compare_to_prod.py > /tmp/result.json
          echo "should_promote=$(jq .should_promote /tmp/result.json)" >> $GITHUB_OUTPUT
          echo "new_f1=$(jq .new_f1 /tmp/result.json)" >> $GITHUB_OUTPUT
          echo "prod_f1=$(jq .prod_f1 /tmp/result.json)" >> $GITHUB_OUTPUT

      - name: Register to MLflow (Staging)
        if: steps.compare.outputs.should_promote == 'true'
        run: python scripts/register_to_staging.py
        env:
          MLFLOW_TRACKING_URI: ${{ secrets.MLFLOW_URI }}

      - name: Notify Slack
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "🔄 CT pipeline complete. New F1: ${{ steps.compare.outputs.new_f1 }}, Prod F1: ${{ steps.compare.outputs.prod_f1 }}. Promoted: ${{ steps.compare.outputs.should_promote }}"
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
```

### .github/workflows/deploy.yml
```yaml
name: Deploy

on:
  workflow_dispatch:
    inputs:
      model_version:
        description: "Model version to deploy"
        required: true
        type: string
      environment:
        description: "Environment"
        required: true
        type: choice
        default: staging
        options: [staging, production]

jobs:
  build:
    runs-on: ubuntu-latest
    outputs:
      image_tag: ${{ steps.build.outputs.tag }}
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USER }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}
      - id: build
        run: |
          TAG="${{ github.sha }}"
          docker build -t myuser/churn-api:$TAG --build-arg MODEL_VERSION=${{ inputs.model_version }} .
          docker push myuser/churn-api:$TAG
          echo "tag=$TAG" >> $GITHUB_OUTPUT

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment: ${{ inputs.environment }}
    steps:
      - uses: actions/checkout@v4
      - uses: azure/setup-kubectl@v4
      - run: |
          mkdir -p ~/.kube
          echo "${{ secrets.KUBECONFIG }}" > ~/.kube/config
      - name: Deploy
        run: |
          kubectl set image deployment/churn-api \
            api=myuser/churn-api:${{ needs.build.outputs.image_tag }} \
            -n ${{ inputs.environment }}
          kubectl rollout status deployment/churn-api \
            -n ${{ inputs.environment }} --timeout=600s
      - name: Smoke test
        run: |
          URL="https://${{ inputs.environment }}.churn-api.example.com/health"
          for i in {1..30}; do
            if curl -f $URL; then exit 0; fi
            sleep 10
          done
          exit 1
```

---

## 16. Security & Compliance in ML Pipelines

### The 6 Attack Vectors for ML Systems

1. **Data poisoning** — attacker injects malicious training data. Defense: input validation, anomaly detection on training data.
2. **Model inversion** — attacker reconstructs training data from model outputs. Defense: differential privacy (DP-SGD), limit prediction confidence exposure.
3. **Adversarial inputs** — attacker perturbs input to get wrong prediction. Defense: adversarial training, input validation.
4. **Model theft** — attacker queries your API many times to clone your model. Defense: rate limiting, query pattern detection.
5. **Supply chain attacks** — malicious PyPI package in your requirements. Defense: pin versions, scan with `pip-audit`, `safety`.
6. **Secret leakage** — API keys committed to git. Defense: pre-commit hooks with `detect-secrets`, GitHub Secret Scanning.

### Pre-commit Hooks for ML Security

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: [--maxkb=500]  # catch large data accidentally added
      - id: detect-private-key

  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.5.0
    hooks:
      - id: detect-secrets
        args: [--baseline, .secrets.baseline]

  - repo: https://github.com/psf/black
    rev: 24.4.2
    hooks:
      - id: black

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.5.0
    hooks:
      - id: ruff
        args: [--fix]

  - repo: https://github.com/pycqa/bandit
    rev: 1.7.9
    hooks:
      - id: bandit
        args: [-r, src/]
```

### Model Cards for Compliance

```python
# scripts/generate_model_card.py
from dataclasses import dataclass
from datetime import datetime
import json

@dataclass
class ModelCard:
    name: str
    version: str
    description: str
    intended_use: str
    intended_users: str
    out_of_scope: list[str]
    training_data: str
    evaluation_data: str
    metrics: dict
    ethical_considerations: str
    caveats: str
    contact: str

card = ModelCard(
    name="churn-prediction",
    version="v2.3",
    description="Predicts probability of customer churn in next 30 days.",
    intended_use="Customer retention campaigns by marketing team.",
    intended_users="Marketing analysts at our company.",
    out_of_scope=["Use for non-customer populations", "Use for credit decisions"],
    training_data="Customer behavior data from Jan 2022 - Dec 2023. 250k rows.",
    evaluation_data="Held-out 50k customers from Jan 2024.",
    metrics={"accuracy": 0.87, "f1": 0.83, "auc": 0.91},
    ethical_considerations="Model should not be sole determinant of customer outreach. Demographic fairness audited quarterly.",
    caveats="Performance may degrade if product pricing changes significantly.",
    contact="ml-team@company.com",
)

with open(f"model_card_v{card.version}.json", "w") as f:
    json.dump(card.__dict__, f, indent=2)
```

---

## 17. Cost Optimization in CI/CD

ML CI/CD is **expensive**. A naive setup can burn $10k+/month. Optimize:

### 1. Cache Dependencies
```yaml
- uses: actions/setup-python@v5
  with:
    python-version: "3.11"
    cache: pip          # cache pip downloads
    cache-dependency-path: requirements.txt
```

### 2. Cache DVC Data
```yaml
- uses: actions/cache@v4
  with:
    path: .dvc/cache
    key: dvc-${{ hashFiles('data/*.dvc') }}
```

### 3. Skip Unnecessary Runs
```yaml
on:
  push:
    paths:
      - "src/**"
      - "tests/**"
      - "data/**"
      - "requirements.txt"
      - ".github/workflows/**"
```

### 4. Use Smaller Runners for Non-ML Jobs
Linting, unit tests, docs → `ubuntu-latest` (cheap).
Training → GPU runner (expensive, only when needed).

### 5. Self-hosted Runners for Heavy ML
GitHub's hosted GPU runners are ~$0.40/min. Self-hosted with a $1k GPU pays back in ~3 weeks of heavy use.

### 6. Spot Instances for Training
Use preemptible/spot instances for training jobs that can resume from checkpoints.

### 7. Model Distillation
Train a huge model once, distill into a small model for serving. Inference 10x cheaper.

### 8. Quantization
Convert FP32 → INT8 for inference. 4x smaller, 2-4x faster, minimal accuracy loss.

---

## 18. Common Failures and How to Prevent Them

### Failure 1: "Pipeline passed in CI but failed in prod"
**Cause:** Environment differences (Python version, library versions, OS).
**Fix:** Use Docker for everything. CI builds the exact image that goes to prod.

### Failure 2: "Model degraded, no one noticed for 2 weeks"
**Cause:** No monitoring.
**Fix:** Set up Evidently + Prometheus from day 1. Alerts to Slack/PagerDuty.

### Failure 3: "Training data leaked into test set"
**Cause:** Split BEFORE deduplication, or test set is a subset of train.
**Fix:** Use `sklearn.model_selection.train_test_split` with `random_state` and audit periodically.

### Failure 4: "Pipeline took 6 hours, then failed at the last step"
**Cause:** No checkpointing.
**Fix:** Each pipeline step should be idempotent and resumable. Use DVC/MLflow to cache intermediate results.

### Failure 5: "Deployed model gives different predictions than the trained model"
**Cause:** Training-serving skew. Preprocessing differs between train and serve.
**Fix:** Use the same code path for both. Or use a feature store.

### Failure 6: "Costs spiked to $20k last month"
**Cause:** Retraining too frequently, no caching, over-provisioned GPUs.
**Fix:** Monitor CI/CD costs. Set budgets. Optimize per Section 17.

### Failure 7: "Audit found we can't explain why the model denied this loan"
**Cause:** No lineage tracking, no model card, no logging of which features led to which prediction.
**Fix:** Log every prediction with input features. Use SHAP for explanations. Generate model cards.

### Failure 8: "Model served stale data because feature store lagged"
**Cause:** Feature store online serving not synced with offline.
**Fix:** Monitor feature freshness. Alert if last-update > 1 hour.

---

## 19. Summary & Next Steps

### What You Learned

1. ML CI/CD = traditional CI/CD + Data CI + Model CI + CT + CM.
2. There are 4 pipeline types: code, training, deployment, monitoring.
3. GitHub Actions / GitLab CI / Jenkins all can do ML CI/CD — pick based on context.
4. ML testing has 5 layers — aim for all 5.
5. Model promotion uses Champion-Challenger, A/B, Shadow, or Canary.
6. Rollback must include code, model, AND data.
7. Security: 6 attack vectors, mitigate with pre-commit hooks, DP, rate limiting.
8. Cost optimization is non-trivial — cache, self-host, quantize.

### What's Next

- Read **03_AI_API_Development_FastAPI.md** — how to actually wrap a model in a serving API.
- Read **04_Docker_Kubernetes_for_ML.md** — how to package and deploy.
- Read **05_10_Projects_Beginner_to_Pro.md** — apply this end-to-end.

### How to Practice This

1. Set up a free GitHub repo
2. Add the workflows from this file
3. Make commits and watch them run
4. Set up a free MLflow server (or use `sqlite:///mlflow.db` locally)
5. Trigger a scheduled retrain
6. Add monitoring with Evidently
7. Push to your LinkedIn: "Built end-to-end MLOps pipeline with GitHub Actions + MLflow + DVC + Evidently"

When you can do all 7, you're hireable.

---

**End of File 2. Continue to 03_AI_API_Development_FastAPI.md.**
