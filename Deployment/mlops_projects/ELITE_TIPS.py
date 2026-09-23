# ============================================================
# MLOPS MASTERY: 10 Projects from Zero to Production
# ============================================================
# Every file is heavily commented. Every concept explained.
# Read the projects in ORDER — each one builds on the last.
# ============================================================

"""
ELITE TIPS & TRICKS — Things 99% of ML Engineers Don't Know

Read this file carefully. These are the hard-won lessons that
separate junior ML engineers from senior MLOps engineers.
"""

# =============================================================================
# TIP 1: The Training-Serving Skew is the #1 silent killer
# =============================================================================
TRAINING_SERVING_SKEW = """
Problem: Your model uses `df['age'].fillna(df['age'].mean())` at training time.
At serving time, someone computes the mean differently → different imputation →
model sees different input → predictions silently degrade.

Solution: ALWAYS use the SAME code for feature engineering at train AND serve time.
This is exactly why Feature Stores (Project 4) exist.

Checklist:
  ✓ Feature engineering code lives in ONE place (feature store)
  ✓ The same function is called at training time and serving time
  ✓ Preprocessing parameters (mean, std, categories) are SAVED from training
    and LOADED at serving time — NEVER recomputed on live data
"""

# =============================================================================
# TIP 2: Log MORE than you think you need
# =============================================================================
LOGGING_ADVICE = """
Log these for every prediction in production:
  - timestamp
  - model version
  - input features (or feature hash if PII-sensitive)
  - raw model output (all probabilities, not just the top class)
  - prediction latency
  - request ID (for tracing)
  - user/entity ID

Why? You'll need this when:
  - A user complains about a bad recommendation → trace their prediction
  - Model starts degrading → compare feature distributions over time
  - You need to retrain → use logged inputs as new training data
  - A/B test analysis → compare outcomes per model variant

Cost: Storing this is CHEAP. Not having it when you need it is EXPENSIVE.
"""

# =============================================================================
# TIP 3: Never blindly deploy a new model
# =============================================================================
CHAMPION_CHALLENGER = """
Always do Champion/Challenger comparison before deploying:

WRONG approach:
  - New model has higher test ROC-AUC → deploy it → hope for the best

RIGHT approach:
  1. Keep current production model (Champion) running
  2. Run Champion/Challenger comparison on SAME test set
  3. Use bootstrap confidence intervals (not just point estimates)
  4. Require minimum improvement threshold (e.g. +0.5% ROC-AUC)
  5. Only deploy if Challenger is better with statistical confidence

Why? Test set metrics can be misleading:
  - Test set might not reflect current production distribution
  - Variance in small test sets causes spurious "improvements"
  - Bootstrap CI reveals when the improvement is just noise
"""

# =============================================================================
# TIP 4: The 4 types of drift (most people only know 1)
# =============================================================================
DRIFT_TYPES = """
1. DATA DRIFT (most common):
   Input feature distributions change.
   Example: Users in Jan buy different products than users in July.
   Detection: KS test, PSI on feature distributions.

2. CONCEPT DRIFT:
   The relationship between X and y changes.
   Example: "large transaction" used to mean fraud; now it's just Venmo.
   Detection: Monitor model accuracy on labeled data over time. CUSUM test.

3. LABEL DRIFT:
   The target distribution changes.
   Example: Fraud rate jumps from 1% to 5%.
   Detection: Monitor prediction class distribution. Compare to historical.

4. UPSTREAM DATA DRIFT:
   A data pipeline upstream changes how it computes a field.
   Example: The ETL job that computes `days_active` changes its definition.
   Detection: Monitor feature value ranges and statistics. Validate schema.

Most teams only detect #1. #2 is the deadliest. #4 is the most sneaky.
"""

# =============================================================================
# TIP 5: Separate metrics → Don't use test accuracy for deployment decisions
# =============================================================================
METRICS_SEPARATION = """
Use DIFFERENT data for different purposes:

  TRAINING SET:    Train the model (touch it constantly)
  VALIDATION SET:  Tune hyperparameters and early stopping (touch it often)
  TEST SET:        Final model evaluation ONLY (touch it ONCE)
  HOLDOUT SET:     Champion/Challenger comparison (never used in training)
  SHADOW SET:      Evaluate in production with real distribution

Common mistake: using the validation set for Champion/Challenger comparison.
If you tuned hyperparameters on the validation set, it's already "seen" by
the model's training process → overly optimistic metrics.

Always keep a truly holdout set for final comparisons.
"""

# =============================================================================
# TIP 6: Async everything in your serving layer
# =============================================================================
ASYNC_SERVING = """
Sequential serving (WRONG for high traffic):
  request 1 → predict → wait → return (3ms)
  request 2 → predict → wait → return (3ms)  ← blocked by request 1
  Total for 1000 requests: 3000ms

Async serving (RIGHT):
  request 1, 2, 3, ... N all handled concurrently
  Total for 1000 requests: ~3ms + overhead

FastAPI + asyncio handles this automatically IF your prediction code is non-blocking.
For CPU-bound predictions: use multiple uvicorn workers (--workers 4).
For GPU: use batching to maximize GPU utilization.
"""

