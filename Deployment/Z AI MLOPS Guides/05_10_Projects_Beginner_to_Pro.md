# 10 Projects — Beginner to Pro

> "Theory without practice is decoration. Practice without theory is gambling. This file gives you both, in 10 graded projects."
>
> **How to use this file:** Build each project in order. Don't skip. Don't rush. Each one builds on the previous. By Project 10, you'll have a portfolio that gets you hired.

---

## Project Index

| # | Project | Level | Skills Mastered | Est. Time |
|---|---------|-------|-----------------|-----------|
| 1 | Iris Classifier API | Beginner | FastAPI basics, Pydantic, scikit-learn | 2 hours |
| 2 | Dockerize the API | Beginner | Docker, Dockerfile, image optimization | 2 hours |
| 3 | MLflow Tracking | Beginner | Experiment tracking, model registry | 3 hours |
| 4 | DVC Pipeline + CI | Intermediate | DVC, GitHub Actions, automated testing | 4 hours |
| 5 | Monitoring with Evidently | Intermediate | Drift detection, Prometheus, alerting | 4 hours |
| 6 | LLM API with Streaming | Intermediate | OpenAI-compatible API, SSE, async | 5 hours |
| 7 | K8s Deployment with Helm | Advanced | Kubernetes, Helm, Ingress, HPA | 6 hours |
| 8 | Multi-Model Serving | Advanced | Model registry, versioning, A/B routing | 5 hours |
| 9 | End-to-End MLOps | Advanced | Full pipeline, retraining triggers, drift | 8 hours |
| 10 | Production AI Platform | Pro | Auth, billing, canary, observability, scale | 10+ hours |

**Total estimated time: ~50 hours of focused work.** That's how you become hirable.

---

# Project 1 — Iris Classifier API (Beginner)

## Goal
Build your first ML API: a FastAPI service that classifies Iris flowers.

## Skills You'll Master
- FastAPI app structure
- Pydantic schemas
- Path operations
- Loading a scikit-learn model
- Testing with TestClient
- Auto-generated docs

## Architecture
```
Client → POST /predict → FastAPI → sklearn model → JSON response
```

## Step 1: Project Setup

```bash
mkdir p01-iris-api && cd p01-iris-api
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install fastapi uvicorn scikit-learn pydantic pytest httpx
pip freeze > requirements.txt
```

## Step 2: Train and Save a Model

```python
# train.py
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib

data = load_iris(as_frame=True)
X, y = data.data, data.target
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = RandomForestClassifier(n_estimators=100, max_depth=3, random_state=42)
model.fit(X_train, y_train)
print(f"Test accuracy: {model.score(X_test, y_test):.4f}")

joblib.dump(model, "model.pkl")
print("Saved model.pkl")
```

```bash
python train.py
# Test accuracy: 1.0000
# Saved model.pkl
```

## Step 3: The FastAPI App

```python
# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Literal
import joblib
import os

MODEL_PATH = os.environ.get("MODEL_PATH", "model.pkl")

app = FastAPI(
    title="Iris Classifier API",
    description="Classify Iris flowers from sepal/petal measurements.",
    version="1.0.0",
)

# Load model ONCE at import time
try:
    model = joblib.load(MODEL_PATH)
    species_names = ["setosa", "versicolor", "virginica"]
except Exception as e:
    model = None
    print(f"Failed to load model: {e}")

class IrisFeatures(BaseModel):
    sepal_length: float = Field(..., gt=0, lt=20, description="cm")
    sepal_width: float = Field(..., gt=0, lt=20, description="cm")
    petal_length: float = Field(..., gt=0, lt=20, description="cm")
    petal_width: float = Field(..., gt=0, lt=20, description="cm")

class PredictionResponse(BaseModel):
    species: str
    species_index: int
    probabilities: dict[str, float]
    model_version: str

@app.get("/health")
def health():
    return {"status": "ok" if model is not None else "loading"}

@app.post("/predict", response_model=PredictionResponse)
def predict(features: IrisFeatures):
    if model is None:
        raise HTTPException(503, "Model not loaded")
    
    X = [[features.sepal_length, features.sepal_width,
          features.petal_length, features.petal_width]]
    
    pred_idx = int(model.predict(X)[0])
    probas = model.predict_proba(X)[0]
    
    return PredictionResponse(
        species=species_names[pred_idx],
        species_index=pred_idx,
        probabilities={species_names[i]: float(p) for i, p in enumerate(probas)},
        model_version="v1.0",
    )

@app.get("/")
def root():
    return {"service": "Iris Classifier", "docs": "/docs"}
```

## Step 4: Run It

```bash
uvicorn main:app --reload
```

Open `http://localhost:8000/docs` — you'll see interactive Swagger UI. Click `/predict`, click "Try it out", fill in values, click "Execute".

## Step 5: Test It

```python
# test_main.py
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_predict():
    response = client.post("/predict", json={
        "sepal_length": 5.1,
        "sepal_width": 3.5,
        "petal_length": 1.4,
        "petal_width": 0.2,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["species"] == "setosa"
    assert 0 <= data["probabilities"]["setosa"] <= 1

def test_invalid_input():
    response = client.post("/predict", json={
        "sepal_length": -5,  # invalid
        "sepal_width": 3.5,
        "petal_length": 1.4,
        "petal_width": 0.2,
    })
    assert response.status_code == 422

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
```

```bash
pytest test_main.py -v
```

## Extension Ideas
- Add a `/predict/batch` endpoint
- Add input validation (e.g., sepal_length must be > petal_length * 0.5)
- Add a `/models` endpoint listing loaded models
- Add structured logging

## What You Built
A complete, testable, documented ML API. **First portfolio piece done.**

---

# Project 2 — Dockerize the API (Beginner)

## Goal
Package the Iris API in Docker. Anyone with Docker can run your API with one command.

## Skills You'll Master
- Dockerfile writing
- Image layering & caching
- Multi-stage builds
- `.dockerignore`
- Docker Compose for testing

## Step 1: Add a `.dockerignore`

```
# .dockerignore
__pycache__
*.pyc
.pytest_cache
venv/
.venv/
.env
*.md
.git
```

## Step 2: Write the Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl && rm -rf /var/lib/apt/lists/*

# Python deps (cached layer)
COPY requirements.txt .
RUN pip install -r requirements.txt

# App code
COPY main.py train.py ./

# Train model at build time (or COPY a pre-trained model)
RUN python train.py

# Non-root user
RUN useradd -m -u 1000 appuser
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Step 3: Build & Run

```bash
docker build -t iris-api:v1 .
docker run -p 8000:8000 iris-api:v1

# In another terminal
curl http://localhost:8000/health
curl -X POST http://localhost:8000/predict \
    -H "Content-Type: application/json" \
    -d '{"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}'
```

## Step 4: Multi-Stage Build (Smaller Image)

```dockerfile
# Stage 1: builder
FROM python:3.11-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: runtime
FROM python:3.11-slim AS runtime
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Install curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY main.py train.py ./
RUN python train.py

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t iris-api:v2 .
docker images | grep iris
# iris-api  v2  ... 280MB  (vs 410MB for v1)
```

## Step 5: Docker Compose for Testing

```yaml
# docker-compose.yml
version: "3.9"
services:
  api:
    build: .
    ports: ["8000:8000"]
    environment:
      - MODEL_PATH=/app/model.pkl
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s
      timeout: 3s
      retries: 5
```

```bash
docker compose up -d
docker compose ps
docker compose logs -f api
docker compose down
```

## Extension Ideas
- Add a PostgreSQL service to log predictions
- Add Redis for caching
- Tag with git SHA: `docker build -t iris-api:sha-$(git rev-parse --short HEAD) .`
- Push to Docker Hub

## What You Built
A reproducible, portable ML API container. Ship it anywhere.

---

# Project 3 — MLflow Tracking (Beginner)

## Goal
Add experiment tracking to your training. Track every model version, parameter, and metric.

## Skills You'll Master
- MLflow tracking
- MLflow model registry
- Model versioning & staging
- Serving models from MLflow
- MLflow UI

## Step 1: Install + Start MLflow Server

```bash
pip install mlflow
mlflow server --backend-store-uri sqlite:///mlflow.db --default-artifact-root ./mlruns --host 0.0.0.0 --port 5000
```

Open `http://localhost:5000`.

## Step 2: Tracked Training Script

```python
# train_tracked.py
import mlflow
import mlflow.sklearn
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import accuracy_score, f1_score
from mlflow.models import infer_signature

mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("iris-classification")

data = load_iris(as_frame=True)
X, y = data.data, data.target
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

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
                    "max_depth": str(max_d),
                    "min_samples_split": mss,
                    "random_state": 42,
                }
                mlflow.log_params(params)
                
                model = RandomForestClassifier(**{
                    "n_estimators": n_est,
                    "max_depth": max_d,
                    "min_samples_split": mss,
                    "random_state": 42,
                })
                model.fit(X_train, y_train)
                preds = model.predict(X_test)
                
                metrics = {
                    "accuracy": accuracy_score(y_test, preds),
                    "f1_macro": f1_score(y_test, preds, average="macro"),
                }
                mlflow.log_metrics(metrics)
                
                signature = infer_signature(X_train, model.predict(X_train))
                mlflow.sklearn.log_model(
                    model,
                    artifact_path="model",
                    signature=signature,
                    registered_model_name="iris-classifier",
                )
                
                print(f"{params} → {metrics}")
                if metrics["f1_macro"] > best_f1:
                    best_f1 = metrics["f1_macro"]
                    best_run_id = run.info.run_id

print(f"\nBest F1: {best_f1:.4f}, Run ID: {best_run_id}")
```

## Step 3: Promote Best Model to Production

