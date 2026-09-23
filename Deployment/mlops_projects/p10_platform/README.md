# MLOps Mastery: 10 Projects — Zero to Production

> Every line commented. Every concept explained. 10 real projects that teach you everything.

---

## The 10 Projects

| # | Project | Key Tool | Core Skill | Difficulty |
|---|---------|----------|------------|------------|
| 01 | Experiment Tracking | MLflow | Log params, metrics, models | Beginner |
| 02 | Data Versioning | DVC | Version datasets like code | Beginner |
| 03 | Model Registry | MLflow Registry | Lifecycle: None→Staging→Prod | Beginner |
| 04 | Feature Store | Custom + Feast | Offline/online stores, no skew | Intermediate |
| 05 | CI/CD Pipeline | GitHub Actions | Automate train→test→deploy | Intermediate |
| 06 | Model Serving | FastAPI | Production API with caching | Intermediate |
| 07 | Drift Monitoring | Evidently/Scipy | KS test, PSI, CUSUM | Intermediate |
| 08 | Auto Retraining | Optuna | HPO + Champion/Challenger | Advanced |
| 09 | A/B Testing | Scipy/Custom | Shadow, Bandit, Canary | Advanced |
| 10 | Full Platform | All of the above | Event-driven MLOps system | Advanced |

---

## Study Order

```
Week 1:  Projects 1, 2, 3  — Core concepts, tooling
Week 2:  Projects 4, 5     — Data + CI/CD fundamentals
Week 3:  Projects 6, 7     — Serving + Monitoring
Week 4:  Projects 8, 9, 10 — Advanced automation
Week 5+: Rebuild from scratch using a real dataset you care about
```

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run any project
cd p01_experiments && python train.py && mlflow ui
cd p02_data_versioning && python dvc_workflow.py
cd p03_model_registry && python model_registry.py
cd p04_feature_store && python feature_store.py
cd p05_cicd && python pipeline.py
cd p05_cicd && pytest test_model.py -v
cd p06_serving && uvicorn serve:app --reload
cd p07_monitoring && python monitor.py
cd p08_retraining && python automated_retrain.py
cd p09_ab_testing && python ab_testing.py
cd p10_platform && python platform.py

# Read the elite tips
python ELITE_TIPS.py
```

## What Each File Teaches

### p01_experiments/train.py
- MLflow experiment setup, `start_run()` context manager
- Logging params, metrics, tags, artifacts, and the model itself
- Auto-logging with `mlflow.sklearn.autolog()`
- Loading models back from run IDs

### p02_data_versioning/dvc_workflow.py
- How DVC .dvc pointer files work internally (MD5 hashing)
- `dvc.yaml` pipeline definition (DAG of stages)
- `params.yaml` for tracked hyperparameters
- Remote storage setup (S3/GCS/Azure)
- Data validation as a pipeline stage

### p03_model_registry/model_registry.py
- Model versions and stages (None/Staging/Production/Archived)
- Programmatic stage transitions with `MlflowClient`
- Automated quality gates before promotion
- Loading model by stage (not by version number!)
- Rollback to previous version

### p04_feature_store/feature_store.py
- FeatureDefinition and FeatureView data structures
- Offline store (Parquet) vs Online store (SQLite/Redis)
- **Point-in-time correct feature retrieval** (no leakage!)
- Materializing features to both stores
- Why training-serving skew happens and how to prevent it

### p05_cicd/pipeline.py + test_model.py + github_actions.yaml
- 4-stage pipeline: data → train → evaluate → package
- Quality gates with `assert` and `sys.exit(1)` on failure
- 4 test categories: data, behavior, performance, integration
- Complete GitHub Actions workflow with 7 jobs
- Docker build, staging deploy, production with manual approval

### p06_serving/serve.py
- FastAPI with `lifespan` for model loading at startup
- Pydantic validation with custom validators
- Prediction caching with deterministic cache keys
- Batch prediction endpoint with `asyncio.gather()`
- Background tasks for async prediction logging
- Middleware for request/response logging
- Dockerfile with health checks and non-root user

### p07_monitoring/monitor.py
- KS test: non-parametric distribution comparison
- PSI: industry standard, 3-level severity
- Jensen-Shannon Divergence: symmetric, bounded
- CUSUM: detects gradual concept drift over time
- Full monitoring report with alerting
- Visual drift dashboard with matplotlib

### p08_retraining/automated_retrain.py
- Trigger logic: drift, performance drop, schedule
- Optuna HPO with TPE sampler + MedianPruner
- Cross-validation objective function
- Bootstrap confidence intervals for Champion/Challenger
- Full retraining loop logged to MLflow
- Airflow DAG for scheduled execution

### p09_ab_testing/ab_testing.py
- Consistent hashing for sticky user assignment
- Shadow deployment: silent challenger, zero risk
- Statistical tests: chi-squared (binary), t-test, Mann-Whitney U
- Power analysis: sample size BEFORE running experiment
- Epsilon-greedy multi-armed bandit
- Canary deployment with gradual traffic ramp

### p10_platform/platform.py
- EventBus with pub/sub architecture
- All 9 projects integrated into one system
- Production readiness checklist (47 items)
- Real-world stack comparison (AWS/GCP/Azure vs open source)

### ELITE_TIPS.py
- Training-serving skew (the #1 silent killer)
- What to log for every prediction
- Champion/Challenger best practices
- 4 types of drift
- Metrics separation (train/val/test/holdout/shadow)
- MLOps maturity model (0→4)
- Reproducibility requirements
- Interview prep for MLOps roles

---

## The Mental Model

```
Raw Data
    ↓ (DVC + Data Validation)
Feature Store ← Engineer features once, use everywhere
    ↓ (Offline store for training)
Training Pipeline
    ↓ (MLflow tracks everything)
Model Registry
    ↓ (Quality gates + Champion/Challenger)
Staging Environment
    ↓ (Automated tests pass)
Production (via Canary or Blue-Green)
    ↓ (Prediction logging)
Monitoring (Drift detection)
    ↓ (Drift threshold breached)
Automated Retraining ← back to Training Pipeline
```

This loop, running continuously and automatically, is **production MLOps**.