# =============================================================================
# TIP 7: The MLOps Maturity Model
# =============================================================================
MATURITY_MODEL = """
Level 0 — Manual:
  - Model in a Jupyter notebook
  - Deployed by copy-pasting code to a server
  - No monitoring, no version control for models
  - Most companies start here

Level 1 — ML Pipelines:
  - Automated training pipeline
  - Model versioning (MLflow)
  - Basic monitoring (error rates)
  - Manual deployment trigger

Level 2 — Automated CI/CD:
  - Every commit triggers training
  - Automated quality gates
  - Staging + production environments
  - Champion/Challenger deployment
  - Alert on degradation

Level 3 — Full Automation:
  - Drift detection triggers automatic retraining
  - Champion/Challenger deployed automatically
  - A/B testing framework
  - Feature store
  - Full audit log

Level 4 — Self-optimizing:
  - Models retrain themselves based on drift signals
  - Bandit algorithms automatically route traffic to best model
  - Continuous learning from production feedback
  - This is where Google, Facebook, Netflix operate

Goal for most companies: Level 2 or 3.
"""

# =============================================================================
# TIP 8: Reproducibility requirements
# =============================================================================
REPRODUCIBILITY = """
A model run is reproducible if you can recreate the EXACT same model given:
  1. The code (Git commit hash)
  2. The data (DVC commit hash / data fingerprint)
  3. The config (params.yaml stored in MLflow)
  4. The environment (requirements.txt pinned versions / Docker image)
  5. The random seeds (logged to MLflow as params)

Test: Can a new teammate checkout your repo and recreate the production model?
If not → you don't have reproducibility.

Always log: git_commit_hash, data_hash, python_version, all random seeds.
"""

# =============================================================================
# TIP 9: Don't over-engineer early
# =============================================================================
PRAGMATISM = """
Week 1-4 of a new ML project:
  ✓ Jupyter notebooks + MLflow for experiment tracking
  ✓ Git for code versioning
  ✗ Skip: Kafka, feature store, k8s, Airflow

Month 2-3 (first production model):
  ✓ FastAPI serving + Docker
  ✓ Basic monitoring (log predictions, check error rate)
  ✓ CI/CD with GitHub Actions
  ✗ Skip: multi-armed bandit, full feature store

Month 4+ (at scale, multiple models):
  ✓ Feature store (if multiple teams using same features)
  ✓ Full monitoring + drift detection
  ✓ A/B testing framework
  ✓ Automated retraining

The mistake: building a Kafka + Kubernetes + feature store + Airflow
platform before you have a single model in production.
Build what you need. Add MLOps infrastructure as pain points emerge.
"""

# =============================================================================
# TIP 10: Interview topics for MLOps roles
# =============================================================================
INTERVIEW_PREP = """
Questions you will definitely be asked:

1. "How do you detect and handle data drift?"
   Answer: KS test + PSI on features, CUSUM on model performance.
   Thresholds: PSI > 0.2 = retrain. CUSUM alarm = investigate concept drift.

2. "How do you do a zero-downtime model deployment?"
   Answer: Blue-green deployment. Run new model in parallel, shift traffic
   gradually (canary), roll back if metrics degrade.

3. "What's the training-serving skew and how do you prevent it?"
   Answer: When features are computed differently at training vs serving.
   Prevention: Feature store. One function for both contexts.

4. "How do you decide when to retrain a model?"
   Answer: Trigger-based: drift alerts, performance degradation.
   Schedule-based: weekly/monthly depending on data velocity.
   Always use Champion/Challenger before deploying new model.

5. "What would you monitor for a deployed model?"
   Answer: Input feature distributions (drift), output score distribution,
   prediction latency P50/P95/P99, business metrics (conversion, revenue),
   ground truth accuracy as labels come in.

6. "How do you handle class imbalance in production?"
   Answer: Track class distribution shift over time. If fraud rate changes
   from 1% → 5%, the model threshold needs adjustment. This is label drift.
"""


if __name__ == "__main__":
    print("="*60)
    print("MLOPS MASTERY: ELITE TIPS & TRICKS")
    print("="*60)
    tips = {
        "Training-Serving Skew": TRAINING_SERVING_SKEW,
        "Logging Strategy":      LOGGING_ADVICE,
        "Champion/Challenger":   CHAMPION_CHALLENGER,
        "Types of Drift":        DRIFT_TYPES,
        "Metrics Separation":    METRICS_SEPARATION,
        "Async Serving":         ASYNC_SERVING,
        "Maturity Model":        MATURITY_MODEL,
        "Reproducibility":       REPRODUCIBILITY,
        "Pragmatism":            PRAGMATISM,
        "Interview Prep":        INTERVIEW_PREP,
    }
    for title, content in tips.items():
        print(f"\n{'─'*60}")
        print(f"  {title}")
        print(f"{'─'*60}")
        print(content)