```python
# promote.py
import mlflow

client = mlflow.tracking.MlflowClient()

# List all versions of iris-classifier
versions = client.search_model_versions("name='iris-classifier'")
for v in versions:
    print(f"v{v.version} stage={v.current_stage} run_id={v.run_id}")

# Find the best one (or hardcode from train_tracked.py output)
# For demo, promote v1 to Staging
client.transition_model_version_stage(
    name="iris-classifier",
    version=1,
    stage="Staging",
)

# Then to Production
client.transition_model_version_stage(
    name="iris-classifier",
    version=1,
    stage="Production",
    archive_existing_versions=True,
)
```

## Step 4: Serve from MLflow

```bash
mlflow models serve -m "models:/iris-classifier/Production" --port 5001 --host 0.0.0.0

# Test
curl -X POST http://localhost:5001/invocations \
    -H "Content-Type: application/json" \
    -d '{
        "dataframe_split": {
            "columns": ["sepal length (cm)", "sepal width (cm)", "petal length (cm)", "petal width (cm)"],
            "data": [[5.1, 3.5, 1.4, 0.2]]
        }
    }'
```

## Step 5: Load from Registry in FastAPI

```python
# main.py (updated)
import mlflow.sklearn
import os

MODEL_NAME = os.environ.get("MODEL_NAME", "iris-classifier")
MODEL_STAGE = os.environ.get("MODEL_STAGE", "Production")
MLFLOW_URI = os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5000")

mlflow.set_tracking_uri(MLFLOW_URI)

try:
    model = mlflow.sklearn.load_model(f"models:/{MODEL_NAME}/{MODEL_STAGE}")
    print(f"Loaded {MODEL_NAME}/{MODEL_STAGE}")
except Exception as e:
    print(f"Failed to load model: {e}")
    model = None
```

Now your API pulls the **current Production model** from MLflow. When you promote a new model, the API auto-uses it on restart (or with hot-reload — see File 3 Section 7).

## Extension Ideas
- Add a `/models/refresh` endpoint that hot-reloads
- Add model comparison view in UI
- Set up auto-promotion when F1 improves by X%
- Track training data hash alongside model

## What You Built
A versioned, registered, queryable model lifecycle. No more "where's the latest model?"

---

# Project 4 — DVC Pipeline + GitHub Actions CI (Intermediate)

## Goal
Build a reproducible ML pipeline with DVC and automate it with GitHub Actions.

## Skills You'll Master
- DVC data versioning
- DVC pipelines (`dvc.yaml`)
- GitHub Actions CI for ML
- Automated testing at 3 levels (code, data, model)
- Reproducible builds

## Step 1: Project Structure

```
p04-dvc-pipeline/
├── .github/workflows/ci.yml
├── data/
│   └── raw/
│       └── customers.csv (DVC-tracked)
├── src/
│   ├── prepare.py
│   ├── train.py
│   └── evaluate.py
├── tests/
│   ├── test_data.py
│   └── test_model.py
├── dvc.yaml
├── params.yaml
├── requirements.txt
└── README.md
```

## Step 2: Initialize DVC

```bash
git init
pip install dvc
dvc init
git commit -m "Initialize DVC"
```

## Step 3: Generate Synthetic Churn Data

```python
# generate_data.py
import pandas as pd
import numpy as np
import os

np.random.seed(42)
n = 5000

data = pd.DataFrame({
    "customer_id": [f"c{i}" for i in range(n)],
    "age": np.random.randint(18, 80, n),
    "monthly_spend": np.random.exponential(100, n).round(2),
    "tenure_months": np.random.randint(1, 60, n),
    "support_tickets": np.random.poisson(2, n),
    "plan_type": np.random.choice(["free", "basic", "pro"], n, p=[0.3, 0.4, 0.3]),
})

# Create churn label with some signal
churn_prob = (
    0.1
    + 0.3 * (data["support_tickets"] > 5)
    + 0.2 * (data["tenure_months"] < 6)
    + 0.15 * (data["plan_type"] == "free")
    - 0.1 * (data["monthly_spend"] > 200)
)
data["churn"] = (np.random.random(n) < churn_prob).astype(int)

os.makedirs("data/raw", exist_ok=True)
data.to_csv("data/raw/customers.csv", index=False)
print(f"Generated {len(data)} rows, churn rate: {data['churn'].mean():.3f}")

# Track with DVC
# Run: dvc add data/raw/customers.csv
```

```bash
python generate_data.py
dvc add data/raw/customers.csv
git add data/raw/customers.csv.dvc .gitignore
git commit -m "Add customers.csv v1"
```

## Step 4: Pipeline Stages

```python
# src/prepare.py
import argparse
import pandas as pd
from sklearn.model_selection import train_test_split
import os
import yaml

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", default="data/raw/customers.csv")
    parser.add_argument("--out", default="data/processed")
    parser.add_argument("--params", default="params.yaml")
    args = parser.parse_args()
    
    with open(args.params) as f:
        params = yaml.safe_load(f)
    
    os.makedirs(args.out, exist_ok=True)
    df = pd.read_csv(args.raw)
    
    # Encode plan_type
    df = pd.get_dummies(df, columns=["plan_type"], drop_first=True)
    
    train, test = train_test_split(
        df, test_size=params["prepare"]["test_size"],
        random_state=params["seed"], stratify=df["churn"]
    )
    train.to_csv(os.path.join(args.out, "train.csv"), index=False)
    test.to_csv(os.path.join(args.out, "test.csv"), index=False)
    print(f"Train: {len(train)}, Test: {len(test)}")

if __name__ == "__main__":
    main()
```

```python
# src/train.py
import argparse
import pandas as pd
import pickle
import yaml
from sklearn.ensemble import RandomForestClassifier

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", default="data/processed/train.csv")
    parser.add_argument("--out", default="models/model.pkl")
    parser.add_argument("--params", default="params.yaml")
    args = parser.parse_args()
    
    with open(args.params) as f:
        params = yaml.safe_load(f)
    
    train_params = params["train"]
    df = pd.read_csv(args.train)
    X = df.drop(columns=["customer_id", "churn"])
    y = df["churn"]
    
    model = RandomForestClassifier(
        n_estimators=train_params["n_estimators"],
        max_depth=train_params["max_depth"],
        random_state=params["seed"],
        n_jobs=-1,
    )
    model.fit(X, y)
    
    import os
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "wb") as f:
        pickle.dump(model, f)
    print(f"Saved {args.out}")
    # Save feature names too
    with open(args.out + ".features.json", "w") as f:
        import json
        json.dump(list(X.columns), f)

if __name__ == "__main__":
    main()
```

```python
# src/evaluate.py
import argparse
import pandas as pd
import pickle
import json
import os
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score, confusion_matrix

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="models/model.pkl")
    parser.add_argument("--test", default="data/processed/test.csv")
    parser.add_argument("--out", default="metrics/eval.json")
    args = parser.parse_args()
    
    with open(args.model, "rb") as f:
        model = pickle.load(f)
    
    df = pd.read_csv(args.test)
    X = df.drop(columns=["customer_id", "churn"])
    y = df["churn"]
    preds = model.predict(X)
    probas = model.predict_proba(X)[:, 1]
    
    metrics = {
        "accuracy": float(accuracy_score(y, preds)),
        "f1": float(f1_score(y, preds)),
        "auc": float(roc_auc_score(y, probas)),
        "confusion_matrix": confusion_matrix(y, preds).tolist(),
    }
    
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(metrics, f, indent=2)
    print(json.dumps(metrics, indent=2))

if __name__ == "__main__":
    main()
```

## Step 5: params.yaml

```yaml
# params.yaml
seed: 42

prepare:
  test_size: 0.2

train:
  n_estimators: 200
  max_depth: 8
```

## Step 6: dvc.yaml

```yaml
# dvc.yaml
stages:
  prepare:
    cmd: python src/prepare.py --raw data/raw/customers.csv --out data/processed --params params.yaml
    deps:
      - src/prepare.py
      - data/raw/customers.csv
      - params.yaml
    outs:
      - data/processed/train.csv
      - data/processed/test.csv
  
  train:
    cmd: python src/train.py --train data/processed/train.csv --out models/model.pkl --params params.yaml
    deps:
      - src/train.py
      - data/processed/train.csv
      - params.yaml
    outs:
      - models/model.pkl
  
  evaluate:
    cmd: python src/evaluate.py --model models/model.pkl --test data/processed/test.csv --out metrics/eval.json
    deps:
      - src/evaluate.py
      - models/model.pkl
      - data/processed/test.csv
    metrics:
      - metrics/eval.json:
          cache: false
```

## Step 7: Run the Pipeline

```bash
dvc repro
# Runs prepare → train → evaluate
dvc metrics show
# accuracy  f1  auc
cat metrics/eval.json
```

## Step 8: Tests

```python
# tests/test_data.py
import pandas as pd
import pytest

def test_data_schema():
    df = pd.read_csv("data/raw/customers.csv")
    required = {"customer_id", "age", "monthly_spend", "tenure_months", "support_tickets", "plan_type", "churn"}
    assert required.issubset(df.columns)

def test_no_nulls():
    df = pd.read_csv("data/raw/customers.csv")
    assert df.isnull().sum().sum() == 0

def test_churn_balance():
    df = pd.read_csv("data/raw/customers.csv")
    rate = df["churn"].mean()
    assert 0.1 < rate < 0.6, f"Unexpected churn rate: {rate}"
```

```python
# tests/test_model.py
import pandas as pd
import pickle
import json
import pytest

@pytest.fixture
def model():
    with open("models/model.pkl", "rb") as f:
        return pickle.load(f)

def test_model_exists():
    import os
    assert os.path.exists("models/model.pkl")

def test_accuracy_above_threshold():
    with open("metrics/eval.json") as f:
        m = json.load(f)
    assert m["accuracy"] >= 0.7, f"Accuracy {m['accuracy']} below 0.7"

def test_f1_above_threshold():
    with open("metrics/eval.json") as f:
        m = json.load(f)
    assert m["f1"] >= 0.5, f"F1 {m['f1']} below 0.5"

def test_model_predicts(model):
    df = pd.read_csv("data/processed/test.csv")
    X = df.drop(columns=["customer_id", "churn"]).iloc[:5]
    preds = model.predict(X)
    assert len(preds) == 5
    assert set(preds).issubset({0, 1})
```

## Step 9: GitHub Actions CI

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip
      - run: pip install -r requirements.txt
      - run: pip install pytest
      
      - name: Lint
        run: |
          pip install black ruff
          black --check .
          ruff check .
      
      - name: Reproduce pipeline
        run: dvc repro
      
      - name: Run tests
        run: pytest tests/ -v
      
      - name: Show metrics
        run: dvc metrics show
```

## Step 10: requirements.txt

```
dvc>=3.50.0
scikit-learn>=1.4.0
pandas>=2.0.0
pyyaml>=6.0
pytest>=8.0.0
```

## Extension Ideas
- Add S3 as DVC remote (`dvc remote add -d storage s3://my-bucket/dvc`)
- Schedule a weekly retraining with a separate workflow
- Add model registration to MLflow after training
- Add a Slack notification with metrics

## What You Built
A reproducible, tested, CI-driven ML pipeline. This is **Level 1 MLOps**.

---

# Project 5 — Monitoring with Evidently (Intermediate)

## Goal
Add drift detection + alerting to your ML service. Detect when production input distribution shifts from training.

## Skills You'll Master
- Evidently drift reports
- Prometheus custom metrics
- Alerting rules
- Grafana dashboards
- Continuous Monitoring (CM)

## Step 1: Install

```bash
pip install evidently prometheus-client fastapi uvicorn
```

## Step 2: Reference vs Current Data

```python
# monitoring/drift_check.py
import pandas as pd
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset, TargetDriftPreset, RegressionPreset
import json
import os

REFERENCE_PATH = "data/reference.csv"
CURRENT_PATH = "data/current.csv"
REPORT_PATH = "reports/drift_report.html"

def check_drift():
    reference = pd.read_csv(REFERENCE_PATH)
    current = pd.read_csv(CURRENT_PATH)
    
    report = Report(metrics=[DataDriftPreset()])
    report.run(reference_data=reference, current_data=current)
    
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    report.save_html(REPORT_PATH)
    
    # Programmatic check
    result = report.as_dict()
    drift_detected = result["metrics"][0]["result"]["dataset_drift"]
    drift_share = result["metrics"][0]["result"]["drift_share"]
    
    print(f"Dataset drift: {drift_detected}")
    print(f"Drifted columns share: {drift_share:.2%}")
    
    # Per-column drift
    for col, info in result["metrics"][0]["result"]["drift_by_columns"].items():
        if info["drift_detected"]:
            print(f"  ⚠️  {col} drifted (method={info['method']}, p_value={info['p_value']:.4f})")
    
    return drift_detected, drift_share

if __name__ == "__main__":
    check_drift()
```

## Step 3: Generate Drifted Data to Test

```python
# generate_drifted_data.py
import pandas as pd
import numpy as np

# Reference: same as training data
ref = pd.read_csv("data/raw/customers.csv")
ref_sample = ref.sample(1000, random_state=42)
ref_sample.to_csv("data/reference.csv", index=False)

# Current: artificially drifted (age shifted up, monthly_spend up)
np.random.seed(99)
current = ref.sample(1000, random_state=99).copy()
current["age"] = current["age"] + np.random.normal(15, 5, len(current))  # shift +15
current["monthly_spend"] = current["monthly_spend"] * 1.5  # 50% increase
current.to_csv("data/current.csv", index=False)

print("Generated reference + drifted current")
```

## Step 4: FastAPI App with Metrics

```python
# main.py
import time
import random
from collections import defaultdict
from fastapi import FastAPI, Request
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import pandas as pd

app = FastAPI()

# Metrics
REQUEST_COUNT = Counter("predictions_total", "Total predictions", ["endpoint"])
REQUEST_LATENCY = Histogram("prediction_latency_seconds", "Latency")
FEATURE_AGE = Histogram("feature_age", "Age distribution", buckets=[18, 30, 40, 50, 60, 70, 80])
FEATURE_SPEND = Histogram("feature_monthly_spend", "Spend distribution", buckets=[0, 50, 100, 200, 500, 1000])
DRIFT_SCORE = Gauge("drift_score", "Latest drift score")

class Features(BaseModel):
    age: int
    monthly_spend: float
    tenure_months: int
    support_tickets: int

@app.post("/predict")
async def predict(features: Features):
    start = time.time()
    
    # Record feature distributions
    FEATURE_AGE.observe(features.age)
    FEATURE_SPEND.observe(features.monthly_spend)
    
    # Mock prediction
    prob = 0.3 + 0.05 * features.support_tickets
    if features.tenure_months < 6:
        prob += 0.2
    prob = min(prob, 0.95)
    
    REQUEST_COUNT.labels(endpoint="/predict").inc()
    REQUEST_LATENCY.observe(time.time() - start)
    
    return {"churn_probability": prob}

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
```

## Step 5: Drift Detection Service

```python
# monitoring/drift_service.py
import requests
import time
import os
from prometheus_client import Gauge, start_http_server
import pandas as pd
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset

DRIFT_GAUGE = Gauge("ml_drift_score", "Drift score (0-1)")
DRIFT_DETECTED = Gauge("ml_drift_detected", "1 if drift detected")

def fetch_recent_predictions(n=1000):
    """Query Prometheus for recent feature observations."""
    # In real life: query Prometheus range vector for feature_age_bucket etc.
    # For demo: just read current.csv
    return pd.read_csv("data/current.csv")

def compute_drift():
    reference = pd.read_csv("data/reference.csv")
    current = fetch_recent_predictions()
    
    report = Report(metrics=[DataDriftPreset()])
    report.run(reference_data=reference, current_data=current)
    result = report.as_dict()
    
    drift_share = result["metrics"][0]["result"]["drift_share"]
    drift_detected = int(result["metrics"][0]["result"]["dataset_drift"])
    
    DRIFT_GAUGE.set(drift_share)
    DRIFT_DETECTED.set(drift_detected)
    
    return drift_share, drift_detected

if __name__ == "__main__":
    start_http_server(9091)  # expose metrics on :9091
    print("Drift service on :9091/metrics")
    
    while True:
        try:
            score, detected = compute_drift()
            print(f"Drift score: {score:.3f}, detected: {detected}")
            if detected:
                # Alert (Slack webhook, PagerDuty, etc.)
                print("🚨 DRIFT DETECTED")
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(60)
```

## Step 6: Prometheus Config

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: api
    static_configs:
      - targets: ["host.docker.internal:8000"]
  - job_name: drift
    static_configs:
      - targets: ["host.docker.internal:9091"]
  
  # Alert rules
rule_files:
  - alerts.yml
```

```yaml
# alerts.yml
groups:
  - name: ml
    rules:
      - alert: HighDrift
        expr: ml_drift_detected == 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "ML drift detected"
          description: "Drift score is {{ $value }}"
      
      - alert: HighLatency
        expr: histogram_quantile(0.99, rate(prediction_latency_seconds_bucket[5m])) > 1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "p99 latency > 1s"
```

## Step 7: Run Everything

```bash
# Terminal 1: API
uvicorn main:app --port 8000

# Terminal 2: Drift service
python monitoring/drift_service.py

# Terminal 3: Prometheus
prometheus --config.file=prometheus.yml

# Generate test traffic
python -c "
import requests, random
for _ in range(1000):
    requests.post('http://localhost:8000/predict', json={
        'age': random.randint(18, 80),
        'monthly_spend': random.uniform(0, 500),
        'tenure_months': random.randint(1, 60),
        'support_tickets': random.randint(0, 10),
    })
"
```

Open Prometheus at `http://localhost:9090`, query `ml_drift_score` and `prediction_latency_seconds_bucket`.

## Extension Ideas
- Add alert routing to PagerDuty
- Auto-trigger retraining when drift detected (call your DVC pipeline)
- Add data quality checks (nulls, schema violations)
- Add per-feature drift dashboards in Grafana

## What You Built
Continuous monitoring with auto-alerting. **You now have Level 1.5 MLOps.**

---

# Project 6 — LLM API with Streaming (Intermediate)

## Goal
Build an OpenAI-compatible LLM API with streaming, token counting, and concurrency control.

## Skills You'll Master
- OpenAI-compatible API design
- Server-Sent Events (SSE)
- Async/await with HTTPX
- Token counting (tiktoken)
- GPU resource management
- Bearer token auth

## Step 1: Setup

```bash
pip install fastapi uvicorn httpx tiktoken pydantic python-multipart
```

## Step 2: OpenAI-Compatible Schemas

```python
# schemas.py
from pydantic import BaseModel, Field
from typing import Literal, Optional, Union
from enum import Enum

class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: Optional[str] = None
    name: Optional[str] = None
    tool_calls: Optional[list] = None

class ChatCompletionRequest(BaseModel):
    model: str = "gpt-3.5-turbo"
    messages: list[ChatMessage]
    temperature: float = Field(1.0, ge=0, le=2)
    top_p: float = Field(1.0, ge=0, le=1)
    n: int = Field(1, ge=1, le=10)
    stream: bool = False
    stop: Optional[Union[str, list[str]]] = None
    max_tokens: Optional[int] = Field(None, ge=1)
    presence_penalty: float = Field(0, ge=-2, le=2)
    frequency_penalty: float = Field(0, ge=-2, le=2)
    user: Optional[str] = None

class Choice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: Optional[str] = None

class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class ChatCompletionResponse(BaseModel):
    id: str
    object: Literal["chat.completion"] = "chat.completion"
    created: int
    model: str
    choices: list[Choice]
    usage: Usage

class DeltaChoice(BaseModel):
    index: int
    delta: dict
    finish_reason: Optional[str] = None

class ChatCompletionChunk(BaseModel):
    id: str
    object: Literal["chat.completion.chunk"] = "chat.completion.chunk"
    created: int
    model: str
    choices: list[DeltaChoice]
```

## Step 3: LLM Backend

```python
# llm_backend.py
import os
import httpx
from typing import AsyncGenerator

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_BASE_URL = "https://api.openai.com/v1"

async def call_openai(messages: list[dict], model: str, temperature: float, stream: bool, max_tokens: Optional[int] = None):
    """Proxy to OpenAI (or any OpenAI-compatible API)."""
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "stream": stream,
    }
    if max_tokens:
        payload["max_tokens"] = max_tokens
    
    if stream:
        return stream_openai(payload, headers)
    else:
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(f"{OPENAI_BASE_URL}/chat/completions", json=payload, headers=headers)
            r.raise_for_status()
            return r.json()

async def stream_openai(payload, headers) -> AsyncGenerator[str, None]:
    async with httpx.AsyncClient(timeout=120) as client:
        async with client.stream("POST", f"{OPENAI_BASE_URL}/chat/completions", json=payload, headers=headers) as r:
            r.raise_for_status()
            async for line in r.aiter_lines():
                if line.startswith("data: "):
                    yield line + "\n\n"
```

## Step 4: Token Counter

```python
# tokens.py
import tiktoken

# Cache encoders per model
_encoders = {}

def get_encoder(model: str):
    if model not in _encoders:
        try:
            _encoders[model] = tiktoken.encoding_for_model(model)
        except KeyError:
            _encoders[model] = tiktoken.get_encoding("cl100k_base")
    return _encoders[model]

def count_tokens(text: str, model: str = "gpt-3.5-turbo") -> int:
    return len(get_encoder(model).encode(text))

def count_messages_tokens(messages: list[dict], model: str = "gpt-3.5-turbo") -> int:
    """Approximate tokens for a messages list (OpenAI's formula)."""
    enc = get_encoder(model)
    tokens_per_message = 4  # role + content overhead
    num_tokens = 0
    for msg in messages:
        num_tokens += tokens_per_message
        for key, value in msg.items():
            num_tokens += len(enc.encode(str(value)))
            if key == "name":
                num_tokens += -1  # name saves a token
    num_tokens += 2  # assistant priming
    return num_tokens
```

## Step 5: FastAPI App

```python
# main.py
import asyncio
import json
import time
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from typing import Optional

from schemas import (
    ChatCompletionRequest, ChatCompletionResponse, ChatCompletionChunk,
    Choice, Usage, ChatMessage
)
from llm_backend import call_openai
from tokens import count_tokens, count_messages_tokens

# In-memory API key store (use DB in production)
VALID_KEYS = {"demo-key-123": {"name": "Demo", "tier": "free"}}

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    if credentials.credentials not in VALID_KEYS:
        raise HTTPException(401, "Invalid API key")
    return VALID_KEYS[credentials.credentials]

# Concurrency limiter (e.g., to limit GPU usage)
MAX_CONCURRENT = 10
semaphore = asyncio.Semaphore(MAX_CONCURRENT)

app = FastAPI(title="LLM API Gateway", version="1.0.0")

@app.post("/v1/chat/completions")
async def chat_completion(
    req: ChatCompletionRequest,
    client = Depends(verify_token),
):
    async with semaphore:
        messages = [m.model_dump(exclude_none=True) for m in req.messages]
        prompt_tokens = count_messages_tokens(messages, req.model)
        
        if req.stream:
            return StreamingResponse(
                stream_response(req, messages, prompt_tokens),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                },
            )
        
        # Non-streaming
        response = await call_openai(
            messages=messages,
            model=req.model,
            temperature=req.temperature,
            stream=False,
            max_tokens=req.max_tokens,
        )
        
        # Transform to our format
        completion_id = f"chatcmpl-{uuid.uuid4().hex[:29]}"
        return ChatCompletionResponse(
            id=completion_id,
            created=int(time.time()),
            model=req.model,
            choices=[
                Choice(
                    index=i,
                    message=ChatMessage(role="assistant", content=c["message"]["content"]),
                    finish_reason=c.get("finish_reason"),
                )
                for i, c in enumerate(response["choices"])
            ],
            usage=Usage(
                prompt_tokens=response["usage"]["prompt_tokens"],
                completion_tokens=response["usage"]["completion_tokens"],
                total_tokens=response["usage"]["total_tokens"],
            ),
        )

async def stream_response(req: ChatCompletionRequest, messages: list[dict], prompt_tokens: int):
    """Forward OpenAI stream and append usage at end."""
    completion_id = f"chatcmpl-{uuid.uuid4().hex[:29]}"
    created = int(time.time())
    completion_tokens = 0
    
    try:
        async for line in call_openai(
            messages=messages,
            model=req.model,
            temperature=req.temperature,
            stream=True,
            max_tokens=req.max_tokens,
        ):
            # Forward as-is, but rewrite id/created for consistency
            if line.startswith("data: ") and "[DONE]" not in line:
                try:
                    data = json.loads(line[6:])
                    data["id"] = completion_id
                    data["created"] = created
                    # Count tokens
                    if data["choices"] and data["choices"][0]["delta"].get("content"):
                        completion_tokens += count_tokens(data["choices"][0]["delta"]["content"], req.model)
                    yield f"data: {json.dumps(data)}\n\n"
                except json.JSONDecodeError:
                    yield line
            else:
                yield line
        
        # Final chunk with usage
        final = {
            "id": completion_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": req.model,
            "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            },
        }
        yield f"data: {json.dumps(final)}\n\n"
        yield "data: [DONE]\n\n"
    except Exception as e:
        error_chunk = {
            "error": {"message": str(e), "type": "internal_error"},
        }
        yield f"data: {json.dumps(error_chunk)}\n\n"

@app.get("/v1/models")
async def list_models(client = Depends(verify_token)):
    return {
        "object": "list",
        "data": [
            {"id": "gpt-3.5-turbo", "object": "model", "owned_by": "openai"},
            {"id": "gpt-4", "object": "model", "owned_by": "openai"},
            {"id": "gpt-4-turbo", "object": "model", "owned_by": "openai"},
        ],
    }

@app.get("/health")
def health():
    return {"status": "ok"}
```

## Step 6: Test It

```bash
export OPENAI_API_KEY=sk-...
uvicorn main:app --reload

# Non-streaming
curl -X POST http://localhost:8000/v1/chat/completions \
    -H "Authorization: Bearer demo-key-123" \
    -H "Content-Type: application/json" \
    -d '{
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "Say hello in 3 words"}]
    }'

# Streaming
curl -X POST http://localhost:8000/v1/chat/completions \
    -H "Authorization: Bearer demo-key-123" \
    -H "Content-Type: application/json" \
    -N \
    -d '{
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "Write a haiku about Python"}],
        "stream": true
    }'
```

The `-N` flag disables curl buffering — you'll see tokens stream in real time.

## Step 7: OpenAI SDK Compatibility Test

```python
# test_openai_compat.py
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="demo-key-123",
)

# Non-streaming
resp = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Hello!"}],
)
print(resp.choices[0].message.content)
print(f"Tokens: {resp.usage.total_tokens}")

# Streaming
stream = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Count 1 to 10"}],
    stream=True,
)
for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
print()
```

If this works, you've built a drop-in OpenAI replacement. Clients can swap `base_url` and use your service.

## Extension Ideas
- Add rate limiting per API key
- Add a /v1/embeddings endpoint
- Add fallback: if OpenAI fails, route to Anthropic
- Add cost tracking per user
- Add a streaming cancellation endpoint

## What You Built
A production-grade LLM API gateway. **Charge for it and you have a business.**

---

# Project 7 — K8s Deployment with Helm (Advanced)

## Goal
Deploy your ML API to Kubernetes with a Helm chart, complete with HPA, Ingress, TLS, and observability.

## Skills You'll Master
- Helm chart authoring
- K8s deployment patterns
- Ingress + cert-manager
- HPA + resource limits
- Prometheus annotations

## Step 1: Prerequisites

Install locally:
- Docker Desktop (with Kubernetes enabled) OR `kind` OR `minikube`
- `kubectl`
- `helm`
- `openssl` (for self-signed certs in dev)

```bash
# Verify
kubectl get nodes
helm version
```

## Step 2: Chart Structure

```
ml-api-chart/
├── Chart.yaml
├── values.yaml
├── values-dev.yaml
├── values-prod.yaml
└── templates/
    ├── _helpers.tpl
    ├── deployment.yaml
    ├── service.yaml
    ├── configmap.yaml
    ├── secret.yaml
    ├── hpa.yaml
    ├── ingress.yaml
    ├── serviceaccount.yaml
    └── tests/
        └── test-connection.yaml
```

## Step 3: Chart.yaml

```yaml
apiVersion: v2
name: ml-api
description: ML inference API
type: application
version: 1.0.0
appVersion: "2.3.0"
maintainers:
  - name: ML Team
```

## Step 4: values.yaml

```yaml
replicaCount: 3

image:
  repository: myuser/ml-api
  tag: ""
  pullPolicy: IfNotPresent

nameOverride: ""
fullnameOverride: ""

serviceAccount:
  create: true
  annotations: {}
  name: ""

podAnnotations:
  prometheus.io/scrape: "true"
  prometheus.io/port: "8000"
  prometheus.io/path: "/metrics"

podSecurityContext:
  fsGroup: 1000

securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false
  capabilities:
    drop: ["ALL"]

service:
  type: ClusterIP
  port: 80
  targetPort: 8000

ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/rate-limit: "100"
  host: api.example.com
  tls: true

resources:
  requests:
    cpu: 250m
    memory: 512Mi
  limits:
    cpu: 1000m
    memory: 1Gi

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 20
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80

env:
  LOG_LEVEL: INFO
  MODEL_NAME: churn-prediction
  MODEL_STAGE: Production

secrets:
  mlflowUri: ""
  databaseUrl: ""

probes:
  liveness:
    path: /health/live
    initialDelaySeconds: 30
  readiness:
    path: /health/ready
    initialDelaySeconds: 30

nodeSelector: {}
tolerations: []
affinity: {}
```

## Step 5: values-prod.yaml

```yaml
replicaCount: 5

resources:
  requests:
    cpu: 500m
    memory: 1Gi
  limits:
    cpu: 2000m
    memory: 2Gi

autoscaling:
  enabled: true
  minReplicas: 5
  maxReplicas: 50
  targetCPUUtilizationPercentage: 65

ingress:
  host: api.prod.example.com
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/rate-limit: "1000"
    nginx.ingress.kubernetes.io/proxy-body-size: "50m"
```

## Step 6: templates/_helpers.tpl

```yaml
{{/*
Expand the name of the chart.
*/}}
{{- define "ml-api.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Fully qualified app name.
*/}}
{{- define "ml-api.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "ml-api.labels" -}}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
{{ include "ml-api.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "ml-api.selectorLabels" -}}
app.kubernetes.io/name: {{ include "ml-api.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
```

## Step 7: templates/deployment.yaml

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "ml-api.fullname" . }}
  labels:
    {{- include "ml-api.labels" . | nindent 4 }}
spec:
  {{- if not .Values.autoscaling.enabled }}
  replicas: {{ .Values.replicaCount }}
  {{- end }}
  selector:
    matchLabels:
      {{- include "ml-api.selectorLabels" . | nindent 6 }}
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 0
      maxSurge: 1
  template:
    metadata:
      annotations:
        {{- with .Values.podAnnotations }}
        {{- toYaml . | nindent 8 }}
        {{- end }}
      labels:
        {{- include "ml-api.selectorLabels" . | nindent 8 }}
    spec:
      serviceAccountName: {{ include "ml-api.fullname" . }}
      securityContext:
        {{- toYaml .Values.podSecurityContext | nindent 8 }}
      containers:
        - name: {{ .Chart.Name }}
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          ports:
            - name: http
              containerPort: {{ .Values.service.targetPort }}
              protocol: TCP
          envFrom:
            - configMapRef:
                name: {{ include "ml-api.fullname" . }}
            - secretRef:
                name: {{ include "ml-api.fullname" . }}
          livenessProbe:
            httpGet:
              path: {{ .Values.probes.liveness.path }}
              port: http
            initialDelaySeconds: {{ .Values.probes.liveness.initialDelaySeconds }}
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: {{ .Values.probes.readiness.path }}
              port: http
            initialDelaySeconds: {{ .Values.probes.readiness.initialDelaySeconds }}
            periodSeconds: 5
          startupProbe:
            httpGet:
              path: {{ .Values.probes.liveness.path }}
              port: http
            failureThreshold: 30
            periodSeconds: 10
          resources:
            {{- toYaml .Values.resources | nindent 12 }}
          securityContext:
            {{- toYaml .Values.securityContext | nindent 12 }}
          volumeMounts:
            - name: tmp
              mountPath: /tmp
      volumes:
        - name: tmp
          emptyDir: {}
      {{- with .Values.nodeSelector }}
      nodeSelector:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.tolerations }}
      tolerations:
        {{- toYaml . | nindent 8 }}
      {{- end }}
```

## Step 8: Other Templates

```yaml
# templates/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ include "ml-api.fullname" . }}
  labels:
    {{- include "ml-api.labels" . | nindent 4 }}
spec:
  type: {{ .Values.service.type }}
  ports:
    - port: {{ .Values.service.port }}
      targetPort: http
      protocol: TCP
      name: http
  selector:
    {{- include "ml-api.selectorLabels" . | nindent 4 }}
```

```yaml
# templates/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "ml-api.fullname" . }}
  labels:
    {{- include "ml-api.labels" . | nindent 4 }}
data:
  {{- range $k, $v := .Values.env }}
  {{ $k }}: {{ $v | quote }}
  {{- end }}
```

```yaml
# templates/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: {{ include "ml-api.fullname" . }}
  labels:
    {{- include "ml-api.labels" . | nindent 4 }}
type: Opaque
stringData:
  {{- range $k, $v := .Values.secrets }}
  {{ $k }}: {{ $v | quote }}
  {{- end }}
```

```yaml
# templates/hpa.yaml
{{- if .Values.autoscaling.enabled }}
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {{ include "ml-api.fullname" . }}
  labels:
    {{- include "ml-api.labels" . | nindent 4 }}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {{ include "ml-api.fullname" . }}
  minReplicas: {{ .Values.autoscaling.minReplicas }}
  maxReplicas: {{ .Values.autoscaling.maxReplicas }}
  metrics:
    {{- if .Values.autoscaling.targetCPUUtilizationPercentage }}
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: {{ .Values.autoscaling.targetCPUUtilizationPercentage }}
    {{- end }}
    {{- if .Values.autoscaling.targetMemoryUtilizationPercentage }}
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: {{ .Values.autoscaling.targetMemoryUtilizationPercentage }}
    {{- end }}
{{- end }}
```

```yaml
# templates/ingress.yaml
{{- if .Values.ingress.enabled }}
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {{ include "ml-api.fullname" . }}
  labels:
    {{- include "ml-api.labels" . | nindent 4 }}
  {{- with .Values.ingress.annotations }}
  annotations:
    {{- toYaml . | nindent 4 }}
  {{- end }}
spec:
  ingressClassName: {{ .Values.ingress.className }}
  {{- if .Values.ingress.tls }}
  tls:
    - hosts:
        - {{ .Values.ingress.host }}
      secretName: {{ include "ml-api.fullname" . }}-tls
  {{- end }}
  rules:
    - host: {{ .Values.ingress.host }}
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: {{ include "ml-api.fullname" . }}
                port:
                  number: {{ .Values.service.port }}
{{- end }}
```

```yaml
# templates/serviceaccount.yaml
{{- if .Values.serviceAccount.create }}
apiVersion: v1
kind: ServiceAccount
metadata:
  name: {{ include "ml-api.fullname" . }}
  labels:
    {{- include "ml-api.labels" . | nindent 4 }}
  {{- with .Values.serviceAccount.annotations }}
  annotations:
    {{- toYaml . | nindent 4 }}
  {{- end }}
{{- end }}
```

## Step 9: Install Prerequisites

```bash
# Nginx ingress
helm install ingress-nginx ingress-nginx/ingress-nginx \
    --namespace ingress-nginx --create-namespace

# cert-manager
helm install cert-manager jetstack/cert-manager \
    --namespace cert-manager --create-namespace \
    --set installCRDs=true

# Prometheus stack
helm install monitoring prometheus-community/kube-prometheus-stack \
    --namespace monitoring --create-namespace \
    --set grafana.adminPassword=admin
```

## Step 10: Deploy Your Chart

```bash
# Lint first
helm lint ./ml-api-chart

# Dry-run (template only)
helm template ml-api ./ml-api-chart -f values-dev.yaml

# Install
helm install ml-api ./ml-api-chart -f values-dev.yaml

# Check
kubectl get pods,svc,ingress,hpa

# Test the service
kubectl port-forward svc/ml-api 8080:80
curl http://localhost:8080/health/live

# Upgrade
helm upgrade ml-api ./ml-api-chart -f values-prod.yaml

# Rollback
helm history ml-api
helm rollback ml-api 1

# Uninstall
helm uninstall ml-api
```

## Step 11: Load Test + Watch HPA Scale

```bash
# Install hey (load tester)
go install github.com/rakyll/hey@latest

# Generate load
hey -z 5m -c 50 -m POST -H "Content-Type: application/json" \
    -d '{"age":35,"monthly_spend":100,"tenure_months":12,"support_tickets":2}' \
    http://localhost:8080/predict

# In another terminal, watch HPA
kubectl get hpa -w
```

You'll see replicas scale from 3 → 5 → 10 → ... as CPU climbs, then back down.

## Extension Ideas
- Add a PodDisruptionBudget for HA during node maintenance
- Add network policies for zero-trust
- Add a canary release with Argo Rollouts
- Add ServiceMonitor for Prometheus auto-discovery

## What You Built
A production-grade K8s deployment. This is **what real companies run**.

---

# Project 8 — Multi-Model Serving with A/B Testing (Advanced)

## Goal
Serve multiple model versions simultaneously, route traffic via A/B test, and switch to the winner.

## Skills You'll Master
- Model registry operations
- Multi-version serving
- A/B test routing
- Traffic splitting with Ingress
- Champion-challenger pattern

## Step 1: Architecture

```
                ┌──────────────────┐
                │   Load Balancer  │
                └────────┬─────────┘
                         │
              ┌──────────┴──────────┐
              │                     │
    ┌─────────▼──────┐    ┌─────────▼──────┐
    │  v1 (Champion) │    │  v2 (Challenger)│
    │  Service        │    │  Service        │
    └────────────────┘    └────────────────┘
              │                     │
              └──────────┬──────────┘
                         │
                ┌────────▼─────────┐
                │  Analytics DB    │
                │  (predictions +  │
                │   outcomes)      │
                └──────────────────┘
```

## Step 2: Two Model Versions

```python
# train_v1.py — old model
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split

data = load_iris(as_frame=True)
X, y = data.data, data.target
X_train, _, y_train, _ = train_test_split(X, y, test_size=0.2, random_state=42)

model = RandomForestClassifier(n_estimators=10, max_depth=3, random_state=42)
model.fit(X_train, y_train)
joblib.dump(model, "models/v1.pkl")
print("Trained v1 (small RF)")
```

```python
# train_v2.py — new model (more estimators)
import joblib
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split

data = load_iris(as_frame=True)
X, y = data.data, data.target
X_train, _, y_train, _ = train_test_split(X, y, test_size=0.2, random_state=42)

model = GradientBoostingClassifier(n_estimators=100, max_depth=3, random_state=42)
model.fit(X_train, y_train)
joblib.dump(model, "models/v2.pkl")
print("Trained v2 (GBM)")
```

## Step 3: API with Version Routing

```python
# main.py
import os
import joblib
import random
import json
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
import redis
import uuid
from datetime import datetime

r = redis.Redis(host=os.environ.get("REDIS_HOST", "localhost"), decode_responses=True)

# Load both models
models = {
    "v1": joblib.load("models/v1.pkl"),
    "v2": joblib.load("models/v2.pkl"),
}
species = ["setosa", "versicolor", "virginica"]

# A/B test config: 80% v1, 20% v2
TRAFFIC_SPLIT = {"v1": 0.8, "v2": 0.2}

app = FastAPI()

class Features(BaseModel):
    sepal_length: float
    sepal_width: float
    petal_length: float
    petal_width: float
    true_label: int | None = None  # for offline eval

class Prediction(BaseModel):
    prediction: str
    model_version: str
    request_id: str

def pick_version() -> str:
    return random.choices(
        list(TRAFFIC_SPLIT.keys()),
        weights=list(TRAFFIC_SPLIT.values()),
    )[0]

@app.post("/predict")
def predict(features: Features):
    version = pick_version()
    model = models[version]
    
    X = [[features.sepal_length, features.sepal_width,
          features.petal_length, features.petal_width]]
    pred_idx = int(model.predict(X)[0])
    
    request_id = str(uuid.uuid4())
    
    # Log for later A/B analysis
    r.hset(f"ab:{request_id}", mapping={
        "version": version,
        "prediction": pred_idx,
        "true_label": features.true_label if features.true_label is not None else "",
        "timestamp": datetime.utcnow().isoformat(),
    })
    r.expire(f"ab:{request_id}", 86400 * 30)  # 30 days
    
    return Prediction(
        prediction=species[pred_idx],
        model_version=version,
        request_id=request_id,
    )

@app.post("/feedback")
def feedback(request_id: str, true_label: int):
    """Client reports the true outcome for offline eval."""
    r.hset(f"ab:{request_id}", "true_label", true_label)
    return {"status": "recorded"}

@app.get("/ab/results")
def ab_results():
    """Compute A/B test results so far."""
    results = {"v1": {"correct": 0, "total": 0}, "v2": {"correct": 0, "total": 0}}
    for key in r.scan_iter("ab:*"):
        data = r.hgetall(key)
        if not data.get("true_label"):
            continue
        version = data["version"]
        correct = int(data["prediction"]) == int(data["true_label"])
        results[version]["total"] += 1
        if correct:
            results[version]["correct"] += 1
    
    for v in results.values():
        v["accuracy"] = v["correct"] / v["total"] if v["total"] > 0 else 0
    
    return results

@app.post("/ab/promote/{version}")
def promote(version: str):
    """Promote a version to 100% traffic."""
    if version not in models:
        raise HTTPException(404, "Unknown version")
    global TRAFFIC_SPLIT
    TRAFFIC_SPLIT = {v: (1.0 if v == version else 0.0) for v in models}
    return {"status": "promoted", "split": TRAFFIC_SPLIT}
```

## Step 4: Generate Traffic + Compute A/B Results

```python
# generate_ab_traffic.py
import requests
import random
from sklearn.datasets import load_iris

data = load_iris(as_frame=True)

for _ in range(1000):
    idx = random.randint(0, len(data.data) - 1)
    row = data.data.iloc[idx]
    true_label = int(data.target.iloc[idx])
    
    r = requests.post("http://localhost:8000/predict", json={
        "sepal_length": float(row["sepal length (cm)"]),
        "sepal_width": float(row["sepal width (cm)"]),
        "petal_length": float(row["petal length (cm)"]),
        "petal_width": float(row["petal width (cm)"]),
        "true_label": true_label,
    })
    pred = r.json()
    print(f"v={pred['model_version']} predicted={pred['prediction']} true={species[true_label]}")

# Check results
print(requests.get("http://localhost:8000/ab/results").json())
```

## Step 5: Promote the Winner

```bash
# After analyzing results, promote v2
curl -X POST http://localhost:8000/ab/promote/v2
```

## Extension Ideas
- Add statistical significance testing
- Use multi-armed bandit instead of fixed split
- Add per-user sticky routing (so a user always sees the same version)
- Visualize results in Grafana

## What You Built
A real A/B testing system for ML models. **This is how production ML decisions get made.**

---

# Project 9 — End-to-End MLOps with Auto-Retraining (Advanced)

## Goal
Wire everything together: data → train → validate → register → deploy → monitor → drift-detect → retrain loop.

## Skills You'll Master
- Full ML lifecycle automation
- Drift-triggered retraining
- Champion-challenger promotion
- Slack alerting
- Audit logging

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     SCHEDULED / TRIGGERED                   │
└─────────────────────────┬───────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  1. Data validation (Great Expectations)                   │
└─────────────────────────┬───────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  2. DVC pipeline (prepare → train → evaluate)              │
└─────────────────────────┬───────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  3. Register to MLflow (Staging)                           │
└─────────────────────────┬───────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  4. Compare to Production (champion-challenger)            │
└─────────────────────────┬───────────────────────────────────┘
                better? │              worse?
                        ▼                        ▼
┌──────────────────────────────┐    ┌──────────────────────┐
│  5. Deploy to canary (10%)   │    │  Skip & notify Slack │
└─────────────────┬────────────┘    └──────────────────────┘
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  6. Monitor canary for 1 hour (errors, latency, accuracy)  │
└─────────────────────────┬───────────────────────────────────┘
              SLO OK?     │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  7. Promote to Production (100%)                           │
└─────────────────────────┬───────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  8. Continuous monitoring (Evidently + Prometheus)         │
└─────────────────────────┬───────────────────────────────────┘
              drift?       │
                          ▼
                  ┌───────┴────────┐
                  │  Go to step 1  │
                  └────────────────┘
```

## Step 1: Components

You'll need:
- FastAPI serving (from Project 1+3)
- MLflow server
- PostgreSQL (for predictions + MLflow backend)
- Redis (for caching + rate limit)
- Prefect or Airflow (orchestrator)
- Evidently (drift detection)
- Slack (alerts)
- Kubernetes (deploy)

## Step 2: Orchestration with Prefect

```python
# pipelines/full_mlops.py
import os
import subprocess
import json
import time
import requests
from datetime import datetime
import mlflow
from prefect import flow, task, get_run_logger
from prefect.tasks import task_input_hash

SLACK_WEBHOOK = os.environ["SLACK_WEBHOOK"]
MLFLOW_URI = os.environ.get("MLFLOW_TRACKING_URI", "http://mlflow:5000")

def notify_slack(message: str, color: str = "good"):
    requests.post(SLACK_WEBHOOK, json={
        "attachments": [{
            "color": color,
            "text": message,
            "ts": str(int(time.time())),
        }]
    })

@task(retries=3, retry_delay_seconds=60)
def validate_data():
    logger = get_run_logger()
    logger.info("Validating data...")
    result = subprocess.run(
        ["pytest", "tests/test_data.py", "-v"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        notify_slack(f"❌ Data validation failed:\n```\n{result.stdout[-1000:]}\n```", "danger")
        raise RuntimeError("Data validation failed")
    logger.info("Data validation passed")
    return True

@task
def run_training_pipeline():
    logger = get_run_logger()
    logger.info("Running DVC pipeline...")
    result = subprocess.run(
        ["dvc", "repro", "-f"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        notify_slack(f"❌ Training failed:\n```\n{result.stdout[-1000:]}\n```", "danger")
        raise RuntimeError("Training failed")
    logger.info("Training completed")
    
    with open("metrics/eval.json") as f:
        metrics = json.load(f)
    logger.info(f"Metrics: {metrics}")
    return metrics

@task
def register_to_staging(metrics: dict):
    logger = get_run_logger()
    mlflow.set_tracking_uri(MLFLOW_URI)
    client = mlflow.tracking.MlflowClient()
    
    # Find latest run for this experiment
    runs = client.search_runs(
        experiment_ids=[client.get_experiment_by_name("churn-prediction").experiment_id],
        order_by=["attributes.start_time DESC"],
        max_results=1,
    )
    if not runs:
        raise RuntimeError("No MLflow run found")
    run_id = runs[0].info.run_id
    
    # Create new version
    mv = client.create_model_version(
        name="churn-prediction",
        source=f"runs:/{run_id}/model",
        run_id=run_id,
    )
    
    # Transition to Staging
    client.transition_model_version_stage(
        name="churn-prediction",
        version=mv.version,
        stage="Staging",
    )
    logger.info(f"Registered v{mv.version} to Staging. F1: {metrics['f1']:.4f}")
    return mv.version

@task
def compare_to_production(staging_version: int, new_metrics: dict):
    """Compare Staging F1 to Production F1."""
    logger = get_run_logger()
    client = mlflow.tracking.MlflowClient()
    
    try:
        prod = client.get_latest_versions("churn-prediction", stages=["Production"])[0]
        prod_run = client.get_run(prod.run_id)
        prod_f1 = prod_run.data.metrics.get("f1", 0)
    except IndexError:
        logger.info("No Production model — auto-promote")
        return True
    
    new_f1 = new_metrics["f1"]
    improvement = new_f1 - prod_f1
    
    logger.info(f"Staging F1: {new_f1:.4f}, Production F1: {prod_f1:.4f}, improvement: {improvement:+.4f}")
    
    if improvement > 0.005:  # at least 0.5% better
        notify_slack(
            f"✅ New model v{staging_version} beats Production (F1 {new_f1:.4f} vs {prod_f1:.4f}). Initiating canary deploy.",
            "good",
        )
        return True
    else:
        notify_slack(
            f"⚠️ New model v{staging_version} not better than Production (F1 {new_f1:.4f} vs {prod_f1:.4f}). Skipping deploy.",
            "warning",
        )
        return False

@task
def canary_deploy(staging_version: int):
    """Deploy Staging model to 10% of traffic in K8s."""
    logger = get_run_logger()
    logger.info("Starting canary deploy...")
    
    # In real life: kubectl apply -f canary.yaml
    # Or use Argo Rollouts / Seldon
    subprocess.run([
        "kubectl", "set", "image",
        "deployment/churn-api-canary",
        f"api=myregistry/churn-api:v{staging_version}",
        "-n", "ml-prod",
    ], check=True)
    
    # Wait for canary to be ready
    subprocess.run([
        "kubectl", "rollout", "status",
        "deployment/churn-api-canary",
        "-n", "ml-prod", "--timeout=300s",
    ], check=True)
    
    logger.info("Canary deployed. Monitoring for 1 hour...")
    return staging_version

@task
def monitor_canary(duration_seconds: int = 3600):
    """Watch canary SLOs for the duration."""
    logger = get_run_logger()
    end_time = time.time() + duration_seconds
    
    while time.time() < end_time:
        # Query Prometheus for canary error rate and latency
        try:
            error_rate = requests.get(
                "http://prometheus:9090/api/v1/query",
                params={"query": 'rate(http_requests_total{deployment="canary",status=~"5.."}[5m]) / rate(http_requests_total{deployment="canary"}[5m])'},
            ).json()["data"]["result"]
            
            if error_rate and float(error_rate[0]["value"][1]) > 0.05:
                notify_slack("🚨 Canary error rate > 5%! Rolling back.", "danger")
                subprocess.run(["kubectl", "rollout", "undo", "deployment/churn-api-canary", "-n", "ml-prod"])
                return False
            
            time.sleep(60)
        except Exception as e:
            logger.warning(f"Monitor check failed: {e}")
            time.sleep(60)
    
    logger.info("Canary healthy for 1 hour")
    return True

@task
def promote_to_production(staging_version: int):
    """Promote Staging → Production in MLflow and K8s."""
    logger = get_run_logger()
    client = mlflow.tracking.MlflowClient()
    
    client.transition_model_version_stage(
        name="churn-prediction",
        version=staging_version,
        stage="Production",
        archive_existing_versions=True,
    )
    
    subprocess.run([
        "kubectl", "set", "image",
        "deployment/churn-api",
        f"api=myregistry/churn-api:v{staging_version}",
        "-n", "ml-prod",
    ], check=True)
    
    subprocess.run([
        "kubectl", "rollout", "status",
        "deployment/churn-api",
        "-n", "ml-prod", "--timeout=600s",
    ], check=True)
    
    notify_slack(f"🚀 Promoted v{staging_version} to Production!", "good")

@flow(name="full-mlops-pipeline", log_prints=True)
def full_mlops_pipeline():
    validate_data()
    metrics = run_training_pipeline()
    staging_version = register_to_staging(metrics)
    should_deploy = compare_to_production(staging_version, metrics)
    
    if should_deploy:
        canary_deploy(staging_version)
        healthy = monitor_canary(duration_seconds=60)  # 1 min for demo; 1h in prod
        if healthy:
            promote_to_production(staging_version)

if __name__ == "__main__":
    full_mlops_pipeline()
    
    # In production: schedule with Prefect Deployments
    # from prefect.deployments import Deployment
    # Deployment(full_mlops_pipeline).serve(
    #     name="weekly-retrain",
    #     cron="0 2 * * 0",
    # )
```

## Step 3: Drift-Triggered Retraining

```python
# monitoring/drift_triggered_retrain.py
import requests
import time
import os
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset
import pandas as pd

PREFECT_API = os.environ.get("PREFECT_API_URL")
PREFECT_DEPLOYMENT_ID = os.environ.get("RETRAIN_DEPLOYMENT_ID")
PROMETHEUS = "http://prometheus:9090"

def get_recent_predictions(n=1000):
    """Fetch recent prediction inputs from feature store or DB."""
    # In real life: query feature store
    return pd.read_csv("data/current.csv")

def check_drift():
    ref = pd.read_csv("data/reference.csv")
    cur = get_recent_predictions()
    
    report = Report(metrics=[DataDriftPreset()])
    report.run(reference_data=ref, current_data=cur)
    result = report.as_dict()
    return result["metrics"][0]["result"]["dataset_drift"]

def trigger_retrain():
    requests.post(
        f"{PREFECT_API}/deployments/{PREFECT_DEPLOYMENT_ID}/execute",
        headers={"Authorization": f"Bearer {os.environ['PREFECT_API_KEY']}"},
    )

if __name__ == "__main__":
    while True:
        try:
            if check_drift():
                print("🚨 Drift detected — triggering retrain")
                trigger_retrain()
                # Sleep 6h to avoid retriggering during retrain
                time.sleep(6 * 3600)
            else:
                print("No drift")
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(3600)  # check hourly
```

## Step 4: Run It End-to-End

```bash
# Start MLflow
mlflow server --backend-store-uri sqlite:///mlflow.db --port 5000 &

# Start Prefect server
prefect server start &

# Start the API
uvicorn main:app --port 8000 &

# Start drift monitor
python monitoring/drift_triggered_retrain.py &

# Trigger pipeline manually
python pipelines/full_mlops.py

# Or schedule via Prefect
prefect deployment build pipelines/full_mlops.py:full_mlops_pipeline --name weekly-retrain --cron "0 2 * * 0"
prefect deployment apply full_mlops_pipeline-deployment.yaml
```

## Extension Ideas
- Add fairness audits to the pipeline
- Add cost tracking (GPU hours, API calls)
- Add automatic model pruning (archive models older than 90 days)
- Add lineage tracking (OpenLineage)

## What You Built
A **fully automated** ML lifecycle. This is **Level 2 MLOps** — what Google/Meta/Netflix do. You're now hirable as a Senior MLOps Engineer.

---

# Project 10 — Production AI Platform (Pro)

## Goal
Build a multi-tenant AI platform: clients sign up, get API keys, are billed per token, can deploy their own models. **This is a real business.**

## Skills You'll Master
- Multi-tenant architecture
- API key management + billing
- Per-tenant rate limiting
- Per-tenant model isolation
- Audit logging
- Compliance (GDPR, SOC2)
- High availability
- Cost optimization

## Architecture

```
                    ┌─────────────────────┐
                    │   Cloudflare / WAF  │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  Kubernetes Ingress │
                    │  (nginx + cert-mgr) │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
      ┌───────▼─────┐  ┌───────▼─────┐  ┌───────▼─────┐
      │ Auth Service│  │ Billing Svc │  │  API Gateway│
      │  (FastAPI)  │  │ (FastAPI)   │  │  (FastAPI)  │
      └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
             │                │                │
             └────────────────┼────────────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
      ┌───────▼─────┐ ┌───────▼─────┐ ┌───────▼─────┐
      │ PostgreSQL  │ │   Redis     │ │  S3 / MinIO │
      │ (tenants,   │ │ (cache,     │ │ (model      │
      │  usage)     │ │  rate limit)│ │  artifacts) │
      └─────────────┘ └─────────────┘ └─────────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
      ┌───────▼─────┐ ┌───────▼─────┐ ┌───────▼─────┐
      │ Model Pool  │ │ Model Pool  │ │ Model Pool  │
      │ (GPU node 1)│ │ (GPU node 2)│ │ (CPU nodes) │
      └─────────────┘ └─────────────┘ └─────────────┘
```

## Step 1: Tenant Management Service

```python
# services/tenant_service/main.py
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import asyncpg
import uuid
import hashlib
import secrets
from datetime import datetime

app = FastAPI()

async def get_db():
    conn = await asyncpg.connect("postgresql://postgres:postgres@db:5432/platform")
    try:
        yield conn
    finally:
        await conn.close()

class TenantCreate(BaseModel):
    name: str
    email: str
    plan: str = "free"  # free / pro / enterprise

class APIKeyOut(BaseModel):
    key: str
    tenant_id: str
    created_at: datetime

@app.post("/tenants", response_model=APIKeyOut)
async def create_tenant(t: TenantCreate, db = Depends(get_db)):
    tenant_id = str(uuid.uuid4())
    
    # Insert tenant
    await db.execute(
        "INSERT INTO tenants (id, name, email, plan) VALUES ($1, $2, $3, $4)",
        tenant_id, t.name, t.email, t.plan,
    )
    
    # Generate API key
    raw_key = f"sk-{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    
    await db.execute(
        "INSERT INTO api_keys (key_hash, tenant_id, name) VALUES ($1, $2, $3)",
        key_hash, tenant_id, "default",
    )
    
    return APIKeyOut(key=raw_key, tenant_id=tenant_id, created_at=datetime.utcnow())

@app.get("/tenants/{tenant_id}")
async def get_tenant(tenant_id: str, db = Depends(get_db)):
    row = await db.fetchrow("SELECT * FROM tenants WHERE id = $1", tenant_id)
    if not row:
        raise HTTPException(404, "Tenant not found")
    
    usage = await db.fetchrow(
        "SELECT COUNT(*), COALESCE(SUM(tokens), 0) FROM usage_log WHERE tenant_id = $1",
        tenant_id,
    )
    return {
        "id": row["id"],
        "name": row["name"],
        "plan": row["plan"],
        "requests_total": usage["count"],
        "tokens_total": usage["sum"],
    }
```

## Step 2: API Gateway (Auth + Billing + Rate Limit)

```python
# services/gateway/main.py
import os
import time
import hashlib
import asyncio
import httpx
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import StreamingResponse
import redis.asyncio as redis
import asyncpg
from pydantic import BaseModel

redis_client = redis.from_url("redis://redis:6379", decode_responses=True)

RATE_LIMITS = {"free": 60, "pro": 1000, "enterprise": 10000}  # per minute
TOKEN_LIMITS = {"free": 10_000, "pro": 1_000_000, "enterprise": 100_000_000}  # per month

app = FastAPI()

async def get_db():
    conn = await asyncpg.connect("postgresql://postgres:postgres@db:5432/platform")
    try:
        yield conn
    finally:
        await conn.close()

async def authenticate(request: Request, db = Depends(get_db)):
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(401, "Missing bearer token")
    key = auth[7:]
    key_hash = hashlib.sha256(key.encode()).hexdigest()
    
    # Lookup
    row = await db.fetchrow(
        """
        SELECT ak.tenant_id, t.plan 
        FROM api_keys ak 
        JOIN tenants t ON ak.tenant_id = t.id 
        WHERE ak.key_hash = $1 AND ak.active = true
        """,
        key_hash,
    )
    if not row:
        raise HTTPException(401, "Invalid API key")
    
    return {"tenant_id": row["tenant_id"], "plan": row["plan"]}

async def rate_limit(client: dict):
    """Per-tenant rate limit."""
    key = f"rl:{client['tenant_id']}:{int(time.time() // 60)}"
    count = await redis_client.incr(key)
    if count == 1:
        await redis_client.expire(key, 60)
    
    limit = RATE_LIMITS[client["plan"]]
    if count > limit:
        raise HTTPException(
            429,
            f"Rate limit exceeded ({limit}/min for {client['plan']} plan)",
            headers={"Retry-After": "60"},
        )

async def check_token_budget(client: dict, tokens: int, db):
    """Check monthly token budget."""
    month = time.strftime("%Y-%m")
    key = f"tokens:{client['tenant_id']}:{month}"
    used = int(await redis_client.get(key) or 0)
    limit = TOKEN_LIMITS[client["plan"]]
    if used + tokens > limit:
        raise HTTPException(
            402,  # Payment Required
            f"Token budget exceeded ({used}/{limit} this month). Upgrade plan.",
        )

async def record_usage(client: dict, tokens: int, db):
    """Log usage for billing."""
    month = time.strftime("%Y-%m")
    await redis_client.incrby(f"tokens:{client['tenant_id']}:{month}", tokens)
    
    await db.execute(
        "INSERT INTO usage_log (tenant_id, tokens, timestamp) VALUES ($1, $2, NOW())",
        client["tenant_id"], tokens,
    )

class ChatRequest(BaseModel):
    model: str
    messages: list[dict]
    max_tokens: int = 100
    stream: bool = False

@app.post("/v1/chat/completions")
async def chat(req: ChatRequest, request: Request, client = Depends(authenticate), db = Depends(get_db)):
    await rate_limit(client)
    
    # Estimate tokens
    est_input_tokens = sum(len(m.get("content", "").split()) for m in req.messages) * 2
    est_total = est_input_tokens + req.max_tokens
    await check_token_budget(client, est_total, db)
    
    # Forward to backend model service
    async with httpx.AsyncClient(timeout=120) as http:
        backend_resp = await http.post(
            "http://model-service:8000/v1/chat/completions",
            json=req.dict(),
            headers={"X-Tenant-ID": client["tenant_id"]},
        )
    
    # Record actual usage
    actual_tokens = backend_resp.json().get("usage", {}).get("total_tokens", est_total)
    await record_usage(client, actual_tokens, db)
    
    return backend_resp.json()

@app.get("/v1/usage")
async def get_usage(client = Depends(authenticate), db = Depends(get_db)):
    month = time.strftime("%Y-%m")
    used = int(await redis_client.get(f"tokens:{client['tenant_id']}:{month}") or 0)
    return {
        "tenant_id": client["tenant_id"],
        "plan": client["plan"],
        "month": month,
        "tokens_used": used,
        "tokens_limit": TOKEN_LIMITS[client["plan"]],
    }
```

## Step 3: Billing Service

```python
# services/billing/main.py
import os
import stripe
from fastapi import FastAPI, HTTPException, Depends
import asyncpg
from pydantic import BaseModel

stripe.api_key = os.environ["STRIPE_API_KEY"]

PRICES = {
    "free": None,
    "pro": "price_xxx_pro",
    "enterprise": "price_xxx_ent",
}

app = FastAPI()

class UpgradeRequest(BaseModel):
    tenant_id: str
    new_plan: str
    payment_method_id: str

@app.post("/upgrade")
async def upgrade(req: UpgradeRequest):
    if req.new_plan not in PRICES or not PRICES[req.new_plan]:
        raise HTTPException(400, "Invalid plan")
    
    # Create Stripe customer + subscription
    customer = stripe.Customer.create(
        payment_method=req.payment_method_id,
        invoice_settings={"default_payment_method": req.payment_method_id},
    )
    
    subscription = stripe.Subscription.create(
        customer=customer.id,
        items=[{"price": PRICES[req.new_plan]}],
        expand=["latest_invoice.payment_intent"],
    )
    
    # Update tenant plan in DB
    async with asyncpg.connect("postgresql://postgres:postgres@db:5432/platform") as db:
        await db.execute(
            "UPDATE tenants SET plan = $1, stripe_customer_id = $2 WHERE id = $3",
            req.new_plan, customer.id, req.tenant_id,
        )
    
    return {"status": "upgraded", "subscription_id": subscription.id}

@app.post("/webhook")
async def stripe_webhook(request):
    # Handle Stripe webhooks (payment_failed, subscription_deleted, etc.)
    ...
```

## Step 4: Database Schema

```sql
-- migrations/001_initial.sql
CREATE TABLE tenants (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    plan TEXT NOT NULL DEFAULT 'free',
    stripe_customer_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key_hash TEXT NOT NULL UNIQUE,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    name TEXT NOT NULL DEFAULT 'default',
    active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_used_at TIMESTAMPTZ
);

CREATE TABLE usage_log (
    id BIGSERIAL PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    tokens INTEGER NOT NULL,
    endpoint TEXT,
    model TEXT,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_usage_log_tenant_month ON usage_log (tenant_id, date_trunc('month', timestamp));

CREATE TABLE audit_log (
    id BIGSERIAL PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    action TEXT NOT NULL,
    details JSONB,
    ip_address INET,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

## Step 5: K8s Deployment

```yaml
# k8s/gateway-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-gateway
spec:
  replicas: 5
  selector:
    matchLabels:
      app: api-gateway
  template:
    metadata:
      labels:
        app: api-gateway
    spec:
      containers:
      - name: gateway
        image: myregistry/api-gateway:v1
        env:
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: gateway-secrets
              key: redis-url
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: gateway-secrets
              key: database-url
        resources:
          requests: {cpu: 500m, memory: 512Mi}
          limits: {cpu: 1000m, memory: 1Gi}
        livenessProbe:
          httpGet: {path: /health, port: 8000}
        readinessProbe:
          httpGet: {path: /health/ready, port: 8000}
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-gateway
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-gateway
  minReplicas: 5
  maxReplicas: 50
  metrics:
  - type: Resource
    resource:
      name: cpu
      target: {type: Utilization, averageUtilization: 70}
```

## Step 6: Observability + Audit

```python
# Add to gateway: audit logging middleware
@app.middleware("http")
async def audit_log(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    
    # Log to audit table
    if request.url.path.startswith("/v1/"):
        tenant_id = getattr(request.state, "tenant_id", None)
        if tenant_id:
            asyncio.create_task(log_audit(
                tenant_id=tenant_id,
                action=request.url.path,
                details={
                    "method": request.method,
                    "status": response.status_code,
                    "duration_ms": duration * 1000,
                },
                ip=request.client.host,
            ))
    
    return response

async def log_audit(tenant_id, action, details, ip):
    async with asyncpg.connect("postgresql://postgres:postgres@db:5432/platform") as db:
        await db.execute(
            "INSERT INTO audit_log (tenant_id, action, details, ip_address) VALUES ($1, $2, $3, $4)",
            tenant_id, action, json.dumps(details), ip,
        )
```

## Step 7: Multi-Region (Optional)

For true production:
- Deploy in us-east-1, eu-west-1, ap-southeast-1
- Use Route53 latency-based routing
- Sync tenants via PostgreSQL logical replication
- Sync models via S3 cross-region replication

## What You Built

A real multi-tenant AI platform. **This is the kind of system you'd build at OpenAI, Anthropic, or your own AI startup.**

## Final Checklist — Are You Hireable?

If you can build **all 10 projects**, you can:
- [ ] Build a FastAPI service from scratch
- [ ] Containerize and deploy to Kubernetes
- [ ] Set up CI/CD with GitHub Actions
- [ ] Track experiments with MLflow
- [ ] Version data with DVC
- [ ] Detect drift with Evidently
- [ ] Build an OpenAI-compatible LLM API
- [ ] Run A/B tests for models
- [ ] Automate the full ML lifecycle
- [ ] Build a multi-tenant platform

**You are now ready to apply for these roles:**
- ML Engineer
- MLOps Engineer
- AI Engineer
- Platform Engineer (ML)
- Backend Engineer (AI products)
- Data Engineer (ML focus)

**Expected salary range (2024-2025, US):** $120k - $250k depending on location and company.

---

## Final Words

You now have the **complete system** to go from zero to hirable. But knowledge is just potential. **Execution is what pays.**

Don't read this and close the tab. Pick Project 1 today. Build it. Tomorrow, Project 2. The week after, Project 4. In 3 months of consistent work, you'll be unrecognizable.

Then:
1. Put all 10 projects on GitHub
2. Write a Medium/Dev.to post on each
3. Add them to your resume
4. Apply to 50 roles
5. Pass technical interviews with confidence
6. Get the offer
7. Get paid

**Go build.**

---

**End of File 5. Continue to 00_README_Roadmap.md.**
